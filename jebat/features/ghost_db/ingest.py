"""Ghost DB — Ingestion Pipeline (chunk + embed + index)."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .client import GhostClient, GhostConfig
from .models import Document
from .chunkers import BaseChunker, get_chunker
from .embeddings import EmbeddingProvider, get_embedding_provider
from .processor import FileProcessor, IngestedFile, IngestResult


@dataclass
class IngestResult:
    """Result of batch ingestion."""
    files: list[IngestedFile]
    total_chunks: int = 0
    total_vectors: int = 0
    total_latency_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for f in self.files if f.error is None)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class IngestionPipeline:
    """High-level ingestion pipeline for directories and files."""

    def __init__(
        self,
        client: GhostClient,
        collection: str,
        chunker: Optional[BaseChunker] = None,
        embed_provider: Optional[EmbeddingProvider] = None,
        config: Optional[GhostConfig] = None,
    ):
        self.client = client
        self.collection = collection
        self.config = config or GhostConfig()

        # Initialize chunker
        self.chunker = chunker or get_chunker(
            strategy=self.config.ingestion.chunker,
            chunk_size=self.config.ingestion.chunk_size,
            chunk_overlap=self.config.ingestion.chunk_overlap,
        )

        # Initialize embedding provider
        self.embed_provider = embed_provider or get_embedding_provider(
            provider=self.config.embeddings.default_provider,
            **self.config.embeddings.get(self.config.embeddings.default_provider, {}),
        )

        # Verify collection exists
        try:
            self.client.get_collection(collection)
        except Exception:
            # Create collection with embedding dimension
            self.client.create_collection(
                name=collection,
                dimension=self.embed_provider.dimension,
            )

    def ingest_file(
        self,
        file_path: Path,
        base_metadata: Optional[dict[str, Any]] = None,
    ) -> IngestedFile:
        """Ingest a single file."""
        processor = FileProcessor(
            client=self.client,
            chunker=self.chunker,
            embed_provider=self.embed_provider,
            collection=self.collection,
        )
        return processor.process_file(file_path, base_metadata)

    def ingest_directory(
        self,
        directory: Path,
        pattern: str = "**/*",
        exclude_patterns: Optional[list[str]] = None,
        recursive: bool = True,
        base_metadata: Optional[dict[str, Any]] = None,
        max_workers: int = 4,
        show_progress: bool = True,
    ) -> IngestResult:
        """Ingest all matching files in a directory."""
        start = time.time()
        exclude_patterns = exclude_patterns or [
            "**/__pycache__/**",
            "**/.git/**",
            "**/node_modules/**",
            "**/*.pyc",
            "**/.venv/**",
            "**/venv/**",
            "**/*.lock",
            "**/*.log",
        ]

        # Find files
        files = list(directory.glob(pattern))
        if not recursive:
            files = [f for f in files if f.parent == directory]

        # Filter
        filtered_files = []
        for f in files:
            if f.is_file():
                rel = f.relative_to(directory)
                if not any(rel.match(pat) for pat in exclude_patterns):
                    filtered_files.append(f)

        if not filtered_files:
            return IngestResult(
                files=[],
                total_chunks=0,
                total_vectors=0,
                total_latency_ms=(time.time() - start) * 1000,
            )

        # Process files in parallel
        results: list[IngestedFile] = []
        processor = FileProcessor(
            client=self.client,
            chunker=self.chunker,
            embed_provider=self.embed_provider,
            collection=self.collection,
        )

        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(processor.process_file, f, base_metadata): f
                    for f in filtered_files
                }
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    if show_progress:
                        status = "✓" if result.error is None else "✗"
                        print(f"  {status} {result.path} ({result.chunks_created} chunks, {result.latency_ms:.0f}ms)")
                        if result.error:
                            print(f"    Error: {result.error}")
        else:
            for f in filtered_files:
                result = processor.process_file(f, base_metadata)
                results.append(result)
                if show_progress:
                    status = "✓" if result.error is None else "✗"
                    print(f"  {status} {f.relative_to(directory)} ({result.chunks_created} chunks, {result.latency_ms:.0f}ms)")
                    if result.error:
                        print(f"    Error: {result.error}")

        total_latency = (time.time() - start) * 1000
        errors = [r.error for r in results if r.error]

        return IngestResult(
            files=results,
            total_chunks=sum(r.chunks_created for r in results),
            total_vectors=sum(r.vectors_indexed for r in results),
            total_latency_ms=total_latency,
            errors=errors,
        )

    def ingest_texts(
        self,
        texts: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> IngestResult:
        """Ingest raw texts directly (no file I/O)."""
        start = time.time()

        if not texts:
            return IngestResult(
                files=[],
                total_chunks=0,
                total_vectors=0,
                total_latency_ms=0,
            )

        metadatas = metadatas or [{}] * len(texts)
        ids = ids or [None] * len(texts)

        all_documents = []
        all_chunks = 0

        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            chunks = self.chunker.chunk(text, meta)
            chunk_texts = [c.text for c in chunks]

            if not chunk_texts:
                continue

            embed_result = self.embed_provider.embed(chunk_texts)

            for j, chunk in enumerate(chunks):
                if j >= len(embed_result.vectors):
                    break
                all_documents.append(Document(
                    collection=self.collection,
                    vector=embed_result.vectors[j].tolist(),
                    text=chunk.text,
                    metadata=chunk.metadata,
                ))

            all_chunks += len(chunks)

        # Batch insert all
        if all_documents:
            self.client.insert_batch(self.collection, all_documents)

        return IngestResult(
            files=[IngestedFile(
                path=f"text_{i}",
                chunks_created=len(self.chunker.chunk(t, m)),
                vectors_indexed=len(self.chunker.chunk(t, m)),
                latency_ms=0,
            ) for i, (t, m) in enumerate(zip(texts, metadatas))],
            total_chunks=all_chunks,
            total_vectors=len(all_documents),
            total_latency_ms=(time.time() - start) * 1000,
        )


def create_ingestion_pipeline(
    collection: str,
    config: Optional[GhostConfig] = None,
    client: Optional[GhostClient] = None,
) -> IngestionPipeline:
    """Factory function to create ingestion pipeline."""
    cfg = config or GhostConfig()
    cl = client or GhostClient(cfg)
    return IngestionPipeline(
        client=cl,
        collection=collection,
        config=cfg,
    )