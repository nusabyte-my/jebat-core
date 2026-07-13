"""Ghost DB — Core Client with SQLite + sqlite-vec."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Optional

import numpy as np

from .models import (
    Collection,
    CollectionStats,
    Document,
    DistanceMetric,
    GhostConfig,
    HNSWParams,
    SearchFilter,
    SearchResult,
)


class GhostError(Exception):
    """Base Ghost DB error."""
    pass


class CollectionNotFound(GhostError):
    pass


class DocumentNotFound(GhostError):
    pass


class VectorDimensionMismatch(GhostError):
    pass


class InvalidFilter(GhostError):
    pass


def _serialize_vector(vec: np.ndarray) -> bytes:
    """Serialize float32 vector to bytes for sqlite-vec."""
    if vec.dtype != np.float32:
        vec = vec.astype(np.float32)
    return vec.tobytes()


def _deserialize_vector(blob: bytes, dimension: int) -> np.ndarray:
    """Deserialize bytes to float32 vector."""
    arr = np.frombuffer(blob, dtype=np.float32)
    if len(arr) != dimension:
        raise VectorDimensionMismatch(f"Expected {dimension} dims, got {len(arr)}")
    return arr


def _filter_to_sql(filter_: Optional[SearchFilter], metadata_col: str = "metadata") -> tuple[str, list[Any]]:
    """Convert SearchFilter to SQL WHERE clause + params."""
    if filter_ is None:
        return "", []

    clauses = []
    params = []

    def add_clause(sql: str, *vals: Any) -> None:
        clauses.append(sql)
        params.extend(vals)

    def build(f: SearchFilter) -> str:
        parts = []

        if f.eq:
            for k, v in f.eq.items():
                parts.append(f"json_extract({metadata_col}, '$.{k}') = ?")
                params.append(v)

        for op, attr in [(">", "gt"), (">=", "gte"), ("<", "lt"), ("<=", "lte")]:
            vals = getattr(f, attr) or {}
            for k, v in vals.items():
                parts.append(f"json_extract({metadata_col}, '$.{k}') {op} ?")
                params.append(v)

        if f.in_:
            for k, vals_list in f.in_.items():
                placeholders = ",".join(["?"] * len(vals_list))
                parts.append(f"json_extract({metadata_col}, '$.{k}') IN ({placeholders})")
                params.extend(vals_list)

        if f.nin:
            for k, vals_list in f.nin.items():
                placeholders = ",".join(["?"] * len(vals_list))
                parts.append(f"json_extract({metadata_col}, '$.{k}') NOT IN ({placeholders})")
                params.extend(vals_list)

        if f.text:
            # Use FTS5 if available, fallback to LIKE
            for k, q in f.text.items():
                parts.append(f"{metadata_col} LIKE ?")
                params.append(f"%{q}%")

        if f.and_:
            sub_clauses = []
            for sub in f.and_:
                sub_sql = build(sub)
                if sub_sql:
                    sub_clauses.append(f"({sub_sql})")
            if sub_clauses:
                parts.append(" AND ".join(sub_clauses))

        if f.or_:
            sub_clauses = []
            for sub in f.or_:
                sub_sql = build(sub)
                if sub_sql:
                    sub_clauses.append(f"({sub_sql})")
            if sub_clauses:
                parts.append(" OR ".join(sub_clauses))

        if f.not_:
            sub_sql = build(f.not_)
            if sub_sql:
                parts.append(f"NOT ({sub_sql})")

        return " AND ".join(parts) if parts else ""

    where = build(filter_)
    return (f"WHERE {where}", params) if where else ("", params)


@dataclass
class GhostClient:
    """Main Ghost DB client."""
    config: GhostConfig
    _conn: Optional[sqlite3.Connection] = None
    _vec_initialized: bool = False

    def __post_init__(self):
        Path(self.config.path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database connection and schema."""
        self._conn = sqlite3.connect(self.config.path)
        self._conn.row_factory = sqlite3.Row

        # Apply pragmas
        for pragma, value in self.config.pragmas.items():
            self._conn.execute(f"PRAGMA {pragma} = {value}")

        # Load sqlite-vec extension
        self._load_vec_extension()

        # Create schema
        self._create_schema()
        self._vec_initialized = True

    def _load_vec_extension(self) -> None:
        """Load sqlite-vec extension."""
        try:
            self._conn.enable_load_extension(True)
            # Try common paths
            for ext_path in [
                "vec0",           # pip install sqlite-vec
                "sqlite_vec",     # alternative name
                "/usr/local/lib/sqlite3/vec0",
                "/usr/lib/sqlite3/vec0",
            ]:
                try:
                    self._conn.load_extension(ext_path)
                    return
                except Exception:
                    continue
            raise GhostError(
                "sqlite-vec extension not found. Install with: pip install sqlite-vec"
            )
        except Exception as e:
            if "sqlite-vec" not in str(e):
                raise GhostError(f"Failed to load sqlite-vec: {e}") from e
            raise

    def _create_schema(self) -> None:
        """Create database schema."""
        cur = self._conn.cursor()

        # Collections table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ghost_collections (
                name TEXT PRIMARY KEY,
                dimension INTEGER NOT NULL,
                metric TEXT NOT NULL,
                hnsw_params TEXT NOT NULL,
                metadata_schema TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                document_count INTEGER NOT NULL DEFAULT 0,
                size_bytes INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Create per-collection vector tables dynamically
        # We'll create them on collection creation

        # Global FTS5 table for text search across all collections
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS ghost_fts
            USING fts5(
                collection, doc_id, text,
                metadata UNINDEXED,
                content='',
                tokenize='porter unicode61'
            )
        """)

        self._conn.commit()

    def _create_collection_tables(self, name: str, dimension: int, metric: DistanceMetric, hnsw: HNSWParams) -> None:
        """Create vector tables for a collection."""
        cur = self._conn.cursor()

        # Main documents table
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS ghost_{name}_docs (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{{}}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        # Vector table using sqlite-vec
        metric_str = metric.value
        cur.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS ghost_{name}_vec
            USING vec0(
                id TEXT PRIMARY KEY,
                embedding FLOAT[{dimension}] DISTANCE {metric_str},
                +doc_id TEXT
            )
        """)

        # FTS5 content table for this collection
        cur.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS ghost_{name}_fts
            USING fts5(
                doc_id, text,
                metadata UNINDEXED,
                content='ghost_{name}_docs',
                content_rowid='rowid',
                tokenize='porter unicode61'
            )
        """)

        # Triggers to keep FTS in sync
        cur.execute(f"""
            CREATE TRIGGER IF NOT EXISTS ghost_{name}_fts_ai
            AFTER INSERT ON ghost_{name}_docs BEGIN
                INSERT INTO ghost_{name}_fts(rowid, doc_id, text, metadata)
                VALUES (new.rowid, new.id, new.text, new.metadata);
            END
        """)

        cur.execute(f"""
            CREATE TRIGGER IF NOT EXISTS ghost_{name}_fts_ad
            AFTER DELETE ON ghost_{name}_docs BEGIN
                INSERT INTO ghost_{name}_fts(ghost_{name}_fts, rowid, doc_id, text, metadata)
                VALUES ('delete', old.rowid, old.id, old.text, old.metadata);
            END
        """)

        cur.execute(f"""
            CREATE TRIGGER IF NOT EXISTS ghost_{name}_fts_au
            AFTER UPDATE ON ghost_{name}_docs BEGIN
                INSERT INTO ghost_{name}_fts(ghost_{name}_fts, rowid, doc_id, text, metadata)
                VALUES ('delete', old.rowid, old.id, old.text, old.metadata);
                INSERT INTO ghost_{name}_fts(rowid, doc_id, text, metadata)
                VALUES (new.rowid, new.id, new.text, new.metadata);
            END
        """)

        self._conn.commit()

    def _drop_collection_tables(self, name: str) -> None:
        """Drop all tables for a collection."""
        cur = self._conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS ghost_{name}_vec")
        cur.execute(f"DROP TABLE IF EXISTS ghost_{name}_fts")
        cur.execute(f"DROP TABLE IF EXISTS ghost_{name}_docs")
        # Clean FTS triggers
        for suffix in ["_fts_ai", "_fts_ad", "_fts_au"]:
            cur.execute(f"DROP TRIGGER IF EXISTS ghost_{name}{suffix}")
        self._conn.commit()

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Transaction context manager."""
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ─── Collection Management ────────────────────────────────────────

    def create_collection(
        self,
        name: str,
        dimension: int,
        metric: DistanceMetric = DistanceMetric.COSINE,
        hnsw_params: Optional[HNSWParams] = None,
        metadata_schema: Optional[dict[str, Any]] = None,
    ) -> Collection:
        """Create a new vector collection."""
        hnsw = hnsw_params or self.config.hnsw_defaults
        now = time.time()

        collection = Collection(
            name=name,
            dimension=dimension,
            metric=metric,
            hnsw_params=hnsw,
            metadata_schema=metadata_schema or {},
            created_at=now,
            updated_at=now,
        )

        with self._transaction() as cur:
            # Check if exists
            cur.execute("SELECT name FROM ghost_collections WHERE name = ?", (name,))
            if cur.fetchone():
                raise GhostError(f"Collection '{name}' already exists")

            # Insert collection metadata
            cur.execute("""
                INSERT INTO ghost_collections
                (name, dimension, metric, hnsw_params, metadata_schema, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, dimension, metric.value,
                json.dumps(hnsw.__dict__),
                json.dumps(metadata_schema or {}),
                now, now, CollectionStatus.ACTIVE.value
            ))

            # Create collection-specific tables
            self._create_collection_tables(name, dimension, metric, hnsw)

        return collection

    def get_collection(self, name: str) -> Collection:
        """Get collection metadata."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM ghost_collections WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            raise CollectionNotFound(f"Collection '{name}' not found")

        return Collection(
            name=row["name"],
            dimension=row["dimension"],
            metric=DistanceMetric(row["metric"]),
            hnsw_params=HNSWParams(**json.loads(row["hnsw_params"])),
            metadata_schema=json.loads(row["metadata_schema"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=CollectionStatus(row["status"]),
            document_count=row["document_count"],
            size_bytes=row["size_bytes"],
        )

    def list_collections(self) -> list[Collection]:
        """List all collections."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM ghost_collections ORDER BY created_at DESC")
        return [
            Collection(
                name=row["name"],
                dimension=row["dimension"],
                metric=DistanceMetric(row["metric"]),
                hnsw_params=HNSWParams(**json.loads(row["hnsw_params"])),
                metadata_schema=json.loads(row["metadata_schema"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                status=CollectionStatus(row["status"]),
                document_count=row["document_count"],
                size_bytes=row["size_bytes"],
            )
            for row in cur.fetchall()
        ]

    def delete_collection(self, name: str) -> bool:
        """Delete a collection and all its data."""
        with self._transaction() as cur:
            cur.execute("SELECT name FROM ghost_collections WHERE name = ?", (name,))
            if not cur.fetchone():
                return False

            cur.execute("DELETE FROM ghost_collections WHERE name = ?", (name,))
            self._drop_collection_tables(name)

        return True

    def collection_stats(self, name: str) -> CollectionStats:
        """Get detailed collection statistics."""
        coll = self.get_collection(name)
        cur = self._conn.cursor()

        # Vector index size
        cur.execute(f"SELECT COUNT(*) as cnt FROM ghost_{name}_vec")
        vec_count = cur.fetchone()["cnt"]

        # Estimate sizes
        doc_size = coll.document_count * (coll.dimension * 4 + 200)  # vector + overhead
        index_size = vec_count * (coll.dimension * 4 + 100)

        return CollectionStats(
            name=coll.name,
            dimension=coll.dimension,
            metric=coll.metric,
            document_count=coll.document_count,
            size_bytes=doc_size,
            index_size_bytes=index_size,
            hnsw_params=coll.hnsw_params,
            metadata_schema=coll.metadata_schema,
        )

    # ─── Document Operations ──────────────────────────────────────────

    def insert(
        self,
        collection: str,
        text: str,
        vector: np.ndarray,
        metadata: Optional[dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> Document:
        """Insert a single document."""
        coll = self.get_collection(collection)
        vec = np.asarray(vector, dtype=np.float32)

        if vec.shape != (coll.dimension,):
            raise VectorDimensionMismatch(
                f"Vector dimension {vec.shape[0]} != collection dimension {coll.dimension}"
            )

        doc = Document(
            id=doc_id or f"doc_{uuid.uuid4().hex[:16]}",
            collection=collection,
            vector=vec.tolist(),
            text=text,
            metadata=metadata or {},
        )
        now = time.time()

        with self._transaction() as cur:
            # Insert document
            cur.execute(f"""
                INSERT INTO ghost_{collection}_docs (id, text, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (doc.id, doc.text, json.dumps(doc.metadata), now, now))

            # Insert vector
            vec_blob = _serialize_vector(vec)
            cur.execute(f"""
                INSERT INTO ghost_{collection}_vec (id, embedding, doc_id)
                VALUES (?, ?, ?)
            """, (doc.id, vec_blob, doc.id))

            # Update collection stats
            cur.execute("""
                UPDATE ghost_collections
                SET document_count = document_count + 1,
                    updated_at = ?
                WHERE name = ?
            """, (now, collection))

        return doc

    def insert_batch(
        self,
        collection: str,
        documents: list[Document],
    ) -> list[Document]:
        """Insert multiple documents in a transaction."""
        if not documents:
            return []

        coll = self.get_collection(collection)
        now = time.time()

        with self._transaction() as cur:
            for doc in documents:
                vec = np.asarray(doc.vector, dtype=np.float32)
                if vec.shape != (coll.dimension,):
                    raise VectorDimensionMismatch(
                        f"Doc {doc.id}: dimension {vec.shape[0]} != {coll.dimension}"
                    )

                cur.execute(f"""
                    INSERT INTO ghost_{collection}_docs (id, text, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc.id, doc.text, json.dumps(doc.metadata), now, now))

                vec_blob = _serialize_vector(vec)
                cur.execute(f"""
                    INSERT INTO ghost_{collection}_vec (id, embedding, doc_id)
                    VALUES (?, ?, ?)
                """, (doc.id, vec_blob, doc.id))

            cur.execute("""
                UPDATE ghost_collections
                SET document_count = document_count + ?,
                    updated_at = ?
                WHERE name = ?
            """, (len(documents), now, collection))

        return documents

    def get_document(self, collection: str, doc_id: str) -> Document:
        """Get a document by ID."""
        coll = self.get_collection(collection)
        cur = self._conn.cursor()

        cur.execute(f"""
            SELECT id, text, metadata, created_at, updated_at
            FROM ghost_{collection}_docs WHERE id = ?
        """, (doc_id,))
        row = cur.fetchone()
        if not row:
            raise DocumentNotFound(f"Document '{doc_id}' not found in '{collection}'")

        # Get vector
        cur.execute(f"SELECT embedding FROM ghost_{collection}_vec WHERE id = ?", (doc_id,))
        vec_row = cur.fetchone()
        if not vec_row:
            raise DocumentNotFound(f"Vector for '{doc_id}' not found")

        vector = _deserialize_vector(vec_row["embedding"], coll.dimension)

        return Document(
            id=row["id"],
            collection=collection,
            vector=vector.tolist(),
            text=row["text"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_document(
        self,
        collection: str,
        doc_id: str,
        text: Optional[str] = None,
        vector: Optional[np.ndarray] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Document:
        """Update a document."""
        coll = self.get_collection(collection)
        now = time.time()

        with self._transaction() as cur:
            # Check exists
            cur.execute(f"SELECT * FROM ghost_{collection}_docs WHERE id = ?", (doc_id,))
            row = cur.fetchone()
            if not row:
                raise DocumentNotFound(f"Document '{doc_id}' not found")

            # Build update
            updates = []
            params = []

            if text is not None:
                updates.append("text = ?")
                params.append(text)
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(doc_id)
                cur.execute(f"""
                    UPDATE ghost_{collection}_docs
                    SET {", ".join(updates)}
                    WHERE id = ?
                """, params)

            if vector is not None:
                vec = np.asarray(vector, dtype=np.float32)
                if vec.shape != (coll.dimension,):
                    raise VectorDimensionMismatch(
                        f"Vector dimension {vec.shape[0]} != {coll.dimension}"
                    )
                vec_blob = _serialize_vector(vec)
                cur.execute(f"""
                    UPDATE ghost_{collection}_vec
                    SET embedding = ?
                    WHERE id = ?
                """, (vec_blob, doc_id))

        return self.get_document(collection, doc_id)

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document."""
        with self._transaction() as cur:
            cur.execute(f"DELETE FROM ghost_{collection}_docs WHERE id = ?", (doc_id,))
            cur.execute(f"DELETE FROM ghost_{collection}_vec WHERE id = ?", (doc_id,))

            if cur.rowcount > 0:
                cur.execute("""
                    UPDATE ghost_collections
                    SET document_count = document_count - 1,
                        updated_at = ?
                    WHERE name = ?
                """, (time.time(), collection))
                return True
        return False

    # ─── Search ───────────────────────────────────────────────────────

    def search(
        self,
        collection: str,
        query_vector: np.ndarray,
        k: int = 10,
        filter_: Optional[SearchFilter] = None,
        ef_search: Optional[int] = None,
    ) -> list[SearchResult]:
        """Vector similarity search."""
        coll = self.get_collection(collection)
        vec = np.asarray(query_vector, dtype=np.float32)

        if vec.shape != (coll.dimension,):
            raise VectorDimensionMismatch(
                f"Query vector dimension {vec.shape[0]} != {coll.dimension}"
            )

        where_clause, filter_params = _filter_to_sql(filter_)

        # Build query with optional filter
        if where_clause:
            # Join with docs table for metadata filtering
            query = f"""
                SELECT v.id, v.embedding, d.text, d.metadata,
                       vec_distance({coll.metric.value}(v.embedding, ?)) as distance
                FROM ghost_{collection}_vec v
                JOIN ghost_{collection}_docs d ON v.id = d.id
                {where_clause}
                ORDER BY distance ASC
                LIMIT ?
            """
            params = [vec.tobytes()] + filter_params + [k]
        else:
            # Pure vector search (fastest)
            query = f"""
                SELECT id, embedding, distance
                FROM ghost_{collection}_vec
                WHERE embedding MATCH ?
                ORDER BY distance ASC
                LIMIT ?
            """
            params = [vec.tobytes(), k]

        cur = self._conn.cursor()
        if ef_search:
            cur.execute(f"PRAGMA vec_ef_search = {ef_search}")

        cur.execute(query, params)
        rows = cur.fetchall()

        results = []
        for rank, row in enumerate(rows):
            if where_clause:
                doc_id, vec_blob, text, metadata, distance = row
            else:
                doc_id, vec_blob, distance = row
                # Fetch document
                cur.execute(f"SELECT text, metadata FROM ghost_{collection}_docs WHERE id = ?", (doc_id,))
                doc_row = cur.fetchone()
                text, metadata = doc_row["text"], doc_row["metadata"]

            vector = _deserialize_vector(vec_blob, coll.dimension)
            # Convert distance to similarity score (0-1)
            if coll.metric == DistanceMetric.COSINE:
                score = 1.0 - distance
            elif coll.metric == DistanceMetric.INNER_PRODUCT:
                score = 1.0 / (1.0 + distance)
            else:  # L2
                score = 1.0 / (1.0 + distance)

            doc = Document(
                id=doc_id,
                collection=collection,
                vector=vector.tolist(),
                text=text,
                metadata=json.loads(metadata),
            )
            results.append(SearchResult(document=doc, score=score, rank=rank + 1))

        return results

    def hybrid_search(
        self,
        collection: str,
        query_vector: np.ndarray,
        query_text: str,
        k: int = 10,
        alpha: float = 0.7,
        filter_: Optional[SearchFilter] = None,
    ) -> list[SearchResult]:
        """Hybrid search: vector + BM25 (FTS5) with RRF fusion."""
        # Vector search
        vec_results = self.search(collection, query_vector, k * 2, filter_)

        # Text search (BM25 via FTS5)
        coll = self.get_collection(collection)
        where_clause, filter_params = _filter_to_sql(filter_)

        cur = self._conn.cursor()
        if where_clause:
            query = f"""
                SELECT doc_id, text, metadata, bm25(ghost_{collection}_fts) as score
                FROM ghost_{collection}_fts
                WHERE ghost_{collection}_fts MATCH ?
                {where_clause}
                ORDER BY score ASC
                LIMIT ?
            """
            params = [query_text] + filter_params + [k * 2]
        else:
            query = f"""
                SELECT doc_id, text, metadata, bm25(ghost_{collection}_fts) as score
                FROM ghost_{collection}_fts
                WHERE ghost_{collection}_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
            """
            params = [query_text, k * 2]

        cur.execute(query, params)
        text_rows = cur.fetchall()

        # RRF fusion
        rrf_k = 60
        fused_scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        # Vector scores
        for rank, result in enumerate(vec_results):
            doc_id = result.document.id
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + alpha / (rrf_k + rank + 1)
            doc_map[doc_id] = result.document

        # Text scores
        for rank, row in enumerate(text_rows):
            doc_id = row["doc_id"]
            if doc_id not in doc_map:
                # Fetch document
                cur.execute(f"""
                    SELECT text, metadata FROM ghost_{collection}_docs WHERE id = ?
                """, (doc_id,))
                d = cur.fetchone()
                if not d:
                    continue
                vec_row = cur.execute(f"""
                    SELECT embedding FROM ghost_{collection}_vec WHERE id = ?
                """, (doc_id,)).fetchone()
                if not vec_row:
                    continue
                vector = _deserialize_vector(vec_row["embedding"], coll.dimension)
                doc_map[doc_id] = Document(
                    id=doc_id, collection=collection, vector=vector.tolist(),
                    text=d["text"], metadata=json.loads(d["metadata"])
                )
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 - alpha) / (rrf_k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            fused_scores.items(), key=lambda x: x[1], reverse=True
        )[:k]

        return [
            SearchResult(document=doc_map[doc_id], score=score, rank=i + 1)
            for i, (doc_id, score) in enumerate(sorted_results)
        ]

    # ─── Maintenance ──────────────────────────────────────────────────

    def compact(self, collection: Optional[str] = None) -> int:
        """Compact database (reclaim space after deletes)."""
        if collection:
            collections = [self.get_collection(collection)]
        else:
            collections = self.list_collections()

        total_reclaimed = 0
        for coll in collections:
            cur = self._conn.cursor()
            cur.execute(f"PRAGMA page_count")
            before = cur.fetchone()[0]
            cur.execute(f"VACUUM ghost_{coll.name}_docs")
            cur.execute(f"VACUUM ghost_{coll.name}_vec")
            cur.execute(f"VACUUM ghost_{coll.name}_fts")
            cur.execute(f"PRAGMA page_count")
            after = cur.fetchone()[0]
            total_reclaimed += (before - after) * 4096  # page size
        return total_reclaimed

    def snapshot(self, path: str) -> None:
        """Create a backup snapshot."""
        import shutil
        shutil.copy2(self.config.path, path)

    def restore(self, path: str) -> None:
        """Restore from snapshot."""
        import shutil
        if self._conn:
            self._conn.close()
        shutil.copy2(path, self.config.path)
        self._init_db()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> GhostClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()