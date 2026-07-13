"""Ghost DB — CLI Commands for JEBAT."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .client import GhostClient, GhostError
from .models import GhostConfig, DistanceMetric, HNSWParams
from .ingest import create_ingestion_pipeline
from .embeddings import get_embedding_provider


def add_ghost_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add Ghost DB commands to CLI."""
    ghost_parser = subparsers.add_parser("ghost", help="Ghost DB vector database")
    ghost_sub = ghost_parser.add_subparsers(dest="ghost_cmd", required=True)

    # ghost init
    init_p = ghost_sub.add_parser("init", help="Create database and collection")
    init_p.add_argument("name", help="Collection name")
    init_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    init_p.add_argument("--dimension", type=int, default=384, help="Vector dimension")
    init_p.add_argument("--metric", choices=["cosine", "l2", "ip"], default="cosine", help="Distance metric")
    init_p.add_argument("--m", type=int, default=16, help="HNSW M parameter")
    init_p.add_argument("--ef-construction", type=int, default=200, help="HNSW ef_construction")
    init_p.add_argument("--ef-search", type=int, default=64, help="HNSW ef_search")
    init_p.set_defaults(func=cmd_init)

    # ghost list
    list_p = ghost_sub.add_parser("list", help="List collections")
    list_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    list_p.set_defaults(func=cmd_list)

    # ghost info
    info_p = ghost_sub.add_parser("info", help="Show collection stats")
    info_p.add_argument("collection", help="Collection name")
    info_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    info_p.set_defaults(func=cmd_info)

    # ghost delete
    del_p = ghost_sub.add_parser("delete", help="Delete a collection")
    del_p.add_argument("collection", help="Collection name")
    del_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    del_p.set_defaults(func=cmd_delete)

    # ghost ingest
    ingest_p = ghost_sub.add_parser("ingest", help="Ingest files from directory")
    ingest_p.add_argument("collection", help="Target collection")
    ingest_p.add_argument("directory", help="Directory to ingest")
    ingest_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    ingest_p.add_argument("--pattern", default="**/*", help="Glob pattern")
    ingest_p.add_argument("--exclude", action="append", help="Exclude patterns")
    ingest_p.add_argument("--chunker", choices=["recursive", "semantic", "markdown", "code", "fixed"], default="recursive")
    ingest_p.add_argument("--provider", choices=["local", "ollama", "openai"], default="local", help="Embedding provider")
    ingest_p.add_argument("--model", help="Embedding model name")
    ingest_p.add_argument("--workers", type=int, default=4, help="Parallel workers")
    ingest_p.add_argument("--quiet", action="store_true", help="Suppress progress output")
    ingest_p.set_defaults(func=cmd_ingest)

    # ghost search
    search_p = ghost_sub.add_parser("search", help="Search for similar documents")
    search_p.add_argument("collection", help="Collection name")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--path", default="./data/ghost.db", help="Database file path")
    search_p.add_argument("--k", type=int, default=5, help="Number of results")
    search_p.add_argument("--provider", choices=["local", "ollama", "openai"], default="local")
    search_p.add_argument("--model", help="Embedding model")
    search_p.set_defaults(func=cmd_search)

    # ghost hybrid
    hybrid_p = ghost_sub.add_parser("hybrid", help="Hybrid vector + text search")
    hybrid_p.add_argument("collection", help="Collection name")
    hybrid_p.add_argument("query", help="Search query")
    hybrid_p.add_argument("--path", default="./data/ghost.db")
    hybrid_p.add_argument("--k", type=int, default=5)
    hybrid_p.add_argument("--alpha", type=float, default=0.7, help="Vector weight (0-1)")
    hybrid_p.add_argument("--provider", choices=["local", "ollama", "openai"], default="local")
    hybrid_p.add_argument("--model", help="Embedding model")
    hybrid_p.set_defaults(func=cmd_hybrid)

    # ghost snapshot
    snap_p = ghost_sub.add_parser("snapshot", help="Create database snapshot")
    snap_p.add_argument("collection", help="Collection name")
    snap_p.add_argument("--path", default="./data/ghost.db")
    snap_p.add_argument("--output", required=True, help="Snapshot output path")
    snap_p.set_defaults(func=cmd_snapshot)

    # ghost compact
    compact_p = ghost_sub.add_parser("compact", help="Compact database")
    compact_p.add_argument("--path", default="./data/ghost.db")
    compact_p.add_argument("--collection", help="Specific collection (optional)")
    compact_p.set_defaults(func=cmd_compact)


def _get_client(args: argparse.Namespace) -> GhostClient:
    """Create GhostClient from args."""
    config = GhostConfig(path=args.path)
    return GhostClient(config)


def cmd_init(args: argparse.Namespace) -> int:
    """Create database and collection."""
    client = _get_client(args)

    try:
        hnsw = HNSWParams(
            m=args.m,
            ef_construction=args.ef_construction,
            ef_search=args.ef_search,
        )
        coll = client.create_collection(
            name=args.name,
            dimension=args.dimension,
            metric=DistanceMetric(args.metric),
            hnsw_params=hnsw,
        )
        print(f"✓ Created collection '{coll.name}' (dim={coll.dimension}, metric={coll.metric.value})")
        return 0
    except GhostError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """List all collections."""
    client = _get_client(args)

    collections = client.list_collections()
    if not collections:
        print("No collections found.")
        return 0

    print(f"{'Name':<30} {'Dim':<6} {'Metric':<8} {'Docs':<8} {'Size':<10}")
    print("-" * 70)
    for c in collections:
        size_mb = c.size_bytes / 1024 / 1024
        print(f"{c.name:<30} {c.dimension:<6} {c.metric.value:<8} {c.document_count:<8} {size_mb:.1f}MB")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show collection statistics."""
    client = _get_client(args)

    try:
        stats = client.collection_stats(args.collection)
        print(f"Collection: {stats.name}")
        print(f"  Dimension: {stats.dimension}")
        print(f"  Metric: {stats.metric.value}")
        print(f"  Documents: {stats.document_count}")
        print(f"  Data size: {stats.size_bytes / 1024 / 1024:.2f} MB")
        print(f"  Index size: {stats.index_size_bytes / 1024 / 1024:.2f} MB")
        print(f"  HNSW params:")
        print(f"    m: {stats.hnsw_params.m}")
        print(f"    ef_construction: {stats.hnsw_params.ef_construction}")
        print(f"    ef_search: {stats.hnsw_params.ef_search}")
        print(f"    max_elements: {stats.hnsw_params.max_elements}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a collection."""
    client = _get_client(args)

    success = client.delete_collection(args.collection)
    if success:
        print(f"✓ Deleted collection '{args.collection}'")
        return 0
    else:
        print(f"✗ Collection '{args.collection}' not found", file=sys.stderr)
        return 1


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest files from directory."""
    from .embeddings import get_embedding_provider
    from .chunkers import get_chunker

    directory = Path(args.directory)
    if not directory.exists():
        print(f"✗ Directory not found: {directory}", file=sys.stderr)
        return 1

    # Create pipeline with custom settings
    config = GhostConfig(path=args.path)
    client = GhostClient(config)

    chunker = get_chunker(
        strategy=args.chunker,
        chunk_size=512,
        chunk_overlap=50,
    )
    embed_provider = get_embedding_provider(args.provider, args.model)

    # Create collection if needed
    try:
        client.get_collection(args.collection)
    except Exception:
        client.create_collection(
            name=args.collection,
            dimension=embed_provider.dimension,
        )

    pipeline = create_ingestion_pipeline(
        collection=args.collection,
        client=client,
    )
    pipeline.chunker = chunker
    pipeline.embed_provider = embed_provider

    result = pipeline.ingest_directory(
        directory=directory,
        pattern=args.pattern,
        exclude_patterns=args.exclude,
        max_workers=args.workers,
        show_progress=not args.quiet,
    )

    print(f"\n✓ Ingestion complete for '{args.collection}':")
    print(f"  Files: {result.success_count}/{len(result.files)}")
    print(f"  Chunks: {result.total_chunks}")
    print(f"  Vectors: {result.total_vectors}")
    print(f"  Latency: {result.total_latency_ms:.0f}ms")

    if result.errors:
        print(f"  Errors: {len(result.errors)}")
        for err in result.errors[:5]:
            print(f"    - {err}")

    return 0 if result.error_count == 0 else 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search for similar documents."""
    from .embeddings import get_embedding_provider
    import numpy as np

    client = _get_client(args)

    provider = get_embedding_provider(args.provider, args.model)
    query_result = provider.embed([args.query])
    query_vector = query_result.vectors[0]

    try:
        results = client.search(
            collection=args.collection,
            query_vector=query_vector,
            k=args.k,
        )

        if not results:
            print("No results found.")
            return 0

        print(f"Found {len(results)} results for '{args.query}':\n")
        for r in results:
            meta = ", ".join(f"{k}={v}" for k, v in r.document.metadata.items() if k not in ["chunk_index", "chunk_count"])
            print(f"  [{r.rank}] Score: {r.score:.4f} | {meta}")
            print(f"      {r.document.text[:300]}...")
            print()

        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_hybrid(args: argparse.Namespace) -> int:
    """Hybrid vector + text search."""
    from .embeddings import get_embedding_provider
    import numpy as np

    client = _get_client(args)

    provider = get_embedding_provider(args.provider, args.model)
    query_result = provider.embed([args.query])
    query_vector = query_result.vectors[0]

    try:
        results = client.hybrid_search(
            collection=args.collection,
            query_vector=query_vector,
            query_text=args.query,
            k=args.k,
            alpha=args.alpha,
        )

        if not results:
            print("No results found.")
            return 0

        print(f"Found {len(results)} hybrid results for '{args.query}' (α={args.alpha}):\n")
        for r in results:
            meta = ", ".join(f"{k}={v}" for k, v in r.document.metadata.items() if k not in ["chunk_index", "chunk_count"])
            print(f"  [{r.rank}] Score: {r.score:.4f} | {meta}")
            print(f"      {r.document.text[:300]}...")
            print()

        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Create database snapshot."""
    client = _get_client(args)

    try:
        client.snapshot(args.output)
        print(f"✓ Snapshot created: {args.output}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cmd_compact(args: argparse.Namespace) -> int:
    """Compact database to reclaim space."""
    client = _get_client(args)

    try:
        reclaimed = client.compact(args.collection)
        print(f"✓ Compacted, reclaimed {reclaimed / 1024 / 1024:.2f} MB")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1