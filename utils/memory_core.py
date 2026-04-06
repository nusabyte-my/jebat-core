"""
Memory Core System
Advanced memory management system for AI agents with persistent storage,
working memory, episodic memory, and semantic memory capabilities.
"""

import asyncio
import json
import logging
import os
import pickle
import sqlite3
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class MemoryType(Enum):
    """Types of memory in the system"""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"


class MemoryPriority(Enum):
    """Memory priority levels"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    TEMPORARY = 5


@dataclass
class MemoryItem:
    """Individual memory item"""

    id: str
    content: Any
    memory_type: MemoryType
    priority: MemoryPriority
    created_at: float
    last_accessed: float
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    decay_factor: float = 1.0
    expiry_time: Optional[float] = None


@dataclass
class MemoryQuery:
    """Memory query parameters"""

    content: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    tags: List[str] = field(default_factory=list)
    time_range: Optional[Tuple[float, float]] = None
    priority: Optional[MemoryPriority] = None
    similarity_threshold: float = 0.7
    limit: int = 10


class MemoryCore:
    """
    Advanced memory management system for AI agents.

    Features:
    - Multiple memory types (working, episodic, semantic, procedural, emotional)
    - Persistent storage with SQLite
    - Memory consolidation and forgetting mechanisms
    - Semantic search with embeddings
    - Memory decay and cleanup
    - Context-aware retrieval
    """

    def __init__(
        self,
        agent_id: str,
        memory_dir: str = "./memory",
        max_working_memory: int = 1000,
        max_episodic_memory: int = 10000,
        max_semantic_memory: int = 5000,
        consolidation_threshold: float = 0.8,
        decay_rate: float = 0.1,
        cleanup_interval: int = 3600,  # seconds
    ):
        """
        Initialize the Memory Core.

        Args:
            agent_id: Unique identifier for the agent
            memory_dir: Directory for persistent storage
            max_working_memory: Maximum items in working memory
            max_episodic_memory: Maximum items in episodic memory
            max_semantic_memory: Maximum items in semantic memory
            consolidation_threshold: Threshold for memory consolidation
            decay_rate: Rate of memory decay
            cleanup_interval: Interval for memory cleanup in seconds
        """
        self.agent_id = agent_id
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Memory limits
        self.max_working_memory = max_working_memory
        self.max_episodic_memory = max_episodic_memory
        self.max_semantic_memory = max_semantic_memory

        # Memory management parameters
        self.consolidation_threshold = consolidation_threshold
        self.decay_rate = decay_rate
        self.cleanup_interval = cleanup_interval

        # Memory stores
        self.working_memory: deque = deque(maxlen=max_working_memory)
        self.episodic_memory: Dict[str, MemoryItem] = {}
        self.semantic_memory: Dict[str, MemoryItem] = {}
        self.procedural_memory: Dict[str, MemoryItem] = {}
        self.emotional_memory: Dict[str, MemoryItem] = {}

        # Memory indexes for fast retrieval
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.time_index: List[Tuple[float, str]] = []
        self.priority_index: Dict[MemoryPriority, List[str]] = defaultdict(list)

        # Context and associations
        self.context_stack: List[str] = []
        self.associations: Dict[str, List[str]] = defaultdict(list)

        # Initialize database
        self.db_path = self.memory_dir / f"{agent_id}_memory.db"
        self._init_database()

        # Load persistent memories
        self._load_persistent_memories()

        # Setup logging
        self.logger = self._setup_logging()

        # Background tasks
        self.cleanup_task = None
        self.consolidation_task = None

        # Statistics
        self.stats = {
            "memories_created": 0,
            "memories_retrieved": 0,
            "memories_consolidated": 0,
            "memories_forgotten": 0,
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for memory core"""
        logger = logging.getLogger(f"memory_core_{self.agent_id}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"[MemoryCore-{self.agent_id}] %(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # File handler
            file_handler = logging.FileHandler(
                self.memory_dir / f"{self.agent_id}_memory.log"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT,
                    metadata TEXT,
                    embeddings BLOB,
                    decay_factor REAL DEFAULT 1.0,
                    expiry_time REAL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority ON memories(priority)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS associations (
                    memory_id TEXT,
                    associated_id TEXT,
                    strength REAL DEFAULT 1.0,
                    created_at REAL DEFAULT (julianday('now')),
                    PRIMARY KEY (memory_id, associated_id)
                )
            """)

    def _load_persistent_memories(self):
        """Load memories from persistent storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, content, memory_type, priority, created_at,
                           last_accessed, access_count, tags, metadata,
                           embeddings, decay_factor, expiry_time
                    FROM memories
                    WHERE expiry_time IS NULL OR expiry_time > ?
                """,
                    (time.time(),),
                )

                for row in cursor.fetchall():
                    memory_item = MemoryItem(
                        id=row[0],
                        content=json.loads(row[1]),
                        memory_type=MemoryType(row[2]),
                        priority=MemoryPriority(row[3]),
                        created_at=row[4],
                        last_accessed=row[5],
                        access_count=row[6],
                        tags=json.loads(row[7]) if row[7] else [],
                        metadata=json.loads(row[8]) if row[8] else {},
                        embeddings=pickle.loads(row[9]) if row[9] else None,
                        decay_factor=row[10],
                        expiry_time=row[11],
                    )

                    # Place in appropriate memory store
                    if memory_item.memory_type == MemoryType.EPISODIC:
                        self.episodic_memory[memory_item.id] = memory_item
                    elif memory_item.memory_type == MemoryType.SEMANTIC:
                        self.semantic_memory[memory_item.id] = memory_item
                    elif memory_item.memory_type == MemoryType.PROCEDURAL:
                        self.procedural_memory[memory_item.id] = memory_item
                    elif memory_item.memory_type == MemoryType.EMOTIONAL:
                        self.emotional_memory[memory_item.id] = memory_item

                    # Update indexes
                    self._update_indexes(memory_item)

                # Load associations
                cursor = conn.execute(
                    "SELECT memory_id, associated_id, strength FROM associations"
                )
                for memory_id, associated_id, strength in cursor.fetchall():
                    self.associations[memory_id].append(associated_id)

            self.logger.info(
                f"Loaded {len(self.episodic_memory)} episodic, "
                f"{len(self.semantic_memory)} semantic, "
                f"{len(self.procedural_memory)} procedural, "
                f"{len(self.emotional_memory)} emotional memories"
            )

        except Exception as e:
            self.logger.error(f"Failed to load persistent memories: {e}")

    async def store_memory(
        self,
        content: Any,
        memory_type: MemoryType,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        context: str = None,
        expiry_hours: Optional[float] = None,
    ) -> str:
        """
        Store a new memory item.

        Args:
            content: The content to store
            memory_type: Type of memory
            priority: Priority level
            tags: Associated tags
            metadata: Additional metadata
            context: Current context
            expiry_hours: Hours until expiry (None for permanent)

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        current_time = time.time()

        # Calculate expiry time
        expiry_time = None
        if expiry_hours:
            expiry_time = current_time + (expiry_hours * 3600)

        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            created_at=current_time,
            last_accessed=current_time,
            tags=tags or [],
            metadata=metadata or {},
            expiry_time=expiry_time,
        )

        # Generate embeddings for semantic search (simplified)
        if isinstance(content, str):
            memory_item.embeddings = self._generate_embeddings(content)

        # Store in appropriate memory
        if memory_type == MemoryType.WORKING:
            self.working_memory.append(memory_item)
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory[memory_id] = memory_item
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic_memory[memory_id] = memory_item
        elif memory_type == MemoryType.PROCEDURAL:
            self.procedural_memory[memory_id] = memory_item
        elif memory_type == MemoryType.EMOTIONAL:
            self.emotional_memory[memory_id] = memory_item

        # Update indexes
        self._update_indexes(memory_item)

        # Create context associations
        if context and self.context_stack:
            for ctx_memory_id in self.context_stack[-3:]:  # Last 3 context items
                self.associations[memory_id].append(ctx_memory_id)

        # Store context
        if context:
            self.context_stack.append(memory_id)
            if len(self.context_stack) > 10:  # Keep last 10 contexts
                self.context_stack.pop(0)

        # Persist to database (except working memory)
        if memory_type != MemoryType.WORKING:
            await self._persist_memory(memory_item)

        # Check memory limits and consolidate if needed
        await self._check_memory_limits()

        self.stats["memories_created"] += 1
        self.logger.debug(f"Stored {memory_type.value} memory: {memory_id}")

        return memory_id

    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Retrieve memories based on query parameters.

        Args:
            query: Memory query specification

        Returns:
            List of matching memory items
        """
        candidates = []
        current_time = time.time()

        # Collect candidates from appropriate memory stores
        if query.memory_type:
            if query.memory_type == MemoryType.WORKING:
                candidates.extend(self.working_memory)
            elif query.memory_type == MemoryType.EPISODIC:
                candidates.extend(self.episodic_memory.values())
            elif query.memory_type == MemoryType.SEMANTIC:
                candidates.extend(self.semantic_memory.values())
            elif query.memory_type == MemoryType.PROCEDURAL:
                candidates.extend(self.procedural_memory.values())
            elif query.memory_type == MemoryType.EMOTIONAL:
                candidates.extend(self.emotional_memory.values())
        else:
            # Search all memory stores
            candidates.extend(self.working_memory)
            candidates.extend(self.episodic_memory.values())
            candidates.extend(self.semantic_memory.values())
            candidates.extend(self.procedural_memory.values())
            candidates.extend(self.emotional_memory.values())

        # Filter candidates
        filtered_memories = []
        for memory in candidates:
            # Check expiry
            if memory.expiry_time and memory.expiry_time <= current_time:
                continue

            # Check priority
            if query.priority and memory.priority != query.priority:
                continue

            # Check time range
            if query.time_range:
                start_time, end_time = query.time_range
                if not (start_time <= memory.created_at <= end_time):
                    continue

            # Check tags
            if query.tags:
                if not any(tag in memory.tags for tag in query.tags):
                    continue

            # Content similarity (simplified)
            if query.content and isinstance(memory.content, str):
                similarity = self._calculate_similarity(query.content, memory.content)
                if similarity < query.similarity_threshold:
                    continue
                memory.metadata["similarity_score"] = similarity

            filtered_memories.append(memory)

        # Sort by relevance (priority, recency, access count)
        filtered_memories.sort(
            key=lambda m: (
                -m.priority.value,  # Higher priority first
                -m.last_accessed,  # More recent first
                -m.access_count,  # More accessed first
            )
        )

        # Update access information
        for memory in filtered_memories[: query.limit]:
            memory.last_accessed = current_time
            memory.access_count += 1

        # Update database
        for memory in filtered_memories[: query.limit]:
            if memory.memory_type != MemoryType.WORKING:
                await self._update_memory_access(memory.id, current_time)

        self.stats["memories_retrieved"] += len(filtered_memories[: query.limit])

        return filtered_memories[: query.limit]

    async def forget_memory(self, memory_id: str) -> bool:
        """
        Remove a memory from the system.

        Args:
            memory_id: ID of memory to forget

        Returns:
            True if memory was found and removed
        """
        # Find and remove from appropriate store
        memory_found = False

        # Check working memory
        for i, memory in enumerate(self.working_memory):
            if memory.id == memory_id:
                del self.working_memory[i]
                memory_found = True
                break

        # Check other memory stores
        for memory_store in [
            self.episodic_memory,
            self.semantic_memory,
            self.procedural_memory,
            self.emotional_memory,
        ]:
            if memory_id in memory_store:
                del memory_store[memory_id]
                memory_found = True
                break

        if memory_found:
            # Remove from indexes
            self._remove_from_indexes(memory_id)

            # Remove associations
            del self.associations[memory_id]
            for associated_list in self.associations.values():
                if memory_id in associated_list:
                    associated_list.remove(memory_id)

            # Remove from database
            await self._delete_from_database(memory_id)

            self.stats["memories_forgotten"] += 1
            self.logger.debug(f"Forgot memory: {memory_id}")

        return memory_found

    async def consolidate_memories(self):
        """
        Consolidate memories by identifying patterns and creating higher-level memories.
        """
        try:
            consolidated_count = 0

            # Group episodic memories by similar content/tags
            episodic_groups = self._group_similar_memories(
                list(self.episodic_memory.values())
            )

            for group in episodic_groups:
                if len(group) >= 3 and self._should_consolidate(group):
                    # Create consolidated semantic memory
                    consolidated_content = self._create_consolidated_content(group)

                    await self.store_memory(
                        content=consolidated_content,
                        memory_type=MemoryType.SEMANTIC,
                        priority=MemoryPriority.HIGH,
                        tags=self._merge_tags([m.tags for m in group]),
                        metadata={
                            "consolidated_from": [m.id for m in group],
                            "consolidation_time": time.time(),
                        },
                    )

                    # Reduce priority of original memories
                    for memory in group:
                        if memory.priority.value > MemoryPriority.LOW.value:
                            memory.priority = MemoryPriority(memory.priority.value + 1)

                    consolidated_count += 1

            self.stats["memories_consolidated"] += consolidated_count
            self.logger.info(f"Consolidated {consolidated_count} memory groups")

        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")

    async def cleanup_expired_memories(self):
        """Remove expired memories and apply decay."""
        try:
            current_time = time.time()
            expired_count = 0
            decayed_count = 0

            # Check all memory stores for expired memories
            for memory_store in [
                self.episodic_memory,
                self.semantic_memory,
                self.procedural_memory,
                self.emotional_memory,
            ]:
                expired_ids = []
                for memory_id, memory in memory_store.items():
                    # Check expiry
                    if memory.expiry_time and memory.expiry_time <= current_time:
                        expired_ids.append(memory_id)
                        continue

                    # Apply decay
                    time_since_access = current_time - memory.last_accessed
                    if time_since_access > 86400:  # 1 day
                        decay = self.decay_rate * (time_since_access / 86400)
                        memory.decay_factor = max(0.1, memory.decay_factor - decay)
                        decayed_count += 1

                # Remove expired memories
                for memory_id in expired_ids:
                    await self.forget_memory(memory_id)
                    expired_count += 1

            # Clean working memory (remove old items if full)
            if len(self.working_memory) == self.working_memory.maxlen:
                # Remove oldest 10% if memory is full
                remove_count = max(1, len(self.working_memory) // 10)
                for _ in range(remove_count):
                    if self.working_memory:
                        self.working_memory.popleft()

            self.logger.info(
                f"Cleaned up {expired_count} expired memories, "
                f"applied decay to {decayed_count} memories"
            )

        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        current_time = time.time()

        return {
            "agent_id": self.agent_id,
            "timestamp": current_time,
            "memory_counts": {
                "working": len(self.working_memory),
                "episodic": len(self.episodic_memory),
                "semantic": len(self.semantic_memory),
                "procedural": len(self.procedural_memory),
                "emotional": len(self.emotional_memory),
                "total": (
                    len(self.working_memory)
                    + len(self.episodic_memory)
                    + len(self.semantic_memory)
                    + len(self.procedural_memory)
                    + len(self.emotional_memory)
                ),
            },
            "memory_limits": {
                "working": self.max_working_memory,
                "episodic": self.max_episodic_memory,
                "semantic": self.max_semantic_memory,
            },
            "utilization": {
                "working": len(self.working_memory) / self.max_working_memory * 100,
                "episodic": len(self.episodic_memory) / self.max_episodic_memory * 100,
                "semantic": len(self.semantic_memory) / self.max_semantic_memory * 100,
            },
            "activity_stats": self.stats.copy(),
            "context_depth": len(self.context_stack),
            "associations_count": sum(
                len(assocs) for assocs in self.associations.values()
            ),
            "indexes": {
                "tags": len(self.tag_index),
                "time_entries": len(self.time_index),
                "priority_entries": sum(
                    len(entries) for entries in self.priority_index.values()
                ),
            },
        }

    # Helper methods
    def _update_indexes(self, memory: MemoryItem):
        """Update memory indexes for fast retrieval."""
        # Tag index
        for tag in memory.tags:
            self.tag_index[tag].append(memory.id)

        # Time index
        self.time_index.append((memory.created_at, memory.id))
        self.time_index.sort()

        # Priority index
        self.priority_index[memory.priority].append(memory.id)

    def _remove_from_indexes(self, memory_id: str):
        """Remove memory from all indexes."""
        # Tag index
        for tag_list in self.tag_index.values():
            if memory_id in tag_list:
                tag_list.remove(memory_id)

        # Time index
        self.time_index = [(t, mid) for t, mid in self.time_index if mid != memory_id]

        # Priority index
        for priority_list in self.priority_index.values():
            if memory_id in priority_list:
                priority_list.remove(memory_id)

    def _generate_embeddings(self, text: str) -> np.ndarray:
        """Generate simple embeddings for semantic search (placeholder)."""
        # This is a simplified implementation
        # In practice, you'd use a proper embedding model like sentence-transformers
        words = text.lower().split()
        # Create a simple bag-of-words vector (first 100 most common words)
        vector = np.zeros(100)
        for i, word in enumerate(words[:100]):
            vector[i] = hash(word) % 1000 / 1000.0
        return vector

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings (simplified)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _group_similar_memories(
        self, memories: List[MemoryItem]
    ) -> List[List[MemoryItem]]:
        """Group similar memories for consolidation."""
        groups = []
        used = set()

        for i, memory in enumerate(memories):
            if memory.id in used:
                continue

            group = [memory]
            used.add(memory.id)

            for j, other in enumerate(memories[i + 1 :], i + 1):
                if other.id in used:
                    continue

                # Check similarity based on tags and content
                tag_overlap = len(set(memory.tags).intersection(set(other.tags)))
                time_diff = abs(memory.created_at - other.created_at)

                if tag_overlap >= 2 or (
                    isinstance(memory.content, str)
                    and isinstance(other.content, str)
                    and self._calculate_similarity(memory.content, other.content) > 0.6
                ):
                    group.append(other)
                    used.add(other.id)

            if len(group) > 1:
                groups.append(group)

        return groups

    def _should_consolidate(self, memories: List[MemoryItem]) -> bool:
        """Determine if a group of memories should be consolidated."""
        # Check access patterns, age, and importance
        avg_access = sum(m.access_count for m in memories) / len(memories)
        avg_age = (
            time.time() - sum(m.created_at for m in memories) / len(memories)
        ) / 86400  # days

        return (
            avg_access >= 2 and avg_age >= 1
        )  # Accessed at least twice and older than 1 day

    def _create_consolidated_content(self, memories: List[MemoryItem]) -> str:
        """Create consolidated content from a group of memories."""
        contents = []
        for memory in memories:
            if isinstance(memory.content, str):
                contents.append(memory.content)
            else:
                contents.append(str(memory.content))

        return f"Consolidated pattern from {len(memories)} experiences: " + "; ".join(
            contents
        )

    def _merge_tags(self, tag_lists: List[List[str]]) -> List[str]:
        """Merge tags from multiple memories."""
        all_tags = set()
        for tags in tag_lists:
            all_tags.update(tags)
        return list(all_tags)

    async def _persist_memory(self, memory: MemoryItem):
        """Persist memory to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO memories
                    (id, content, memory_type, priority, created_at, last_accessed,
                     access_count, tags, metadata, embeddings, decay_factor, expiry_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        memory.id,
                        json.dumps(memory.content),
                        memory.memory_type.value,
                        memory.priority.value,
                        memory.created_at,
                        memory.last_accessed,
                        memory.access_count,
                        json.dumps(memory.tags),
                        json.dumps(memory.metadata),
                        pickle.dumps(memory.embeddings)
                        if memory.embeddings is not None
                        else None,
                        memory.decay_factor,
                        memory.expiry_time,
                    ),
                )

                # Store associations
                for associated_id in self.associations[memory.id]:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO associations (memory_id, associated_id, strength, created_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (memory.id, associated_id, 1.0, time.time()),
                    )

        except Exception as e:
            self.logger.error(f"Failed to persist memory {memory.id}: {e}")

    async def _update_memory_access(self, memory_id: str, access_time: float):
        """Update memory access information in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE memories
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id = ?
                """,
                    (access_time, memory_id),
                )
        except Exception as e:
            self.logger.error(f"Failed to update memory access {memory_id}: {e}")

    async def _delete_from_database(self, memory_id: str):
        """Delete memory from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                conn.execute(
                    "DELETE FROM associations WHERE memory_id = ? OR associated_id = ?",
                    (memory_id, memory_id),
                )
        except Exception as e:
            self.logger.error(f"Failed to delete memory {memory_id} from database: {e}")

    async def _check_memory_limits(self):
        """Check and enforce memory limits."""
        # Episodic memory limit
        if len(self.episodic_memory) > self.max_episodic_memory:
            # Remove oldest, least accessed memories
            to_remove = len(self.episodic_memory) - self.max_episodic_memory
            candidates = sorted(
                self.episodic_memory.values(),
                key=lambda m: (m.priority.value, -m.access_count, m.created_at),
            )

            for memory in candidates[:to_remove]:
                await self.forget_memory(memory.id)

        # Semantic memory limit
        if len(self.semantic_memory) > self.max_semantic_memory:
            to_remove = len(self.semantic_memory) - self.max_semantic_memory
            candidates = sorted(
                self.semantic_memory.values(),
                key=lambda m: (m.priority.value, -m.access_count, m.created_at),
            )

            for memory in candidates[:to_remove]:
                await self.forget_memory(memory.id)

    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        self.cleanup_task = asyncio.create_task(self._background_cleanup())
        self.consolidation_task = asyncio.create_task(self._background_consolidation())
        self.logger.info("Started background memory maintenance tasks")

    async def stop_background_tasks(self):
        """Stop background maintenance tasks."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.consolidation_task:
            self.consolidation_task.cancel()
        self.logger.info("Stopped background memory maintenance tasks")

    async def _background_cleanup(self):
        """Background task for periodic memory cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Background cleanup error: {e}")

    async def _background_consolidation(self):
        """Background task for periodic memory consolidation."""
        while True:
            try:
                # Run consolidation every 4 hours
                await asyncio.sleep(4 * 3600)
                await self.consolidate_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Background consolidation error: {e}")

    async def export_memories(
        self, file_path: str, memory_types: List[MemoryType] = None
    ):
        """
        Export memories to a file for backup or analysis.

        Args:
            file_path: Path to export file
            memory_types: Types of memories to export (None for all)
        """
        export_data = {
            "agent_id": self.agent_id,
            "export_timestamp": time.time(),
            "memories": [],
            "associations": dict(self.associations),
            "stats": self.stats.copy(),
        }

        # Collect memories to export
        memory_stores = []
        if not memory_types:
            memory_types = list(MemoryType)

        for memory_type in memory_types:
            if memory_type == MemoryType.WORKING:
                memory_stores.extend(self.working_memory)
            elif memory_type == MemoryType.EPISODIC:
                memory_stores.extend(self.episodic_memory.values())
            elif memory_type == MemoryType.SEMANTIC:
                memory_stores.extend(self.semantic_memory.values())
            elif memory_type == MemoryType.PROCEDURAL:
                memory_stores.extend(self.procedural_memory.values())
            elif memory_type == MemoryType.EMOTIONAL:
                memory_stores.extend(self.emotional_memory.values())

        # Convert memories to exportable format
        for memory in memory_stores:
            memory_data = {
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type.value,
                "priority": memory.priority.value,
                "created_at": memory.created_at,
                "last_accessed": memory.last_accessed,
                "access_count": memory.access_count,
                "tags": memory.tags,
                "metadata": memory.metadata,
                "decay_factor": memory.decay_factor,
                "expiry_time": memory.expiry_time,
            }
            export_data["memories"].append(memory_data)

        # Write to file
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        self.logger.info(
            f"Exported {len(export_data['memories'])} memories to {file_path}"
        )

    async def import_memories(self, file_path: str, overwrite: bool = False):
        """
        Import memories from a file.

        Args:
            file_path: Path to import file
            overwrite: Whether to overwrite existing memories with same ID
        """
        try:
            with open(file_path, "r") as f:
                import_data = json.load(f)

            imported_count = 0
            skipped_count = 0

            for memory_data in import_data.get("memories", []):
                memory_id = memory_data["id"]

                # Check if memory already exists
                existing_memory = None
                for store in [
                    self.episodic_memory,
                    self.semantic_memory,
                    self.procedural_memory,
                    self.emotional_memory,
                ]:
                    if memory_id in store:
                        existing_memory = store[memory_id]
                        break

                if existing_memory and not overwrite:
                    skipped_count += 1
                    continue

                # Create memory item
                memory = MemoryItem(
                    id=memory_id,
                    content=memory_data["content"],
                    memory_type=MemoryType(memory_data["memory_type"]),
                    priority=MemoryPriority(memory_data["priority"]),
                    created_at=memory_data["created_at"],
                    last_accessed=memory_data["last_accessed"],
                    access_count=memory_data["access_count"],
                    tags=memory_data["tags"],
                    metadata=memory_data["metadata"],
                    decay_factor=memory_data.get("decay_factor", 1.0),
                    expiry_time=memory_data.get("expiry_time"),
                )

                # Store in appropriate memory
                if memory.memory_type == MemoryType.EPISODIC:
                    self.episodic_memory[memory_id] = memory
                elif memory.memory_type == MemoryType.SEMANTIC:
                    self.semantic_memory[memory_id] = memory
                elif memory.memory_type == MemoryType.PROCEDURAL:
                    self.procedural_memory[memory_id] = memory
                elif memory.memory_type == MemoryType.EMOTIONAL:
                    self.emotional_memory[memory_id] = memory

                # Update indexes
                self._update_indexes(memory)

                # Persist to database
                await self._persist_memory(memory)

                imported_count += 1

            # Import associations
            associations = import_data.get("associations", {})
            for memory_id, associated_ids in associations.items():
                self.associations[memory_id].extend(associated_ids)

            self.logger.info(
                f"Imported {imported_count} memories, skipped {skipped_count}"
            )

        except Exception as e:
            self.logger.error(f"Failed to import memories: {e}")
            raise

    def __del__(self):
        """Cleanup when memory core is destroyed."""
        try:
            if hasattr(self, "cleanup_task") and self.cleanup_task:
                self.cleanup_task.cancel()
            if hasattr(self, "consolidation_task") and self.consolidation_task:
                self.consolidation_task.cancel()
        except:
            pass
