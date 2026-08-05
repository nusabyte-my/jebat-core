"""Ghost DB — Text Chunkers for Ingestion Pipeline."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Chunk:
    """A text chunk with metadata."""
    text: str
    start_char: int
    end_char: int
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseChunker(ABC):
    """Abstract base class for text chunkers."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        **kwargs
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        """Split text into chunks."""
        pass

    def _merge_metadata(self, base: dict, chunk_meta: dict) -> dict:
        """Merge base metadata with chunk-specific metadata."""
        merged = base.copy() if base else {}
        merged.update(chunk_meta)
        return merged


class RecursiveChunker(BaseChunker):
    """Recursive character text splitter (LangChain-style)."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[list[str]] = None,
        **kwargs
    ):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        if not text:
            return []

        chunks = self._split_text(text, self.separators)
        return [
            Chunk(
                text=chunk,
                start_char=text.find(chunk, (chunks[i-1].end_char if i > 0 else 0)),
                end_char=text.find(chunk, (chunks[i-1].end_char if i > 0 else 0)) + len(chunk),
                metadata=self._merge_metadata(metadata or {}, {"chunk_index": i, "chunk_count": len(chunks)})
            )
            for i, chunk in enumerate(chunks)
        ]

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text by separators."""
        if not text:
            return []

        # Find first separator that splits the text
        separator = None
        for sep in separators:
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                break

        if separator is None:
            return [text]

        splits = text.split(separator)
        result = []
        current = ""

        for split in splits:
            if len(current) + len(split) + len(separator) <= self.chunk_size:
                current += (separator if current else "") + split
            else:
                if current:
                    result.append(current)
                current = split

                # If single split is too large, recurse
                while len(current) > self.chunk_size and len(separators) > 1:
                    sub_splits = self._split_text(current, separators[1:])
                    if len(sub_splits) > 1:
                        result.extend(sub_splits[:-1])
                        current = sub_splits[-1]
                    else:
                        break

        if current:
            result.append(current)

        # Apply overlap
        if self.chunk_overlap > 0 and len(result) > 1:
            overlapped = [result[0]]
            for i in range(1, len(result)):
                prev = result[i-1]
                overlap_text = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev
                overlapped.append(overlap_text + result[i])
            return overlapped

        return result


class SemanticChunker(BaseChunker):
    """Semantic chunker using sentence boundaries."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        **kwargs
    ):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        try:
            import nltk
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            import nltk
            nltk.download('punkt', quiet=True)

    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        import nltk

        if not text:
            return []

        sentences = nltk.sent_tokenize(text)
        chunks = []
        current = ""
        current_start = 0

        for sent in sentences:
            if len(current) + len(sent) + 1 <= self.chunk_size:
                current += (" " if current else "") + sent
            else:
                if current:
                    chunks.append(Chunk(
                        text=current,
                        start_char=current_start,
                        end_char=current_start + len(current),
                        metadata=self._merge_metadata(metadata or {}, {
                            "chunk_index": len(chunks),
                            "sentence_count": current.count(". ") + 1
                        })
                    ))
                current = sent
                current_start = text.find(sent, current_start)

        if current:
            chunks.append(Chunk(
                text=current,
                start_char=current_start,
                end_char=current_start + len(current),
                metadata=self._merge_metadata(metadata or {}, {
                    "chunk_index": len(chunks),
                    "sentence_count": current.count(". ") + 1
                })
            ))

        # Apply overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            for i in range(1, len(chunks)):
                prev_text = chunks[i-1].text
                overlap = prev_text[-self.chunk_overlap:] if len(prev_text) > self.chunk_overlap else prev_text
                chunks[i] = Chunk(
                    text=overlap + " " + chunks[i].text,
                    start_char=chunks[i].start_char,
                    end_char=chunks[i].end_char,
                    metadata=chunks[i].metadata
                )

        return chunks


class MarkdownChunker(BaseChunker):
    """Markdown-aware chunker preserving header hierarchy."""

    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        **kwargs
    ):
        super().__init__(chunk_size, chunk_overlap, **kwargs)

    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        if not text:
            return []

        # Split by headers
        sections = self._split_by_headers(text)
        chunks = []

        for section in sections:
            section_chunks = self._chunk_section(section, metadata)
            chunks.extend(section_chunks)

        # Update chunk indices
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_count"] = len(chunks)

        return chunks

    def _split_by_headers(self, text: str) -> list[dict]:
        """Split markdown by headers, preserving hierarchy."""
        matches = list(self.HEADER_PATTERN.finditer(text))
        if not matches:
            return [{"level": 0, "title": "", "content": text, "start": 0, "end": len(text)}]

        sections = []
        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end]
            sections.append({
                "level": level,
                "title": title,
                "content": content,
                "start": start,
                "end": end,
            })

        return sections

    def _chunk_section(self, section: dict, base_meta: Optional[dict]) -> list[Chunk]:
        """Chunk a markdown section."""
        content = section["content"]
        header = f"{'#' * section['level']} {section['title']}\n" if section["title"] else ""

        # Use recursive chunker for content
        chunker = RecursiveChunker(
            chunk_size=self.chunk_size - len(header),
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        sub_chunks = chunker.chunk(content, metadata={
            **(base_meta or {}),
            "header_level": section["level"],
            "header_title": section["title"],
            "section_start": section["start"],
            "section_end": section["end"],
        })

        # Prepend header to first chunk
        if sub_chunks:
            first = sub_chunks[0]
            sub_chunks[0] = Chunk(
                text=header + first.text,
                start_char=first.start_char,
                end_char=first.end_char + len(header),
                metadata=first.metadata
            )

        return sub_chunks


class CodeChunker(BaseChunker):
    """Code-aware chunker using tree-sitter for AST-based splitting."""

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "c_sharp",
    }

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        language: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        self.language = language
        self.file_path = file_path

        if file_path and not language:
            self.language = self.LANGUAGE_MAP.get(file_path.rsplit(".", 1)[-1].lower())

    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        if not text:
            return []

        # Try AST-based chunking first
        if self.language and TREE_SITTER_AVAILABLE:
            try:
                return self._chunk_ast(text, metadata)
            except Exception:
                pass  # Fall back to recursive

        # Fallback: recursive with code-friendly separators
        return self._chunk_recursive(text, metadata)

    def _chunk_ast(self, text: str, metadata: Optional[dict]) -> list[Chunk]:
        """AST-based chunking using tree-sitter."""
        # This is a simplified implementation
        # In production, you'd load the tree-sitter language grammar
        # and extract function/class definitions as chunks
        return self._chunk_recursive(text, metadata)

    def _chunk_recursive(self, text: str, metadata: Optional[dict]) -> list[Chunk]:
        """Recursive chunking with code-friendly separators."""
        chunker = RecursiveChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\nclass ",
                "\n\ndef ",
                "\n\nasync def ",
                "\n\n",
                "\n",
                " ",
                "",
            ]
        )
        return chunker.chunk(text, metadata)


class FixedSizeChunker(BaseChunker):
    """Simple fixed-size chunker with overlap (fastest, least semantic)."""

    def chunk(self, text: str, metadata: Optional[dict[str, Any]] = None) -> list[Chunk]:
        if not text:
            return []

        chunks = []
        step = self.chunk_size - self.chunk_overlap

        for i in range(0, len(text), step):
            chunk_text = text[i:i + self.chunk_size]
            chunks.append(Chunk(
                text=chunk_text,
                start_char=i,
                end_char=min(i + self.chunk_size, len(text)),
                metadata=self._merge_metadata(metadata or {}, {
                    "chunk_index": len(chunks),
                    "chunk_size": len(chunk_text),
                })
            ))

        return chunks


def get_chunker(
    strategy: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    **kwargs
) -> BaseChunker:
    """Factory function to get chunker by strategy."""
    chunkers = {
        "recursive": RecursiveChunker,
        "semantic": SemanticChunker,
        "markdown": MarkdownChunker,
        "code": CodeChunker,
        "fixed": FixedSizeChunker,
    }

    if strategy not in chunkers:
        raise ValueError(f"Unknown chunker: {strategy}. Options: {list(chunkers.keys())}")

    return chunkers[strategy](chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)