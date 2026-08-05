"""Ghost DB — Embedded Vector Database for Offline RAG.

A zero-dependency, in-process vector database built on SQLite + sqlite-vec.
Provides high-performance vector search, hybrid search, and MCP integration.
"""

from __future__ import annotations

from .client import GhostClient, GhostError, CollectionNotFound, DocumentNotFound, VectorDimensionMismatch
from .models import (
    GhostConfig,
    Collection,
    Document,
    SearchResult,
    DistanceMetric,
    HNSWParams,
    SearchFilter,
    IngestOptions,
)
from .chunkers import BaseChunker, Chunk, get_chunker
from .embeddings import (
    EmbeddingProvider,
    EmbeddingResult,
    LocalEmbeddings,
    OllamaEmbeddings,
    OpenAIEmbeddings,
    CustomEmbeddings,
    get_embedding_provider,
)
from .ingest import IngestionPipeline, create_ingestion_pipeline, IngestResult
from .processor import FileProcessor, IngestedFile

__version__ = "0.1.0"

__all__ = [
    # Client
    "GhostClient",
    "GhostError",
    "CollectionNotFound",
    "DocumentNotFound",
    "VectorDimensionMismatch",
    # Models
    "GhostConfig",
    "Collection",
    "Document",
    "SearchResult",
    "DistanceMetric",
    "HNSWParams",
    "SearchFilter",
    "IngestOptions",
    # Chunkers
    "BaseChunker",
    "Chunk",
    "get_chunker",
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingResult",
    "LocalEmbeddings",
    "OllamaEmbeddings",
    "OpenAIEmbeddings",
    "CustomEmbeddings",
    "get_embedding_provider",
    # Ingestion
    "IngestionPipeline",
    "create_ingestion_pipeline",
    "IngestResult",
    "FileProcessor",
    "IngestedFile",
]