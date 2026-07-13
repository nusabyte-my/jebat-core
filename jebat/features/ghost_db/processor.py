"""Ghost DB — File Processor for Ingestion."""

from __future__ import annotations

import hashlib
import mimetypes
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .client import GhostClient, VectorDimensionMismatch
from .chunkers import BaseChunker, get_chunker
from .embeddings import EmbeddingProvider
from .models import Document, IngestOptions


@dataclass
class IngestedFile:
    """Result of processing a single file."""
    path: str
    chunks_created: int = 0
    vectors_indexed: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None


@dataclass
class IngestResult:
    """Result of batch ingestion."""
    files: list[IngestedFile]
    total_chunks: int = 0
    total_vectors: int = 0
    total_latency_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


class FileProcessor:
    """Process individual files into vector documents."""

    SUPPORTED_EXTENSIONS = {
        # Code
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".h",
        ".cs", ".php", ".rb", ".swift", ".kt", ".scala", ".clj", ".hs", ".ml",
        # Web
        ".html", ".css", ".scss", ".less", ".vue", ".svelte",
        # Config
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        # Docs
        ".md", ".markdown", ".rst", ".txt", ".adoc",
        # Data
        ".csv", ".tsv",
        # Shell
        ".sh", ".bash", ".zsh", ".fish",
        # Docker
        ".dockerfile", "Dockerfile",
        # Other
        ".sql", ".graphql", ".proto", ".thrift",
    }

    def __init__(
        self,
        client: GhostClient,
        chunker: BaseChunker,
        embed_provider: EmbeddingProvider,
        collection: str,
    ):
        self.client = client
        self.chunker = chunker
        self.embed_provider = embed_provider
        self.collection = collection

    def _get_file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def _is_supported(self, path: Path) -> bool:
        """Check if file extension is supported."""
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _read_file(self, path: Path) -> tuple[str, dict[str, Any]]:
        """Read file content with appropriate encoding."""
        mime_type, _ = mimetypes.guess_type(str(path))

        # Try UTF-8 first
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return content, {"encoding": "utf-8"}
        except UnicodeDecodeError:
            pass

        # Try latin-1 (never fails)
        with open(path, "r", encoding="latin-1") as f:
            content = f.read()
        return content, {"encoding": "latin-1"}

    def _extract_metadata(self, path: Path, base_metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Extract metadata from file."""
        stat = path.stat()
        file_hash = self._get_file_hash(path)
        mime_type, _ = mimetypes.guess_type(str(path))

        metadata = {
            "source": str(path),
            "file_name": path.name,
            "file_ext": path.suffix.lower(),
            "file_size": stat.st_size,
            "file_hash": file_hash,
            "mime_type": mime_type or "text/plain",
            "modified_at": stat.st_mtime,
            "created_at": stat.st_ctime,
        }

        if base_metadata:
            metadata.update(base_metadata)

        return metadata

    def process_file(
        self,
        path: Path,
        base_metadata: Optional[dict[str, Any]] = None,
    ) -> IngestedFile:
        """Process a single file into vector documents."""
        start = time.time()
        result = IngestedFile(path=str(path))

        try:
            # Validate
            if not path.is_file():
                raise ValueError(f"Not a file: {path}")

            if not self._is_supported(path):
                result.error = f"Unsupported extension: {path.suffix}"
                result.latency_ms = (time.time() - start) * 1000
                return result

            # Read file
            content, read_meta = self._read_file(path)
            if not content.strip():
                result.error = "Empty file"
                result.latency_ms = (time.time() - start) * 1000
                return result

            # Extract metadata
            metadata = self._extract_metadata(path, base_metadata)
            metadata.update(read_meta)

            # Chunk
            chunks = self.chunker.chunk(content, metadata)
            if not chunks:
                result.error = "No chunks generated"
                result.latency_ms = (time.time() - start) * 1000
                return result

            # Embed chunks
            chunk_texts = [c.text for c in chunks]
            embed_result = self.embed_provider.embed(chunk_texts)

            # Create documents
            documents = []
            for i, chunk in enumerate(chunks):
                if i >= len(embed_result.vectors):
                    break
                documents.append(Document(
                    collection=self.collection,
                    vector=embed_result.vectors[i].tolist(),
                    text=chunk.text,
                    metadata=chunk.metadata,
                ))

            # Insert batch
            self.client.insert_batch(self.collection, documents)

            result.chunks_created = len(chunks)
            result.vectors_indexed = len(documents)
            result.file_hash = metadata["file_hash"]
            result.mime_type = metadata.get("mime_type")

        except Exception as e:
            result.error = str(e)

        result.latency_ms = (time.time() - start) * 1000
        return result