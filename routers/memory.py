"""6-type eternal memory system (Working, Episodic, Semantic, Procedural, Relational, Vector) with Ghost DB vector search endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jebat.core.memory.layers import MemoryLayer, MemoryMetadata
from jebat.core.memory.manager import MemoryManager

router = APIRouter(prefix="/api/memory", tags=["memory"])

_manager = MemoryManager()


class MemoryStoreRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Memory content to store")
    layer: str = Field(default="M1_EPISODIC", description="Memory layer: M0_SENSORY, M1_EPISODIC, M2_SEMANTIC, M3_CONCEPTUAL, M4_PERMANENT")
    user_id: str = Field(default="default", description="User ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class MemoryRetrieveRequest(BaseModel):
    query: str = Field(default="", description="Search query (filters by user_id)")
    layer: Optional[str] = Field(default=None, description="Restrict to a specific layer")
    user_id: str = Field(default="default", description="User ID")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search term to match against memory content")
    user_id: str = Field(default="default", description="User ID")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


@router.post("/store")
async def store_memory(req: MemoryStoreRequest) -> Dict[str, Any]:
    """Store a memory entry in the specified layer."""
    layer_map = {l.value: l for l in MemoryLayer}
    layer = layer_map.get(req.layer, MemoryLayer.M1_EPISODIC)
    metadata = MemoryMetadata(
        user_id=req.user_id,
        source=req.metadata.get("source"),
        tags=req.metadata.get("tags", []),
        context=req.metadata,
    )
    memory_id = await _manager.store(
        content=req.content,
        layer=layer,
        user_id=req.user_id,
        metadata=metadata,
    )
    return {"memory_id": memory_id, "layer": layer.value, "user_id": req.user_id}


@router.post("/retrieve")
async def retrieve_memories(req: MemoryRetrieveRequest) -> Dict[str, Any]:
    """Retrieve memories filtered by layer and user."""
    layer = None
    if req.layer:
        layer_map = {l.value: l for l in MemoryLayer}
        layer = layer_map.get(req.layer)
    memories = await _manager.asearch(
        query=req.query, layer=layer, user_id=req.user_id, limit=req.limit
    )
    return {"memories": [memory.to_dict() for memory in memories], "total": len(memories)}


@router.post("/search")
async def search_memories(req: MemorySearchRequest) -> Dict[str, Any]:
    """Full-text search across all memory layers."""
    results = await _manager.asearch(
        query=req.query, user_id=req.user_id, limit=req.limit
    )
    return {"results": [memory.to_dict() for memory in results], "total": len(results)}


@router.get("/profile/{user_id}")
async def user_profile(user_id: str) -> Dict[str, Any]:
    """Get a user's memory profile."""
    memories = _manager.search(query="", user_id=user_id, limit=100)
    return {
        "user_id": user_id,
        "memory_count": len(memories),
        "by_layer": {
            layer.value: len([memory for memory in memories if memory.layer is layer])
            for layer in MemoryLayer
        },
    }


@router.get("/stats")
async def memory_stats() -> Dict[str, Any]:
    """Memory layer statistics (entry counts per layer)."""
    return _manager.get_stats()


@router.get("/layers")
async def memory_layers() -> Dict[str, Any]:
    """List available memory layers."""
    return {
        "layers": [
            {"value": l.value, "description": l.value.replace("_", " ").title()}
            for l in MemoryLayer
        ]
    }
