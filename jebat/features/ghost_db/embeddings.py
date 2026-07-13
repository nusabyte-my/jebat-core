"""Ghost DB — Embedding Providers."""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    vectors: np.ndarray          # shape: (n_texts, dimension)
    dimension: int
    model: str
    provider: str
    latency_ms: float
    token_count: int = 0


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> EmbeddingResult:
        """Generate embeddings for a list of texts."""
        pass

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.embed([text]).vectors[0]


class LocalEmbeddings(EmbeddingProvider):
    """Local embeddings using sentence-transformers."""

    _model_cache: dict[str, Any] = {}

    def __init__(
        self,
        model: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        normalize: bool = True,
        batch_size: int = 32,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.device = device
        self.normalize = normalize
        self.batch_size = batch_size
        self._model = None

    @property
    def dimension(self) -> int:
        # Common model dimensions
        dims = {
            "BAAI/bge-small-en-v1.5": 384,
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-large-en-v1.5": 1024,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "intfloat/e5-small-v2": 384,
            "intfloat/e5-base-v2": 768,
            "intfloat/e5-large-v2": 1024,
            "thenlper/gte-small": 384,
            "thenlper/gte-base": 768,
            "thenlper/gte-large": 1024,
        }
        return dims.get(self.model, 384)

    def _load_model(self):
        """Lazy load sentence-transformers model."""
        if self._model is not None:
            return

        cache_key = f"{self.model}:{self.device}"
        if cache_key in self._model_cache:
            self._model = self._model_cache[cache_key]
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self._model = SentenceTransformer(self.model, device=self.device)
        self._model_cache[cache_key] = self._model

    def embed(self, texts: list[str]) -> EmbeddingResult:
        self._load_model()
        start = time.time()

        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Ensure float32
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        latency = (time.time() - start) * 1000
        return EmbeddingResult(
            vectors=embeddings,
            dimension=self.dimension,
            model=self.model,
            provider="local",
            latency_ms=latency,
            token_count=sum(len(t.split()) for t in texts),  # approximate
        )


class OllamaEmbeddings(EmbeddingProvider):
    """Embeddings via Ollama local server."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self._dimension_cache: Optional[int] = None

    @property
    def dimension(self) -> int:
        if self._dimension_cache is not None:
            return self._dimension_cache

        # Probe dimension with a test embedding
        try:
            test = self.embed(["test"])
            self._dimension_cache = test.dimension
            return self._dimension_cache
        except Exception:
            # Fallback dimensions for known models
            dims = {
                "nomic-embed-text": 768,
                "nomic-embed-text-v1.5": 768,
                "mxbai-embed-large": 1024,
                "all-minilm": 384,
                "bge-m3": 1024,
            }
            return dims.get(self.model, 768)

    def embed(self, texts: list[str]) -> EmbeddingResult:
        import httpx

        start = time.time()
        vectors = []

        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                response.raise_for_status()
                data = response.json()
                vec = np.array(data["embedding"], dtype=np.float32)
                vectors.append(vec)

                # Cache dimension
                if self._dimension_cache is None:
                    self._dimension_cache = len(vec)

        embeddings = np.stack(vectors) if vectors else np.empty((0, self.dimension), dtype=np.float32)

        latency = (time.time() - start) * 1000
        return EmbeddingResult(
            vectors=embeddings,
            dimension=self.dimension,
            model=self.model,
            provider="ollama",
            latency_ms=latency,
            token_count=sum(len(t.split()) for t in texts),
        )


class OpenAIEmbeddings(EmbeddingProvider):
    """Embeddings via OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url

        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var or pass api_key)")

    @property
    def dimension(self) -> int:
        dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dims.get(self.model, 1536)

    def embed(self, texts: list[str]) -> EmbeddingResult:
        import httpx

        start = time.time()

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/v1/embeddings" if self.base_url else "https://api.openai.com/v1/embeddings"

        # Batch request
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                headers=headers,
                json={"model": self.model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()

        vectors = []
        for item in data["data"]:
            vec = np.array(item["embedding"], dtype=np.float32)
            vectors.append(vec)

        embeddings = np.stack(vectors) if vectors else np.empty((0, self.dimension), dtype=np.float32)

        latency = (time.time() - start) * 1000
        return EmbeddingResult(
            vectors=embeddings,
            dimension=self.dimension,
            model=self.model,
            provider="openai",
            latency_ms=latency,
            token_count=data.get("usage", {}).get("total_tokens", 0),
        )


class CustomEmbeddings(EmbeddingProvider):
    """Custom callable embedding provider."""

    def __init__(
        self,
        fn: callable,
        dimension: int,
        model: str = "custom",
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self._fn = fn
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> EmbeddingResult:
        start = time.time()
        vectors = self._fn(texts)

        if not isinstance(vectors, np.ndarray):
            vectors = np.array(vectors, dtype=np.float32)

        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        latency = (time.time() - start) * 1000
        return EmbeddingResult(
            vectors=vectors,
            dimension=self.dimension,
            model=self.model,
            provider="custom",
            latency_ms=latency,
        )


def get_embedding_provider(
    provider: str,
    model: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """Factory function to get embedding provider."""
    providers = {
        "local": LocalEmbeddings,
        "ollama": OllamaEmbeddings,
        "openai": OpenAIEmbeddings,
        "custom": CustomEmbeddings,
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Options: {list(providers.keys())}")

    defaults = {
        "local": {"model": "BAAI/bge-small-en-v1.5"},
        "ollama": {"model": "nomic-embed-text"},
        "openai": {"model": "text-embedding-3-small"},
    }

    config = {**defaults.get(provider, {}), **(model and {"model": model} or {}), **kwargs}
    return providers[provider](**config)