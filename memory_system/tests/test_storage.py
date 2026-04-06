"""
JEBAT Memory System - Storage Backend Tests
Comprehensive test suite for database, vector search, and storage operations
"""

import asyncio
import os
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
import pytest

from memory_system.core.memory_layers import (
    HeatScore,
    Memory,
    MemoryImportance,
    MemoryLayer,
    MemoryMetadata,
    MemoryModality,
)
from memory_system.storage import (
    DatabaseConfig,
    DatabaseManager,
    EmbeddingConfig,
    EmbeddingEngine,
    MemoryStorage,
    SearchConfig,
    StorageBackend,
    VectorSearchEngine,
)
c
# ========================================
# Fixtures
# ========================================


@pytest.fixture
def test_db_config():
    """Test database configuration"""
    return DatabaseConfig(
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        database=os.getenv("TEST_DB_NAME", "jebat_test"),
        user=os.getenv("TEST_DB_USER", "jebat"),
        password=os.getenv("TEST_DB_PASSWORD", "jebat_secure_pass"),
        enable_timescale=True,
        enable_pgvector=True,
    )


@pytest.fixture
def test_embedding_config():
    """Test embedding configuration"""
    return EmbeddingConfig(
        provider="openai",
        model="text-embedding-3-small",
        dimension=1536,
        cache_embeddings=True,
    )


@pytest.fixture
def test_search_config():
    """Test search configuration"""
    return SearchConfig(
        similarity_threshold=0.5,
        max_results=10,
        rerank=True,
        use_hybrid=True,
    )


@pytest.fixture
async def db_manager(test_db_config):
    """Database manager fixture"""
    manager = DatabaseManager(test_db_config)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
async def memory_storage(db_manager):
    """Memory storage fixture"""
    storage = MemoryStorage(db_manager)
    yield storage
    # Cleanup test data
    await db_manager.execute("DELETE FROM memories WHERE user_id LIKE 'test_%'")


@pytest.fixture
async def embedding_engine(test_embedding_config):
    """Embedding engine fixture"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    engine = EmbeddingEngine(test_embedding_config, api_key)
    yield engine
    engine.clear_cache()


@pytest.fixture
async def storage_backend(test_db_config, test_embedding_config, test_search_config):
    """Storage backend fixture"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    backend = StorageBackend(
        db_config=test_db_config,
        embedding_config=test_embedding_config,
        search_config=test_search_config,
        openai_api_key=api_key,
    )
    await backend.initialize()
    yield backend

    # Cleanup
    await backend.db_manager.execute("DELETE FROM memories WHERE user_id LIKE 'test_%'")
    await backend.close()


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing"""
    return Memory(
        memory_id=f"test_{uuid4().hex[:8]}",
        content="This is a test memory about machine learning and AI systems.",
        layer=MemoryLayer.M1,
        metadata=MemoryMetadata(
            modality=MemoryModality.TEXT,
            importance=MemoryImportance.MEDIUM,
            session_id="test_session_001",
            tags=["test", "ml", "ai"],
            entities=["machine learning", "AI"],
        ),
        heat=HeatScore(visit_count=1, interaction_depth=0.5),
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1),
    )


# ========================================
# Database Manager Tests
# ========================================


@pytest.mark.asyncio
class TestDatabaseManager:
    """Test database manager functionality"""

    async def test_initialization(self, test_db_config):
        """Test database initialization"""
        manager = DatabaseManager(test_db_config)
        await manager.initialize()

        assert manager._initialized is True
        assert manager.pool is not None

        await manager.close()

    async def test_connection_pool(self, db_manager):
        """Test connection pool operations"""
        # Test simple query
        result = await db_manager.fetchval("SELECT 1")
        assert result == 1

    async def test_extensions_enabled(self, db_manager):
        """Test that required extensions are enabled"""
        # Check pgvector
        vector_version = await db_manager.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )
        assert vector_version is not None

        # Check TimescaleDB
        ts_version = await db_manager.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
        )
        assert ts_version is not None

    async def test_tables_created(self, db_manager):
        """Test that all required tables are created"""
        tables = await db_manager.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        table_names = [row["tablename"] for row in tables]

        assert "memories" in table_names
        assert "memory_consolidations" in table_names
        assert "memory_access_log" in table_names
        assert "sessions" in table_names


# ========================================
# Memory Storage Tests
# ========================================


@pytest.mark.asyncio
class TestMemoryStorage:
    """Test memory storage operations"""

    async def test_store_memory(self, memory_storage, sample_memory):
        """Test storing a memory"""
        user_id = "test_user_001"

        db_id = await memory_storage.store_memory(
            memory_id=sample_memory.memory_id,
            user_id=user_id,
            content=sample_memory.content,
            layer=sample_memory.layer.value,
            modality=sample_memory.metadata.modality.value,
            importance=sample_memory.metadata.importance.value,
            session_id=sample_memory.metadata.session_id,
            tags=sample_memory.metadata.tags,
            entities=sample_memory.metadata.entities,
            expires_at=sample_memory.expires_at,
        )

        assert db_id is not None

    async def test_retrieve_memory(self, memory_storage, sample_memory):
        """Test retrieving a memory"""
        user_id = "test_user_002"

        # Store first
        await memory_storage.store_memory(
            memory_id=sample_memory.memory_id,
            user_id=user_id,
            content=sample_memory.content,
            layer=sample_memory.layer.value,
            modality=sample_memory.metadata.modality.value,
            importance=sample_memory.metadata.importance.value,
        )

        # Retrieve
        retrieved = await memory_storage.retrieve_memory(
            sample_memory.memory_id, user_id
        )

        assert retrieved is not None
        assert retrieved["memory_id"] == sample_memory.memory_id
        assert retrieved["content"] == sample_memory.content
        assert retrieved["user_id"] == user_id

    async def test_search_memories_by_tags(self, memory_storage):
        """Test searching memories by tags"""
        user_id = "test_user_003"

        # Store multiple memories with different tags
        for i in range(3):
            await memory_storage.store_memory(
                memory_id=f"test_mem_{i}",
                user_id=user_id,
                content=f"Test memory {i}",
                layer="M1",
                modality="TEXT",
                importance="MEDIUM",
                tags=["test", f"tag_{i}"],
            )

        # Search by tag
        results = await memory_storage.search_memories(
            user_id=user_id,
            tags=["test"],
            limit=10,
        )

        assert len(results) == 3

    async def test_delete_memory_soft(self, memory_storage, sample_memory):
        """Test soft deletion of memory"""
        user_id = "test_user_004"

        # Store memory
        await memory_storage.store_memory(
            memory_id=sample_memory.memory_id,
            user_id=user_id,
            content=sample_memory.content,
            layer=sample_memory.layer.value,
            modality=sample_memory.metadata.modality.value,
            importance=sample_memory.metadata.importance.value,
        )

        # Soft delete
        deleted = await memory_storage.delete_memory(
            sample_memory.memory_id, soft_delete=True
        )
        assert deleted is True

        # Should not be retrievable
        retrieved = await memory_storage.retrieve_memory(
            sample_memory.memory_id, user_id
        )
        assert retrieved is None

    async def test_update_heat_score(self, memory_storage, sample_memory):
        """Test updating heat score"""
        user_id = "test_user_005"

        # Store memory
        await memory_storage.store_memory(
            memory_id=sample_memory.memory_id,
            user_id=user_id,
            content=sample_memory.content,
            layer=sample_memory.layer.value,
            modality=sample_memory.metadata.modality.value,
            importance=sample_memory.metadata.importance.value,
        )

        # Update heat
        await memory_storage.update_heat_score(
            memory_id=sample_memory.memory_id,
            visit_count=10,
            interaction_depth=0.9,
            recency_score=0.95,
            total_score=9.5,
        )

        # Retrieve and check
        retrieved = await memory_storage.retrieve_memory(
            sample_memory.memory_id, user_id
        )
        assert retrieved["heat_visit_count"] == 10
        assert retrieved["heat_interaction_depth"] == 0.9

    async def test_cleanup_expired(self, memory_storage):
        """Test cleaning up expired memories"""
        user_id = "test_user_006"

        # Store expired memory
        await memory_storage.store_memory(
            memory_id="expired_mem",
            user_id=user_id,
            content="Expired content",
            layer="M0",
            modality="TEXT",
            importance="LOW",
            expires_at=datetime.now() - timedelta(hours=1),
        )

        # Cleanup
        count = await memory_storage.cleanup_expired(layer="M0")
        assert count >= 1

    async def test_layer_stats(self, memory_storage):
        """Test getting layer statistics"""
        user_id = "test_user_007"

        # Store memories in different layers
        for layer in ["M0", "M1", "M2"]:
            await memory_storage.store_memory(
                memory_id=f"mem_{layer}",
                user_id=user_id,
                content=f"Content for {layer}",
                layer=layer,
                modality="TEXT",
                importance="MEDIUM",
            )

        # Get stats
        stats = await memory_storage.get_layer_stats(user_id, "M1")
        assert stats["total_count"] >= 1


# ========================================
# Embedding Engine Tests
# ========================================


@pytest.mark.asyncio
class TestEmbeddingEngine:
    """Test embedding generation"""

    async def test_embed_text(self, embedding_engine):
        """Test single text embedding"""
        text = "This is a test sentence for embedding."
        embedding = await embedding_engine.embed_text(text)

        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 1536

    async def test_embed_batch(self, embedding_engine):
        """Test batch embedding"""
        texts = [
            "First test sentence",
            "Second test sentence",
            "Third test sentence",
        ]

        embeddings = await embedding_engine.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(len(emb) == 1536 for emb in embeddings)

    async def test_embedding_cache(self, embedding_engine):
        """Test embedding caching"""
        text = "Cached test sentence"

        # First call - should generate
        embedding1 = await embedding_engine.embed_text(text)
        cache_size_1 = embedding_engine.get_cache_size()

        # Second call - should use cache
        embedding2 = await embedding_engine.embed_text(text)
        cache_size_2 = embedding_engine.get_cache_size()

        assert np.array_equal(embedding1, embedding2)
        assert cache_size_1 == cache_size_2

    async def test_normalize_embedding(self, embedding_engine):
        """Test embedding normalization"""
        text = "Normalization test"
        embedding = await embedding_engine.embed_text(text)

        # Check if normalized (L2 norm should be 1)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01


# ========================================
# Vector Search Tests
# ========================================


@pytest.mark.asyncio
class TestVectorSearch:
    """Test vector search operations"""

    async def test_basic_search(self, embedding_engine, test_search_config):
        """Test basic vector search"""
        search_engine = VectorSearchEngine(embedding_engine, test_search_config)

        # Create test embeddings
        texts = [
            "Machine learning is a subset of AI",
            "Deep learning uses neural networks",
            "Python is a programming language",
        ]

        embeddings = await embedding_engine.embed_batch(texts)
        metadata = [{"text": text, "idx": i} for i, text in enumerate(texts)]

        # Search
        query = "artificial intelligence and ML"
        results = await search_engine.search(query, embeddings, metadata, top_k=2)

        assert len(results) > 0
        assert len(results) <= 2

        # First result should be most relevant
        assert "machine learning" in results[0][2]["text"].lower()

    async def test_similarity_threshold(self, embedding_engine, test_search_config):
        """Test similarity threshold filtering"""
        test_search_config.similarity_threshold = 0.9  # Very high threshold

        search_engine = VectorSearchEngine(embedding_engine, test_search_config)

        texts = ["Completely unrelated text about cooking"]
        embeddings = await embedding_engine.embed_batch(texts)
        metadata = [{"text": text} for text in texts]

        query = "machine learning algorithms"
        results = await search_engine.search(query, embeddings, metadata)

        # Should have few or no results due to high threshold
        assert len(results) == 0


# ========================================
# Storage Backend Integration Tests
# ========================================


@pytest.mark.asyncio
class TestStorageBackend:
    """Test integrated storage backend"""

    async def test_store_and_retrieve(self, storage_backend, sample_memory):
        """Test storing and retrieving a memory"""
        user_id = "test_user_100"

        # Store
        db_id = await storage_backend.store_memory(sample_memory, user_id)
        assert db_id is not None

        # Retrieve
        retrieved = await storage_backend.retrieve_memory(
            sample_memory.memory_id, user_id
        )
        assert retrieved is not None
        assert retrieved.memory_id == sample_memory.memory_id
        assert retrieved.content == sample_memory.content

    async def test_semantic_search(self, storage_backend):
        """Test semantic search"""
        user_id = "test_user_101"

        # Store test memories
        memories = [
            Memory(
                memory_id=f"test_{i}",
                content=content,
                layer=MemoryLayer.M1,
                metadata=MemoryMetadata(
                    modality=MemoryModality.TEXT,
                    importance=MemoryImportance.MEDIUM,
                ),
                heat=HeatScore(),
                created_at=datetime.now(),
            )
            for i, content in enumerate(
                [
                    "Python is great for machine learning",
                    "JavaScript is used for web development",
                    "Deep learning requires GPUs",
                ]
            )
        ]

        for memory in memories:
            await storage_backend.store_memory(memory, user_id)

        # Search
        results = await storage_backend.semantic_search(
            user_id=user_id,
            query="AI and ML programming",
            limit=2,
            min_similarity=0.5,
        )

        assert len(results) > 0
        # Most relevant should be about machine learning
        assert "machine learning" in results[0][0].content.lower()

    async def test_batch_operations(self, storage_backend):
        """Test batch store and retrieve"""
        user_id = "test_user_102"

        # Create batch of memories
        memories = [
            Memory(
                memory_id=f"batch_{i}",
                content=f"Batch memory {i}",
                layer=MemoryLayer.M1,
                metadata=MemoryMetadata(
                    modality=MemoryModality.TEXT,
                    importance=MemoryImportance.MEDIUM,
                ),
                heat=HeatScore(),
                created_at=datetime.now(),
            )
            for i in range(5)
        ]

        # Store batch
        db_ids = await storage_backend.store_memories_batch(memories, user_id)
        assert len(db_ids) == 5

        # Retrieve batch
        memory_ids = [m.memory_id for m in memories]
        retrieved = await storage_backend.retrieve_memories_batch(memory_ids, user_id)
        assert len(retrieved) == 5
        assert all(m is not None for m in retrieved)

    async def test_consolidation(self, storage_backend):
        """Test memory consolidation"""
        user_id = "test_user_103"

        # Source memory (M1)
        source = Memory(
            memory_id="source_mem",
            content="Original episodic memory",
            layer=MemoryLayer.M1,
            metadata=MemoryMetadata(
                modality=MemoryModality.TEXT,
                importance=MemoryImportance.MEDIUM,
            ),
            heat=HeatScore(visit_count=10),
            created_at=datetime.now(),
        )

        # Store source
        await storage_backend.store_memory(source, user_id)

        # Target memory (M2)
        target = Memory(
            memory_id="target_mem",
            content="Consolidated semantic memory",
            layer=MemoryLayer.M2,
            metadata=MemoryMetadata(
                modality=MemoryModality.TEXT,
                importance=MemoryImportance.HIGH,
                parent_memory_id=source.memory_id,
            ),
            heat=source.heat,
            created_at=datetime.now(),
        )

        # Consolidate
        target_id = await storage_backend.consolidate_memory(
            source_memory=source,
            target_memory=target,
            user_id=user_id,
            reason="High heat score",
        )

        assert target_id is not None

        # Source should be soft-deleted
        source_retrieved = await storage_backend.retrieve_memory(
            source.memory_id, user_id
        )
        assert source_retrieved is None

        # Target should exist
        target_retrieved = await storage_backend.retrieve_memory(
            target.memory_id, user_id
        )
        assert target_retrieved is not None

    async def test_related_memories(self, storage_backend):
        """Test finding related memories"""
        user_id = "test_user_104"

        # Store related memories
        memories = [
            Memory(
                memory_id=f"related_{i}",
                content=content,
                layer=MemoryLayer.M2,
                metadata=MemoryMetadata(
                    modality=MemoryModality.TEXT,
                    importance=MemoryImportance.MEDIUM,
                ),
                heat=HeatScore(),
                created_at=datetime.now(),
            )
            for i, content in enumerate(
                [
                    "Python machine learning with scikit-learn",
                    "Deep learning with PyTorch and TensorFlow",
                    "Data science using pandas and numpy",
                    "Web development with Django",
                ]
            )
        ]

        for memory in memories:
            await storage_backend.store_memory(memory, user_id)

        # Find related to first memory
        related = await storage_backend.get_related_memories(
            memory=memories[0],
            user_id=user_id,
            limit=2,
        )

        assert len(related) > 0
        # Should find other ML-related memories
        related_texts = [m[0].content for m in related]
        assert any("learning" in text.lower() for text in related_texts)

    async def test_health_check(self, storage_backend):
        """Test health check"""
        health = await storage_backend.health_check()

        assert health["initialized"] is True
        assert health["database"] == "healthy"
        assert "embedding_cache_size" in health


# ========================================
# Performance Tests
# ========================================


@pytest.mark.asyncio
@pytest.mark.slow
class TestPerformance:
    """Performance and stress tests"""

    async def test_batch_insert_performance(self, storage_backend):
        """Test batch insert performance"""
        user_id = "test_user_perf"

        # Create 100 memories
        memories = [
            Memory(
                memory_id=f"perf_{i}",
                content=f"Performance test memory {i} with some content",
                layer=MemoryLayer.M1,
                metadata=MemoryMetadata(
                    modality=MemoryModality.TEXT,
                    importance=MemoryImportance.MEDIUM,
                ),
                heat=HeatScore(),
                created_at=datetime.now(),
            )
            for i in range(100)
        ]

        import time

        start = time.time()

        db_ids = await storage_backend.store_memories_batch(memories, user_id)

        elapsed = time.time() - start

        assert len(db_ids) == 100
        assert elapsed < 30  # Should complete in under 30 seconds

    async def test_search_performance(self, storage_backend):
        """Test search performance with many memories"""
        user_id = "test_user_search_perf"

        # Store 50 memories
        memories = [
            Memory(
                memory_id=f"search_perf_{i}",
                content=f"Search test memory {i} about various topics",
                layer=MemoryLayer.M1,
                metadata=MemoryMetadata(
                    modality=MemoryModality.TEXT,
                    importance=MemoryImportance.MEDIUM,
                ),
                heat=HeatScore(),
                created_at=datetime.now(),
            )
            for i in range(50)
        ]

        await storage_backend.store_memories_batch(memories, user_id)

        import time

        start = time.time()

        results = await storage_backend.semantic_search(
            user_id=user_id,
            query="test topics",
            limit=10,
        )

        elapsed = time.time() - start

        assert len(results) > 0
        assert elapsed < 5  # Should be fast with indexes


# ========================================
# Cleanup and Utilities
# ========================================


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup test data after all tests"""
    yield
    # Additional cleanup can be added here
