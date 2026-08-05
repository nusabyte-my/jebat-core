"""Ghost DB — Tests."""

from __future__ import annotations

import os
import tempfile
import shutil
from pathlib import Path

import pytest
import numpy as np

from jebat.features.ghost_db import (
    GhostClient,
    GhostConfig,
    Collection,
    Document,
    DistanceMetric,
    HNSWParams,
    SearchFilter,
    BaseChunker,
    get_chunker,
    EmbeddingProvider,
    get_embedding_provider,
    LocalEmbeddings,
    IngestionPipeline,
    create_ingestion_pipeline,
    FileProcessor,
    IngestedFile,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_ghost.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(temp_db):
    """Create a GhostClient with temp database."""
    config = GhostConfig(path=temp_db)
    client = GhostClient(config)
    yield client
    client.close()


class TestGhostClient:
    """Test core Ghost DB client operations."""

    def test_create_collection(self, client):
        """Test creating a collection."""
        collection = client.create_collection(
            name="test_coll",
            dimension=384,
            metric=DistanceMetric.COSINE,
        )
        assert collection.name == "test_coll"
        assert collection.dimension == 384
        assert collection.metric == DistanceMetric.COSINE

    def test_create_duplicate_collection(self, client):
        """Test creating duplicate collection raises error."""
        client.create_collection("dup", dimension=384)
        with pytest.raises(Exception):
            client.create_collection("dup", dimension=384)

    def test_get_collection(self, client):
        """Test getting collection info."""
        client.create_collection("get_test", dimension=512)
        coll = client.get_collection("get_test")
        assert coll.name == "get_test"
        assert coll.dimension == 512

    def test_list_collections(self, client):
        """Test listing collections."""
        client.create_collection("coll1", dimension=384)
        client.create_collection("coll2", dimension=768)

        collections = client.list_collections()
        assert len(collections) == 2
        names = {c.name for c in collections}
        assert names == {"coll1", "coll2"}

    def test_delete_collection(self, client):
        """Test deleting a collection."""
        client.create_collection("to_delete", dimension=384)
        assert client.delete_collection("to_delete") is True
        assert client.delete_collection("to_delete") is False

    def test_insert_and_get_document(self, client):
        """Test inserting and retrieving a document."""
        client.create_collection("docs", dimension=3)

        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        doc = client.insert(
            collection="docs",
            text="Test document",
            vector=vector,
            metadata={"source": "test"},
        )

        assert doc.id is not None
        assert doc.collection == "docs"
        assert doc.text == "Test document"

        # Retrieve
        retrieved = client.get_document("docs", doc.id)
        assert retrieved.id == doc.id
        assert retrieved.text == "Test document"
        assert retrieved.metadata == {"source": "test"}

    def test_search(self, client):
        """Test vector similarity search."""
        client.create_collection("search_test", dimension=3)

        # Insert known vectors
        docs = [
            ("doc1", np.array([1.0, 0.0, 0.0], dtype=np.float32), "First document"),
            ("doc2", np.array([0.0, 1.0, 0.0], dtype=np.float32), "Second document"),
            ("doc3", np.array([0.0, 0.0, 1.0], dtype=np.float32), "Third document"),
        ]

        for doc_id, vec, text in docs:
            client.insert("search_test", text, vec, metadata={"id": doc_id})

        # Query similar to first
        query = np.array([0.9, 0.1, 0.0], dtype=np.float32)
        results = client.search("search_test", query, k=2)

        assert len(results) == 2
        assert results[0].document.metadata["id"] == "doc1"
        assert results[0].score > results[1].score

    def test_hybrid_search(self, client):
        """Test hybrid vector + text search."""
        client.create_collection("hybrid", dimension=3)

        client.insert("hybrid", "apple banana orange", np.array([1.0, 0.0, 0.0], dtype=np.float32))
        client.insert("hybrid", "cat dog bird", np.array([0.0, 1.0, 0.0], dtype=np.float32))
        client.insert("hybrid", "red green blue", np.array([0.0, 0.0, 1.0], dtype=np.float32))

        query_vec = np.array([0.9, 0.1, 0.0], dtype=np.float32)
        results = client.hybrid_search("hybrid", query_vec, "apple", k=2, alpha=0.5)

        assert len(results) == 2
        # First result should be about apple
        assert "apple" in results[0].document.text.lower()

    def test_filter_search(self, client):
        """Test metadata filtering in search."""
        client.create_collection("filter_test", dimension=2)

        client.insert("filter_test", "doc A", np.array([1.0, 0.0], dtype=np.float32), metadata={"category": "tech", "year": 2024})
        client.insert("filter_test", "doc B", np.array([0.0, 1.0], dtype=np.float32), metadata={"category": "science", "year": 2023})
        client.insert("filter_test", "doc C", np.array([0.7, 0.7], dtype=np.float32), metadata={"category": "tech", "year": 2022})

        # Filter by category
        filter_ = SearchFilter(eq={"category": "tech"})
        results = client.search("filter_test", np.array([1.0, 0.0], dtype=np.float32), k=5, filter_=filter_)

        assert all(r.document.metadata["category"] == "tech" for r in results)

    def test_update_document(self, client):
        """Test updating a document."""
        client.create_collection("update_test", dimension=2)

        doc = client.insert("update_test", "Original", np.array([1.0, 0.0], dtype=np.float32))
        updated = client.update_document(
            "update_test",
            doc.id,
            text="Updated",
            vector=np.array([0.0, 1.0], dtype=np.float32),
            metadata={"version": 2},
        )

        assert updated.text == "Updated"
        assert updated.metadata["version"] == 2

    def test_delete_document(self, client):
        """Test deleting a document."""
        client.create_collection("delete_test", dimension=2)

        doc = client.insert("delete_test", "To delete", np.array([1.0, 0.0], dtype=np.float32))
        assert client.delete_document("delete_test", doc.id) is True
        assert client.delete_document("delete_test", doc.id) is False

        with pytest.raises(Exception):
            client.get_document("delete_test", doc.id)

    def test_batch_insert(self, client):
        """Test batch document insertion."""
        client.create_collection("batch_test", dimension=2)

        docs = [
            Document(collection="batch_test", vector=[1.0, 0.0], text=f"Doc {i}", metadata={"idx": i})
            for i in range(10)
        ]

        client.insert_batch("batch_test", docs)

        # Verify all inserted
        results = client.search("batch_test", np.array([1.0, 0.0], dtype=np.float32), k=10)
        assert len(results) == 10

    def test_collection_stats(self, client):
        """Test collection statistics."""
        client.create_collection("stats_test", dimension=384)

        for i in range(5):
            client.insert("stats_test", f"Doc {i}", np.random.rand(384).astype(np.float32))

        stats = client.collection_stats("stats_test")

        assert stats.name == "stats_test"
        assert stats.dimension == 384
        assert stats.document_count == 5
        assert stats.size_bytes > 0

    def test_snapshot_restore(self, client, temp_db):
        """Test database snapshot and restore."""
        client.create_collection("snap_test", dimension=10)
        for i in range(3):
            client.insert("snap_test", f"Doc {i}", np.random.rand(10).astype(np.float32))

        # Create snapshot
        snap_path = temp_db + ".snap"
        client.snapshot(snap_path)

        # Verify snapshot exists
        assert Path(snap_path).exists()

        # Restore to new client
        new_client = GhostClient(GhostConfig(path=snap_path))
        collections = new_client.list_collections()
        assert any(c.name == "snap_test" for c in collections)

        stats = new_client.collection_stats("snap_test")
        assert stats.document_count == 3

        new_client.close()

    def test_compact(self, client):
        """Test database compaction."""
        client.create_collection("compact_test", dimension=10)

        for i in range(10):
            client.insert("compact_test", f"Doc {i}", np.random.rand(10).astype(np.float32))

        # Delete some
        results = client.search("compact_test", np.random.rand(10).astype(np.float32), k=5)
        for r in results:
            client.delete_document("compact_test", r.document.id)

        reclaimed = client.compact()
        assert reclaimed >= 0


class TestChunkers:
    """Test text chunking strategies."""

    def test_recursive_chunker(self):
        """Test recursive character chunker."""
        chunker = get_chunker("recursive", chunk_size=100, chunk_overlap=20)
        text = "This is a test. " * 20
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.text) <= 120  # chunk_size + overlap

    def test_semantic_chunker(self):
        """Test semantic sentence chunker."""
        chunker = get_chunker("semantic", chunk_size=100, chunk_overlap=20)
        text = "This is sentence one. This is sentence two. This is sentence three. " * 5
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.text) <= 120

    def test_markdown_chunker(self):
        """Test markdown-aware chunker."""
        chunker = get_chunker("markdown", chunk_size=100, chunk_overlap=20)
        text = "# Header\n\nContent here.\n\n## Subheader\n\nMore content."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        # First chunk should have header
        assert "Header" in chunks[0].text

    def test_fixed_chunker(self):
        """Test fixed-size chunker."""
        chunker = get_chunker("fixed", chunk_size=50, chunk_overlap=10)
        text = "A" * 200
        chunks = chunker.chunk(text)

        assert len(chunks) == (200 - 50) // (50 - 10) + 1  # (total - size) / step + 1


class TestEmbeddingProviders:
    """Test embedding providers (requires sentence-transformers)."""

    @pytest.mark.skipif(
        not shutil.which("python") or os.system("python -c 'import sentence_transformers' >/dev/null 2>&1") != 0,
        reason="sentence-transformers not installed",
    )
    def test_local_embeddings(self):
        """Test local sentence-transformer embeddings."""
        provider = get_embedding_provider("local", model="BAAI/bge-small-en-v1.5")
        assert provider.dimension == 384

        result = provider.embed(["Test text", "Another text"])
        assert result.vectors.shape == (2, 384)
        assert result.provider == "local"

    def test_custom_embeddings(self):
        """Test custom embedding function."""
        def custom_embed(texts):
            return np.random.rand(len(texts), 128).astype(np.float32)

        provider = get_embedding_provider("custom", fn=custom_embed, dimension=128)
        assert provider.dimension == 128

        result = provider.embed(["test"])
        assert result.vectors.shape == (1, 128)


class TestIngestionPipeline:
    """Test file ingestion pipeline."""

    def test_ingest_texts(self, client):
        """Test ingesting raw texts."""
        pipeline = create_ingestion_pipeline("ingest_test", client=client)

        result = pipeline.ingest_texts(
            texts=["First document", "Second document"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
        )

        assert result.total_vectors == 2
        assert result.total_chunks == 2

    def test_ingest_directory(self, temp_db):
        """Test ingesting a directory of files."""
        # Create test files
        test_dir = Path(temp_db).parent / "test_files"
        test_dir.mkdir(exist_ok=True)

        (test_dir / "file1.txt").write_text("This is the first test file with some content.")
        (test_dir / "file2.md").write_text("# Header\n\nMarkdown content here.")
        (test_dir / "file3.py").write_text("def hello():\n    return 'world'")

        config = GhostConfig(path=temp_db)
        client = GhostClient(config)

        pipeline = create_ingestion_pipeline("dir_test", client=client)
        result = pipeline.ingest_directory(test_dir)

        assert result.total_vectors > 0
        assert result.success_count == 3

        client.close()

        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


class TestDistanceMetrics:
    """Test different distance metrics."""

    def test_cosine_metric(self, client):
        """Test cosine similarity search."""
        client.create_collection("cosine_test", dimension=3, metric=DistanceMetric.COSINE)

        client.insert("cosine_test", "A", np.array([1.0, 0.0, 0.0], dtype=np.float32))
        client.insert("cosine_test", "B", np.array([0.0, 1.0, 0.0], dtype=np.float32))

        # Query same as A
        results = client.search("cosine_test", np.array([1.0, 0.0, 0.0], dtype=np.float32), k=2)
        assert results[0].document.text == "A"

    def test_l2_metric(self, client):
        """Test L2 distance search."""
        client.create_collection("l2_test", dimension=2, metric=DistanceMetric.L2)

        client.insert("l2_test", "A", np.array([0.0, 0.0], dtype=np.float32))
        client.insert("l2_test", "B", np.array([10.0, 10.0], dtype=np.float32))

        # Query near A
        results = client.search("l2_test", np.array([0.1, 0.1], dtype=np.float32), k=2)
        assert results[0].document.text == "A"

    def test_inner_product_metric(self, client):
        """Test inner product search."""
        client.create_collection("ip_test", dimension=2, metric=DistanceMetric.INNER_PRODUCT)

        client.insert("ip_test", "A", np.array([1.0, 0.0], dtype=np.float32))
        client.insert("ip_test", "B", np.array([0.0, 1.0], dtype=np.float32))

        # Query aligned with A
        results = client.search("ip_test", np.array([1.0, 0.0], dtype=np.float32), k=2)
        assert results[0].document.text == "A"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_collection_search(self, client):
        """Test searching empty collection."""
        client.create_collection("empty", dimension=3)
        results = client.search("empty", np.array([1.0, 0.0, 0.0], dtype=np.float32), k=5)
        assert results == []

    def test_dimension_mismatch(self, client):
        """Test vector dimension mismatch error."""
        client.create_collection("dim_test", dimension=3)

        with pytest.raises(Exception):
            client.insert("dim_test", "Wrong dim", np.array([1.0, 0.0], dtype=np.float32))

    def test_nonexistent_collection(self, client):
        """Test operations on nonexistent collection."""
        with pytest.raises(Exception):
            client.get_collection("does_not_exist")

    def test_invalid_filter(self, client):
        """Test invalid filter syntax."""
        client.create_collection("filter_err", dimension=2)

        # This should not crash, just return no results
        filter_ = SearchFilter(invalid_field="value")
        results = client.search("filter_err", np.array([1.0, 0.0], dtype=np.float32), filter_=filter_)
        assert results == []  # No results for invalid filter


if __name__ == "__main__":
    pytest.main([__file__, "-v"])