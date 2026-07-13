"""Ghost DB — MCP Server for IDE Integration."""

from __future__ import annotations

import json
import asyncio
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
except ImportError:
    Server = InitializationOptions = stdio_server = Tool = TextContent = (
        ImageContent
    ) = EmbeddedResource = None

from .client import GhostClient, GhostError
from .models import GhostConfig, DistanceMetric
from .embeddings import get_embedding_provider


class GhostMCPServer:
    """MCP server exposing Ghost DB operations."""

    def __init__(self, config: GhostConfig | None = None):
        self.config = config or GhostConfig()
        self.client = GhostClient(self.config)
        self.server = Server("ghost-db")

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="ghost_list_collections",
                    description="List all vector collections",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="ghost_create_collection",
                    description="Create a new vector collection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Collection name"},
                            "dimension": {"type": "integer", "default": 384, "description": "Vector dimension"},
                            "metric": {"type": "string", "enum": ["cosine", "l2", "ip"], "default": "cosine"},
                            "m": {"type": "integer", "default": 16},
                            "ef_construction": {"type": "integer", "default": 200},
                            "ef_search": {"type": "integer", "default": 64},
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="ghost_delete_collection",
                    description="Delete a collection",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="ghost_collection_info",
                    description="Get collection statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="ghost_insert",
                    description="Insert documents into a collection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "documents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "metadata": {"type": "object", "default": {}},
                                        "id": {"type": "string"},
                                    },
                                    "required": ["text"],
                                },
                            },
                        },
                        "required": ["collection", "documents"],
                    },
                ),
                Tool(
                    name="ghost_search",
                    description="Vector similarity search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "query": {"type": "string"},
                            "k": {"type": "integer", "default": 5},
                            "provider": {"type": "string", "enum": ["local", "ollama", "openai"], "default": "local"},
                            "model": {"type": "string"},
                        },
                        "required": ["collection", "query"],
                    },
                ),
                Tool(
                    name="ghost_hybrid_search",
                    description="Hybrid vector + BM25 search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "query": {"type": "string"},
                            "k": {"type": "integer", "default": 5},
                            "alpha": {"type": "number", "default": 0.7},
                            "provider": {"type": "string", "enum": ["local", "ollama", "openai"], "default": "local"},
                            "model": {"type": "string"},
                        },
                        "required": ["collection", "query"],
                    },
                ),
                Tool(
                    name="ghost_ingest_file",
                    description="Ingest a single file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "path": {"type": "string"},
                            "chunker": {"type": "string", "enum": ["recursive", "semantic", "markdown", "code", "fixed"], "default": "recursive"},
                            "provider": {"type": "string", "enum": ["local", "ollama", "openai"], "default": "local"},
                            "model": {"type": "string"},
                        },
                        "required": ["collection", "path"],
                    },
                ),
                Tool(
                    name="ghost_ingest_directory",
                    description="Ingest all files in a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "directory": {"type": "string"},
                            "pattern": {"type": "string", "default": "**/*"},
                            "chunker": {"type": "string", "enum": ["recursive", "semantic", "markdown", "code", "fixed"], "default": "recursive"},
                            "provider": {"type": "string", "enum": ["local", "ollama", "openai"], "default": "local"},
                            "model": {"type": "string"},
                            "workers": {"type": "integer", "default": 4},
                        },
                        "required": ["collection", "directory"],
                    },
                ),
                Tool(
                    name="ghost_snapshot",
                    description="Create backup snapshot",
                    inputSchema={
                        "type": "object",
                        "properties": {"output": {"type": "string"}},
                        "required": ["output"],
                    },
                ),
                Tool(
                    name="ghost_compact",
                    description="Compact database to reclaim space",
                    inputSchema={"type": "object", "properties": {"collection": {"type": "string"}}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent | EmbeddedResource]:
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    async def _execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return result."""

        if name == "ghost_list_collections":
            collections = self.client.list_collections()
            return {
                "collections": [
                    {"name": c.name, "dimension": c.dimension, "metric": c.metric.value, "count": c.document_count}
                    for c in collections
                ]
            }

        elif name == "ghost_create_collection":
            metric = DistanceMetric(args.get("metric", "cosine"))
            coll = self.client.create_collection(
                name=args["name"],
                dimension=args.get("dimension", 384),
                metric=metric,
                hnsw_params={
                    "m": args.get("m", 16),
                    "ef_construction": args.get("ef_construction", 200),
                    "ef_search": args.get("ef_search", 64),
                },
            )
            return {"created": True, "collection": coll.name, "dimension": coll.dimension}

        elif name == "ghost_delete_collection":
            success = self.client.delete_collection(args["name"])
            return {"deleted": success}

        elif name == "ghost_collection_info":
            stats = self.client.collection_stats(args["name"])
            return {
                "name": stats.name,
                "dimension": stats.dimension,
                "metric": stats.metric.value,
                "document_count": stats.document_count,
                "size_mb": stats.size_bytes / 1024 / 1024,
                "index_size_mb": stats.index_size_bytes / 1024 / 1024,
            }

        elif name == "ghost_insert":
            # Need embedding provider
            provider_name = args.get("provider", "local")
            model = args.get("model")
            embed_provider = get_embedding_provider(provider_name, model)

            # Embed all texts
            texts = [d["text"] for d in args["documents"]]
            embed_result = embed_provider.embed(texts)

            documents = []
            for i, doc in enumerate(args["documents"]):
                if i >= len(embed_result.vectors):
                    break
                documents.append({
                    "collection": args["collection"],
                    "vector": embed_result.vectors[i].tolist(),
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {}),
                })

            self.client.insert_batch(args["collection"], documents)
            return {"inserted": len(documents)}

        elif name == "ghost_search":
            provider = get_embedding_provider(args.get("provider", "local"), args.get("model"))
            query_result = provider.embed([args["query"]])
            query_vector = query_result.vectors[0]

            results = self.client.search(
                collection=args["collection"],
                query_vector=query_vector,
                k=args.get("k", 5),
            )

            return {
                "results": [
                    {
                        "rank": r.rank,
                        "score": r.score,
                        "text": r.document.text,
                        "metadata": r.document.metadata,
                    }
                    for r in results
                ]
            }

        elif name == "ghost_hybrid_search":
            provider = get_embedding_provider(args.get("provider", "local"), args.get("model"))
            query_result = provider.embed([args["query"]])
            query_vector = query_result.vectors[0]

            results = self.client.hybrid_search(
                collection=args["collection"],
                query_vector=query_vector,
                query_text=args["query"],
                k=args.get("k", 5),
                alpha=args.get("alpha", 0.7),
            )

            return {
                "results": [
                    {
                        "rank": r.rank,
                        "score": r.score,
                        "text": r.document.text,
                        "metadata": r.document.metadata,
                    }
                    for r in results
                ]
            }

        elif name == "ghost_ingest_file":
            from pathlib import Path
            from .ingest import create_ingestion_pipeline

            pipeline = create_ingestion_pipeline(
                collection=args["collection"],
                config=self.config,
                client=self.client,
            )
            result = pipeline.ingest_file(
                Path(args["path"]),
                base_metadata=None,
            )
            return {
                "path": result.path,
                "chunks": result.chunks_created,
                "vectors": result.vectors_indexed,
                "latency_ms": result.latency_ms,
                "error": result.error,
            }

        elif name == "ghost_ingest_directory":
            from pathlib import Path
            from .ingest import create_ingestion_pipeline

            pipeline = create_ingestion_pipeline(
                collection=args["collection"],
                config=self.config,
                client=self.client,
            )
            result = pipeline.ingest_directory(
                Path(args["directory"]),
                pattern=args.get("pattern", "**/*"),
                recursive=True,
                base_metadata=None,
                max_workers=args.get("workers", 4),
            )
            return {
                "files_processed": len(result.files),
                "total_chunks": result.total_chunks,
                "total_vectors": result.total_vectors,
                "latency_ms": result.total_latency_ms,
                "errors": result.errors,
            }

        elif name == "ghost_snapshot":
            self.client.snapshot(args["output"])
            return {"snapshot": args["output"], "success": True}

        elif name == "ghost_compact":
            reclaimed = self.client.compact(args.get("collection"))
            return {"reclaimed_mb": reclaimed / 1024 / 1024}

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ghost-db",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Entry point for MCP server."""
    config = GhostConfig()
    server = GhostMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())