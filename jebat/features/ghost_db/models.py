"""Ghost DB — Core Data Models & Types."""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator


class DistanceMetric(str, Enum):
    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "ip"


class CollectionStatus(str, Enum):
    ACTIVE = "active"
    BUILDING = "building"
    COMPACTING = "compacting"
    ERROR = "error"


@dataclass(frozen=True)
class HNSWParams:
    """HNSW index parameters (sqlite-vec compatible)."""
    m: int = 16                    # connections per layer (8-64)
    ef_construction: int = 200     # build-time search width (50-500)
    ef_search: int = 64            # query-time search width (16-256)
    max_elements: int = 1_000_000  # pre-allocated capacity

    def __post_init__(self):
        if not 8 <= self.m <= 64:
            raise ValueError("m must be in [8, 64]")
        if not 50 <= self.ef_construction <= 500:
            raise ValueError("ef_construction must be in [50, 500]")
        if not 16 <= self.ef_search <= 256:
            raise ValueError("ef_search must be in [16, 256]")


class Collection(BaseModel):
    """Vector collection metadata."""
    name: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", max_length=64)
    dimension: int = Field(..., ge=1, le=8192)
    metric: DistanceMetric = DistanceMetric.COSINE
    hnsw_params: HNSWParams = Field(default_factory=HNSWParams)
    metadata_schema: dict[str, Any] = Field(default_factory=dict)  # JSON Schema
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    status: CollectionStatus = CollectionStatus.ACTIVE
    document_count: int = 0
    size_bytes: int = 0

    @field_validator("metadata_schema", mode="before")
    @classmethod
    def _validate_schema(cls, v: Any) -> dict:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("metadata_schema must be a JSON object")
        return v


class Document(BaseModel):
    """A vector document with metadata."""
    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:16]}")
    collection: str
    vector: list[float]  # float32 array, length = collection.dimension
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def vector_np(self) -> np.ndarray:
        """Convert to float32 numpy array."""
        return np.array(self.vector, dtype=np.float32)


class SearchResult(BaseModel):
    """Search hit with score."""
    document: Document
    score: float = Field(..., ge=0.0, le=1.0)
    rank: int


class SearchFilter(BaseModel):
    """Metadata filter expression (MongoDB-like syntax)."""
    # Equality
    eq: Optional[dict[str, Any]] = None
    # Comparison
    gt: Optional[dict[str, Any]] = None
    gte: Optional[dict[str, Any]] = None
    lt: Optional[dict[str, Any]] = None
    lte: Optional[dict[str, Any]] = None
    # Array
    in_: Optional[dict[str, list[Any]]] = Field(default=None, alias="in")
    nin: Optional[dict[str, list[Any]]] = None
    # Text search (FTS5)
    text: Optional[dict[str, str]] = None
    # Logical
    and_: Optional[list["SearchFilter"]] = Field(default=None, alias="and")
    or_: Optional[list["SearchFilter"]] = Field(default=None, alias="or")
    not_: Optional["SearchFilter"] = Field(default=None, alias="not")

    model_config = {"populate_by_name": True}


SearchFilter.model_rebuild()


class IngestOptions(BaseModel):
    """Options for batch ingestion."""
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunker: Literal["recursive", "semantic", "code", "markdown"] = "recursive"
    batch_size: int = 100
    show_progress: bool = True


class CollectionStats(BaseModel):
    """Collection statistics."""
    name: str
    dimension: int
    metric: DistanceMetric
    document_count: int
    size_bytes: int
    index_size_bytes: int
    hnsw_params: HNSWParams
    metadata_schema: dict[str, Any]


class GhostConfig(BaseModel):
    """Ghost DB configuration."""
    path: str = "./data/ghost.db"
    wal_mode: bool = True
    pragmas: dict[str, Any] = Field(default_factory=lambda: {
        "cache_size": -32768,        # 32MB
        "mmap_size": 268435456,      # 256MB
        "page_size": 4096,
        "synchronous": "NORMAL",
        "journal_mode": "WAL",
    })
    hnsw_defaults: HNSWParams = Field(default_factory=HNSWParams)
    ingestion: IngestOptions = Field(default_factory=IngestOptions)
    embeddings: dict[str, Any] = Field(default_factory=lambda: {
        "default_provider": "local",
        "local": {"model": "BAAI/bge-small-en-v1.5", "device": "cpu"},
        "ollama": {"base_url": "http://localhost:11434", "model": "nomic-embed-text"},
        "openai": {"model": "text-embedding-3-small"},
    })
    mcp: dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "transport": "stdio",
        "http_port": 8099,
    })