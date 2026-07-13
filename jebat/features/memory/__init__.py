"""
Enhanced Memory System with Self-Learning - JEBAT's Long-term Memory

Features:
- Hierarchical memory (Episodic, Semantic, Procedural, Working)
- Self-learning from interactions
- Memory consolidation during dreams
- Pattern extraction and generalization
- Forgetting curve management
- Cross-session persistence
"""

from __future__ import annotations

import asyncio
import json
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict
from collections import deque

import numpy as np


class MemoryType(Enum):
    """Types of memory in the hierarchical system"""
    WORKING = "working"         # Short-term, active context
    EPISODIC = "episodic"       # Events, experiences
    SEMANTIC = "semantic"       # Facts, knowledge
    PROCEDURAL = "procedural"   # Skills, procedures
    EMOTIONAL = "emotional"     # Affective memories
    PROSPECTIVE = "prospective" # Future intentions


class MemoryPhase(Enum):
    """Memory processing phases"""
    ENCODING = "encoding"           # Initial learning
    CONSOLIDATION = "consolidation" # Stabilization
    STORAGE = "storage"             # Long-term storage
    RETRIEVAL = "retrieval"         # Recall
    RECONSOLIDATION = "reconsolidation"  # Updating after retrieval
    FORGETTING = "forgetting"       # Decay/pruning


@dataclass
class MemoryTrace:
    """A single memory trace with full metadata"""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.EPISODIC
    content: str = ""
    embedding: Optional[List[float]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    strength: float = 0.5           # Memory strength (0-1)
    vividness: float = 0.5          # Clarity of memory
    emotional_valence: float = 0.0  # -1 negative to 1 positive
    emotional_arousal: float = 0.0  # 0-1 intensity
    
    # Temporal
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    last_reinforced: Optional[datetime] = None
    
    # Forgetting curve
    decay_rate: float = 0.01        # Base decay per day
    last_consolidated: Optional[datetime] = None
    consolidation_count: int = 0
    
    # Associations
    linked_traces: Set[str] = field(default_factory=set)
    source_trace: Optional[str] = None  # For reconsolidation
    
    # Metadata
    importance: float = 0.5          # Explicit importance
    confidence: float = 0.8          # Confidence in accuracy
    privacy_level: int = 0           # 0=public, 1=private, 2=sensitive
    
    # Learning
    pattern_extracted: bool = False
    generalized_from: Optional[str] = None
    generalization_level: int = 0    # 0=specific, higher=more abstract
    
    def calculate_current_strength(self) -> float:
        """Calculate current strength using forgetting curve"""
        if self.strength <= 0:
            return 0.0
        
        days_since_access = (datetime.now(timezone.utc) - self.last_accessed).total_seconds() / 86400
        days_since_creation = (datetime.now(timezone.utc) - self.created_at).total_seconds() / 86400
        
        # Ebbinghaus forgetting curve with modifications
        # Strength = initial * e^(-decay * time) * reinforcement_factor
        reinforcement = min(1.0, self.access_count * 0.1 + self.consolidation_count * 0.2)
        decay = self.decay_rate * (1 - reinforcement * 0.5)
        
        strength = self.strength * np.exp(-decay * days_since_access) * (1 + reinforcement * 0.5)
        
        # Boost for recent access
        if days_since_access < 1:
            strength *= 1.5
        elif days_since_access < 7:
            strength *= 1.2
        
        return max(0.0, min(1.0, strength))

    def should_consolidate(self) -> bool:
        """Check if memory should be consolidated"""
        if self.consolidation_count >= 5:
            return False
        if self.calculate_current_strength() < 0.3:
            return False
        if self.last_consolidated:
            days = (datetime.now(timezone.utc) - self.last_consolidated).total_seconds() / 86400
            if days < 1:
                return False
        return True

    def reinforce(self, amount: float = 0.1):
        """Reinforce memory (e.g., through retrieval or rehearsal)"""
        self.strength = min(1.0, self.strength + amount)
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        self.last_reinforced = datetime.now(timezone.utc)

    def decay(self):
        """Apply decay (called periodically)"""
        current_strength = self.calculate_current_strength()
        self.strength = current_strength

    def link_to(self, trace_id: str):
        """Create associative link"""
        self.linked_traces.add(trace_id)

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "embedding": self.embedding,
            "context": self.context,
            "tags": list(self.tags),
            "strength": self.strength,
            "vividness": self.vividness,
            "emotional_valence": self.emotional_valence,
            "emotional_arousal": self.emotional_arousal,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "last_consolidated": self.last_consolidated.isoformat() if self.last_consolidated else None,
            "consolidation_count": self.consolidation_count,
            "linked_traces": list(self.linked_traces),
            "source_trace": self.source_trace,
            "importance": self.importance,
            "confidence": self.confidence,
            "privacy_level": self.privacy_level,
            "pattern_extracted": self.pattern_extracted,
            "generalized_from": self.generalized_from,
            "generalization_level": self.generalization_level,
        }


@dataclass
class MemoryQuery:
    """Query for memory retrieval"""
    query_text: str = ""
    memory_types: List[MemoryType] = field(default_factory=lambda: list(MemoryType))
    tags: Set[str] = field(default_factory=set)
    context_filter: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Tuple[datetime, datetime]] = None
    min_strength: float = 0.0
    max_results: int = 10
    include_linked: bool = True
    similarity_threshold: float = 0.2


@dataclass
class ConsolidationResult:
    """Result of memory consolidation"""
    consolidated_count: int = 0
    strengthened_count: int = 0
    pruned_count: int = 0
    patterns_extracted: int = 0
    generalized_concepts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class EnhancedMemorySystem:
    """
    Enhanced Hierarchical Memory System with Self-Learning
    
    Features:
    - Hierarchical memory (Working, Episodic, Semantic, Procedural)
    - Spaced repetition & spaced retrieval
    - Memory consolidation during "sleep"
    - Pattern extraction & generalization
    - Associative recall with spreading activation
    - Forgetting curve management
    - Cross-session persistence
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        config: Optional[Dict] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        ghost_client: Optional[Any] = None,
    ):
        self.config = config or {}
        self.storage_path = storage_path or Path.home() / ".jebat" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Memory stores by type
        self.traces: Dict[str, MemoryTrace] = {}
        self.traces_by_type: Dict[MemoryType, Set[str]] = defaultdict(set)
        self.traces_by_tag: Dict[str, Set[str]] = defaultdict(set)
        
        # Working memory (short-term, limited capacity)
        self.working_memory: deque = deque(maxlen=7)  # Miller's 7±2
        self.working_memory_capacity = 7
        
        # Activation spreading
        self.activation: Dict[str, float] = defaultdict(float)
        self.activation_decay = 0.95
        
        # Consolidation
        self.consolidation_interval = self.config.get("consolidation_interval", 3600)  # seconds
        self.min_strength_threshold = self.config.get("min_strength_threshold", 0.15)
        self.max_memories_per_type = self.config.get("max_memories_per_type", 10000)
        
        # Pattern extraction
        self.pattern_min_occurrences = 3
        self.pattern_similarity_threshold = 0.8
        self.extracted_patterns: Dict[str, Dict] = {}
        
        # Generalization
        self.generalizations: Dict[str, Dict] = {}
        
        # Forgetting
        self.forgetting_curve_enabled = True
        self.base_decay_rate = 0.01  # per day
        
        # Persistence
        self.storage_path = storage_path or Path.home() / ".jebat" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.traces_file = self.storage_path / "traces.json"
        self.patterns_file = self.storage_path / "patterns.json"
        self.metadata_file = self.storage_path / "metadata.json"
        
        # Embedding function for semantic search
        self.embedding_fn = embedding_fn
        
        # Ghost DB for vector search
        self.ghost_client = ghost_client
        self._ghost_collection = "memory_traces"
        self._ghost_dimension = 0  # Set on first embed
        
        # Background tasks
        self._consolidation_task: Optional[asyncio.Task] = None
        self._forgetting_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Load existing
        self._load()

    # ── Core Memory Operations ───────────────────────────────────────

    async def encode(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        context: Optional[Dict] = None,
        tags: Optional[Set[str]] = None,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.0,
        tags_set: Optional[Set[str]] = None,
        source_trace_id: Optional[str] = None,
    ) -> MemoryTrace:
        """Encode a new memory trace"""
        trace = MemoryTrace(
            memory_type=memory_type,
            content=content,
            context=context or {},
            tags=tags_set or tags or set(),
            importance=importance,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            source_trace=source_trace_id,
            decay_rate=self._calculate_decay_rate(memory_type, importance),
        )

        # Generate embedding if available
        if self.embedding_fn:
            try:
                trace.embedding = await self._get_embedding(content)
            except Exception:
                pass

        self._store_trace(trace)
        self._activate_trace(trace.trace_id, activation=1.0)

        # Index in Ghost DB for vector search (best-effort)
        if trace.embedding:
            await self._index_trace_in_ghost(trace)

        # Add to working memory if episodic/working
        if memory_type in (MemoryType.EPISODIC, MemoryType.WORKING):
            self._add_to_working_memory(trace.trace_id)

        # Auto-link to active memories
        await self._auto_associate(trace)

        return trace

    async def retrieve(
        self,
        query: Union[str, MemoryQuery],
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_strength: float = 0.0,
        include_linked: bool = True,
    ) -> List[MemoryTrace]:
        """Retrieve memories matching query.
        
        Uses Ghost DB vector search when available and embedding function is set.
        Falls back to n-gram similarity otherwise.
        """
        if isinstance(query, str):
            query = MemoryQuery(
                query_text=query,
                memory_types=memory_types or list(MemoryType),
                max_results=limit,
                min_strength=min_strength,
                include_linked=include_linked,
            )
        
        # ── Ghost DB vector search (preferred) ──────────────────────
        vector_scores: Dict[str, float] = {}
        if self.ghost_client and self.embedding_fn and query.query_text:
            try:
                query_embedding = await self._get_embedding(query.query_text)
                if query_embedding:
                    vector_results = await self._vector_search_ghost(
                        query_embedding, top_k=query.max_results * 3
                    )
                    vector_scores = {tid: score for tid, score in vector_results}
            except Exception:
                pass  # Fall back to n-gram
        
        # ── Calculate scores for all candidates ─────────────────────
        candidates = []
        for trace_id in self.traces:
            trace = self.traces[trace_id]
            
            # Type filter
            if query.memory_types and trace.memory_type not in query.memory_types:
                continue
            
            # Strength filter
            current_strength = trace.calculate_current_strength()
            if current_strength < query.min_strength:
                continue
            
            # Tag filter
            if query.tags and not query.tags.intersection(trace.tags):
                continue
            
            # Context filter
            if query.context_filter:
                if not all(trace.context.get(k) == v for k, v in query.context_filter.items()):
                    continue
            
            # Time range filter
            if query.time_range:
                if not (query.time_range[0] <= trace.created_at <= query.time_range[1]):
                    continue
            
            # Similarity: prefer vector search, fallback to n-gram
            if trace_id in vector_scores:
                similarity = vector_scores[trace_id]
            elif query.query_text and trace.content:
                similarity = self._text_similarity(query.query_text, trace.content)
            else:
                similarity = 1.0
            
            if similarity < query.similarity_threshold:
                continue
            
            # Activation boost
            activation = self.activation.get(trace.trace_id, 0)
            
            # Score: vector similarity gets higher weight when available
            if trace_id in vector_scores:
                score = current_strength * 0.3 + activation * 0.1 + similarity * 0.6
            else:
                score = current_strength * 0.6 + activation * 0.3 + similarity * 0.1
            candidates.append((score, trace))

        # Sort by score and limit
        candidates.sort(key=lambda x: x[0], reverse=True)
        results = [trace for _, trace in candidates[:query.max_results]]

        # Include linked traces
        if query.include_linked:
            linked = set()
            for trace in results:
                for linked_id in trace.linked_traces:
                    if linked_id in self.traces:
                        linked.add(self.traces[linked_id])
            results.extend(linked)

        # Update access stats
        for trace in results:
            trace.reinforce(0.05)

        return results[:query.max_results]

    async def consolidate(self, force: bool = False) -> ConsolidationResult:
        """Run memory consolidation process"""
        result = ConsolidationResult()
        
        # 1. Identify traces needing consolidation
        to_consolidate = []
        for trace in self.traces.values():
            if trace.should_consolidate() or force:
                to_consolidate.append(trace)

        # 2. Strengthen important memories
        for trace in to_consolidate:
            if trace.calculate_current_strength() > 0.4:
                trace.reinforce(0.15)
                trace.last_consolidated = datetime.now(timezone.utc)
                trace.consolidation_count += 1
                result.strengthened_count += 1
            result.consolidated_count += 1

        # 3. Pattern extraction
        patterns = await self._extract_patterns()
        result.patterns_extracted = len(patterns)

        # 4. Generalization
        generalizations = await self._extract_generalizations()
        result.generalized_concepts = generalizations

        # 3. Prune weak memories
        pruned = self._prune_weak_memories()
        result.pruned_count = pruned

        # Save changes
        self._save()
        
        return result

    async def _extract_patterns(self) -> List[str]:
        """Extract recurring patterns from memories"""
        patterns = []
        
        # Group by tags
        tag_groups = defaultdict(list)
        for trace in self.traces.values():
            for tag in trace.tags:
                tag_groups[tag].append(trace)

        for tag, traces in tag_groups.items():
            if len(traces) >= self.pattern_min_occurrences:
                # Check similarity
                contents = [t.content for t in traces]
                if self._are_similar(contents):
                    pattern = self._extract_pattern(tag, traces)
                    if pattern:
                        patterns.append(pattern)
                        self.extracted_patterns[pattern] = {
                            "tag": tag,
                            "count": len(traces),
                            "traces": [t.trace_id for t in traces],
                            "extracted_at": datetime.now(timezone.utc).isoformat(),
                        }

        return patterns

    def _are_similar(self, contents: List[str]) -> bool:
        """Check if contents are similar enough for pattern"""
        if len(contents) < 2:
            return False
        # Simple similarity check
        # In practice, would use embeddings
        words_sets = [set(c.lower().split()) for c in contents]
        common = set.intersection(*words_sets)
        union = set.union(*words_sets)
        return len(common) / len(union) > self.pattern_similarity_threshold if union else False

    def _extract_pattern(self, tag: str, traces: List[MemoryTrace]) -> str:
        """Extract pattern description from similar traces"""
        # Simple extraction - in practice would use LLM
        common_words = set.intersection(*[set(t.content.lower().split()) for t in traces])
        return f"Pattern: {tag} - recurring themes: {', '.join(list(common_words)[:5])}"

    async def _extract_generalizations(self) -> List[str]:
        """Extract generalizations from specific memories"""
        generalizations = []
        
        # Group by similarity and extract commonalities
        episodic = [t for t in self.traces.values() if t.memory_type == MemoryType.EPISODIC]
        
        # Group similar episodic memories
        groups = defaultdict(list)
        for trace in episodic:
            key = tuple(sorted(trace.tags))[:3] if trace.tags else "untagged"
            groups[key].append(trace)

        for key, traces in groups.items():
            if len(traces) >= 3:
                # Extract common structure
                gen = self._create_generalization(traces)
                if gen:
                    self.generalizations[gen["id"]] = gen
                    generalizations.append(gen["concept"])

        return generalizations

    def _create_generalization(self, traces: List[MemoryTrace]) -> Optional[Dict]:
        """Create a generalized semantic memory from episodes"""
        if len(traces) < 3:
            return None

        # Find common structure
        common_tags = set.intersection(*[set(t.tags) for t in traces]) if traces[0].tags else set()
        
        gen_id = f"gen_{uuid.uuid4().hex[:8]}"
        return {
            "id": gen_id,
            "concept": f"Generalized: {', '.join(list(common_tags)[:3])}",
            "source_traces": [t.trace_id for t in traces],
            "confidence": min(1.0, len(traces) * 0.15),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _prune_weak_memories(self) -> int:
        """Remove memories below threshold"""
        pruned = 0
        to_remove = []

        for trace_id, trace in self.traces.items():
            if trace.calculate_current_strength() < self.min_strength_threshold:
                to_remove.append(trace_id)

        for trace_id in to_remove:
            self._remove_trace(trace_id)
            pruned += 1

        return pruned

    def _forgetting_curve_step(self):
        """Apply forgetting curve decay to all traces"""
        if not self.forgetting_curve_enabled:
            return

        for trace in self.traces.values():
            trace.decay()

        # Remove extremely weak memories
        self._prune_weak_memories()

    # ── Working Memory ──────────────────────────────────────────────

    def _add_to_working_memory(self, trace_id: str):
        if trace_id in self.working_memory:
            self.working_memory.remove(trace_id)
        self.working_memory.appendleft(trace_id)

    def get_working_memory(self) -> List[MemoryTrace]:
        return [self.traces[tid] for tid in self.working_memory if tid in self.traces]

    def clear_working_memory(self):
        self.working_memory.clear()

    # ── Activation Spreading ────────────────────────────────────────

    def _activate_trace(self, trace_id: str, activation: float = 1.0):
        if trace_id in self.traces:
            self.activation[trace_id] = min(1.0, self.activation.get(trace_id, 0) + activation)

    def spread_activation(self, trace_id: str, activation: float = 0.5, depth: int = 2):
        """Spread activation to linked traces"""
        if depth <= 0 or trace_id not in self.traces:
            return

        trace = self.traces[trace_id]
        spread_amount = activation * 0.7

        for linked_id in trace.linked_traces:
            if linked_id in self.traces:
                self.activation[linked_id] = min(1.0, self.activation.get(linked_id, 0) + spread_amount)
                if depth > 1:
                    self.spread_activation(linked_id, activation * 0.5, depth - 1)

    def decay_activation(self):
        """Decay all activations"""
        for trace_id in self.activation:
            self.activation[trace_id] *= self.activation_decay
            if self.activation[trace_id] < 0.01:
                del self.activation[trace_id]

    # ── Retrieval Helpers ───────────────────────────────────────────

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity with n-gram fallback"""
        if self.embedding_fn:
            # Use embeddings if available
            return 0.0  # Handled elsewhere
        
        # Character n-gram similarity (better than word overlap for partial matches)
        def get_ngrams(text: str, n: int = 3) -> Set[str]:
            text = text.lower()
            return {text[i:i+n] for i in range(len(text) - n + 1)}
        
        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        return len(intersection) / len(union) if union else 0.0

    async def _get_embedding(self, text: str) -> List[float]:
        if self.embedding_fn:
            return await self.embedding_fn(text)
        return []

    # ── Ghost DB Vector Search ────────────────────────────────────────

    def _ensure_ghost_collection(self, dimension: int) -> None:
        """Create Ghost DB collection if it doesn't exist."""
        if not self.ghost_client:
            return
        if self._ghost_dimension == dimension and self._ghost_collection in [
            c.name for c in self.ghost_client.list_collections()
        ]:
            return
        try:
            from jebat.features.ghost_db.models import Collection, HNSWParams, DistanceMetric
            self.ghost_client.create_collection(
                Collection(
                    name=self._ghost_collection,
                    dimension=dimension,
                    metric=DistanceMetric.COSINE,
                    hnsw=HNSWParams(m=16, ef_construction=200),
                )
            )
            self._ghost_dimension = dimension
        except Exception:
            pass  # Collection may already exist

    async def _index_trace_in_ghost(self, trace: MemoryTrace) -> None:
        """Index a memory trace in Ghost DB for vector search."""
        if not self.ghost_client or not trace.embedding:
            return
        try:
            import numpy as np
            vec = np.array(trace.embedding, dtype=np.float32)
            self._ensure_ghost_collection(len(trace.embedding))
            from jebat.features.ghost_db.models import Document
            self.ghost_client.upsert(
                collection=self._ghost_collection,
                documents=[Document(
                    id=trace.trace_id,
                    text=trace.content[:1000],
                    embedding=vec,
                    metadata={
                        "memory_type": trace.memory_type.value,
                        "importance": trace.importance,
                        "created_at": trace.created_at.isoformat(),
                    },
                )],
            )
        except Exception:
            pass  # Best-effort indexing

    async def _vector_search_ghost(
        self, query_embedding: List[float], top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Search Ghost DB for similar vectors. Returns [(trace_id, score), ...]."""
        if not self.ghost_client or not query_embedding:
            return []
        try:
            import numpy as np
            vec = np.array(query_embedding, dtype=np.float32)
            results = self.ghost_client.search(
                collection=self._ghost_collection,
                query_vector=vec,
                k=top_k,
            )
            return [(r.id, 1.0 - r.distance) for r in results]  # Convert distance to similarity
        except Exception:
            return []

    # ── Decay ─────────────────────────────────────────────────────────

    def _calculate_decay_rate(self, memory_type: MemoryType, importance: float) -> float:
        base_rates = {
            MemoryType.WORKING: 0.5,
            MemoryType.EPISODIC: 0.02,
            MemoryType.SEMANTIC: 0.005,
            MemoryType.PROCEDURAL: 0.001,
            MemoryType.EMOTIONAL: 0.01,
            MemoryType.PROSPECTIVE: 0.1,
        }
        base = base_rates.get(memory_type, 0.01)
        return base * (1 - importance * 0.5)

    # ── Storage ──────────────────────────────────────────────────────

    def _store_trace(self, trace: MemoryTrace):
        self.traces[trace.trace_id] = trace
        self.traces_by_type[trace.memory_type].add(trace.trace_id)
        for tag in trace.tags:
            self.traces_by_tag[tag].add(trace.trace_id)

    def _remove_trace(self, trace_id: str):
        if trace_id in self.traces:
            trace = self.traces[trace_id]
            self.traces_by_type[trace.memory_type].discard(trace_id)
            for tag in trace.tags:
                self.traces_by_tag[tag].discard(trace_id)
            del self.traces[trace_id]
            self.activation.pop(trace_id, None)

    async def _auto_associate(self, trace: MemoryTrace):
        """Automatically associate with similar active memories"""
        active_ids = [tid for tid, act in self.activation.items() if act > 0.3]
        for active_id in active_ids[:5]:
            if active_id != trace.trace_id and active_id in self.traces:
                trace.link_to(active_id)
                self.traces[active_id].link_to(trace.trace_id)

    # ── Background Tasks ────────────────────────────────────────────

    async def start_background_tasks(self):
        """Start background consolidation and forgetting tasks"""
        self._running = True
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
        self._forgetting_task = asyncio.create_task(self._forgetting_loop())

    async def stop_background_tasks(self):
        self._running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
        if self._forgetting_task:
            self._forgetting_task.cancel()

    async def _consolidation_loop(self):
        while self._running:
            try:
                await asyncio.sleep(self.consolidation_interval)
                if self._running:
                    await self.consolidate()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Consolidation error: {e}")

    async def _forgetting_loop(self):
        while self._running:
            try:
                await asyncio.sleep(3600)  # Hourly
                if self._running:
                    self._forgetting_curve_step()
                    self.decay_activation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Forgetting error: {e}")

    # ── Persistence ─────────────────────────────────────────────────

    def _save(self):
        """Save memory to disk"""
        try:
            data = {
                "traces": {k: v.to_dict() for k, v in self.traces.items()},
                "patterns": self.extracted_patterns,
                "generalizations": self.generalizations,
                "concept_weights": dict(self.concept_weights),
                "concept_graph": {k: list(v) for k, v in self.concept_graph.items()},
            }
            with open(self.traces_file, "w") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            print(f"Memory save error: {e}")

    def _load(self):
        try:
            if self.traces_file.exists():
                with open(self.traces_file) as f:
                    data = json.load(f)

                for tid, td in data.get("traces", {}).items():
                    # Convert datetime strings back
                    for key in ["created_at", "last_accessed", "last_reinforced", "last_consolidated"]:
                        if td.get(key):
                            td[key] = datetime.fromisoformat(td[key])
                    td["tags"] = set(td.get("tags", []))
                    td["linked_traces"] = set(td.get("linked_traces", []))
                    td["memory_type"] = MemoryType(td["memory_type"])
                    trace = MemoryTrace(**td)
                    self.traces[tid] = trace
                    self.traces_by_type[trace.memory_type].add(tid)
                    for tag in trace.tags:
                        self.traces_by_tag[tag].add(tid)

                self.extracted_patterns = data.get("patterns", {})
                self.generalizations = data.get("generalizations", {})
                self.concept_weights = defaultdict(float, data.get("concept_weights", {}))
                self.concept_graph = defaultdict(set, {k: set(v) for k, v in data.get("concept_graph", {}).items()})
        except Exception as e:
            print(f"Memory load error: {e}")

    # ── Convenience Methods ────────────────────────────────────────

    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        **kwargs
    ) -> MemoryTrace:
        """Convenience method to encode a memory"""
        return await self.encode(content, memory_type, **kwargs)

    async def recall(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
    ) -> List[MemoryTrace]:
        """Convenience recall method"""
        return await self.retrieve(query, memory_types=[memory_type] if memory_type else None, limit=limit)

    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        stats = {
            "total_traces": len(self.traces),
            "by_type": {t.value: len(ids) for t, ids in self.traces_by_type.items()},
            "working_memory_size": len(self.working_memory),
            "total_patterns": len(self.extracted_patterns),
            "generalizations": len(self.generalizations),
            "avg_strength": np.mean([t.calculate_current_strength() for t in self.traces.values()]) if self.traces else 0,
            "total_associations": sum(len(t.linked_traces) for t in self.traces.values()),
        }
        return stats


# ── Specialized Memory Classes ─────────────────────────────────────


class WorkingMemory:
    """Limited-capacity working memory with rehearsal"""
    
    def __init__(self, capacity: int = 7, rehearsal_interval: float = 10.0):
        self.capacity = capacity
        self.items: List[MemoryTrace] = []
        self.rehearsal_interval = rehearsal_interval
        self._rehearsal_task: Optional[asyncio.Task] = None

    def add(self, trace: MemoryTrace):
        if trace.trace_id in [i.trace_id for i in self.items]:
            # Move to front (recent)
            self.items = [i for i in self.items if i.trace_id != trace.trace_id]
        self.items.insert(0, trace)
        if len(self.items) > self.capacity:
            self.items.pop()

    def get_all(self) -> List[MemoryTrace]:
        return list(self.items)

    def clear(self):
        self.items.clear()


class SemanticMemory:
    """Long-term semantic knowledge base"""
    
    def __init__(self):
        self.concepts: Dict[str, Dict] = {}
        self.relations: Dict[str, Set[str]] = defaultdict(set)
        self.properties: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def add_concept(self, concept: str, properties: Dict = None, relations: Dict[str, List[str]] = None):
        if concept not in self.concepts:
            self.concepts[concept] = {"count": 0, "confidence": 0.5}
        self.concepts[concept]["count"] += 1
        self.concepts[concept]["confidence"] = min(1.0, self.concepts[concept]["confidence"] + 0.05)
        
        if properties:
            self.properties[concept].update(properties)
        
        if relations:
            for rel_type, targets in relations.items():
                for target in targets:
                    self.relations[f"{concept}:{rel_type}"].add(target)

    def query(self, concept: str, relation: Optional[str] = None) -> Dict:
        result = {"concept": concept, "properties": self.properties.get(concept, {})}
        if relation:
            result["relations"] = list(self.relations.get(f"{concept}:{relation}", set()))
        else:
            result["all_relations"] = {
                k.split(":")[1]: list(v) for k, v in self.relations.items() if k.startswith(f"{concept}:")
            }
        return result


class ProceduralMemory:
    """Skill and procedure memory"""
    
    def __init__(self):
        self.procedures: Dict[str, Dict] = {}
        self.execution_counts: Dict[str, int] = defaultdict(int)
        self.success_rates: Dict[str, float] = {}

    def store_procedure(
        self,
        name: str,
        steps: List[str],
        preconditions: List[str] = None,
        postconditions: List[str] = None,
        tags: Set[str] = None,
    ):
        self.procedures[name] = {
            "name": name,
            "steps": steps,
            "preconditions": preconditions or [],
            "postconditions": postconditions or [],
            "tags": tags or set(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": 1,
        }

    def execute(self, name: str, context: Dict = None) -> Dict:
        """Simulate procedure execution"""
        if name not in self.procedures:
            return {"success": False, "error": "Procedure not found"}
        
        proc = self.procedures[name]
        self.execution_counts[name] += 1
        
        # Simulate success based on history
        success_rate = self.success_rates.get(name, 0.8)
        success = random.random() < success_rate
        
        if success:
            self.success_rates[name] = min(1.0, success_rate + 0.01)
        else:
            self.success_rates[name] = max(0.1, success_rate - 0.05)
        
        return {
            "success": success,
            "steps_executed": proc["steps"],
            "execution_count": self.execution_counts[name],
        }

    def get_procedure(self, name: str) -> Optional[Dict]:
        return self.procedures.get(name)


# ── Self-Learning Integration ───────────────────────────────────────


class SelfLearningMemory(EnhancedMemorySystem):
    """Memory system with explicit self-learning capabilities"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learning_rate = 0.1
        self.meta_learning_enabled = True
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)

    async def learn_from_outcome(
        self,
        action: str,
        context: Dict,
        outcome: str,
        success: bool,
        reward: float = 0.0,
    ):
        """Learn from action outcome"""
        # Store outcome memory
        trace = await self.encode(
            content=f"Action: {action} | Context: {json.dumps(context)} | Outcome: {outcome} | Success: {success}",
            memory_type=MemoryType.PROCEDURAL,
            importance=0.7 if success else 0.9,  # Failures are important
            emotional_valence=0.5 if success else -0.5,
            tags={"learning", "outcome", "success" if success else "failure"},
        )

        # Update strategy performance
        self.strategy_performance[action].append(1.0 if success else 0.0)
        
        # Keep only recent history
        if len(self.strategy_performance[action]) > 100:
            self.strategy_performance[action] = self.strategy_performance[action][-100:]

        # Extract pattern if repeated
        if len(self.strategy_performance[action]) >= 5:
            recent = self.strategy_performance[action][-5:]
            success_rate = sum(recent) / len(recent)
            
            # Create or update procedural memory
            if success_rate > 0.8:
                await self._reinforce_procedure(action, context)
            elif success_rate < 0.3:
                await self._mark_avoid(action, context)

    async def _reinforce_procedure(self, action: str, context: Dict):
        """Reinforce a successful procedure"""
        proc_trace = await self.encode(
            content=f"REINFORCED PROCEDURE: {action} in context {json.dumps(context)}",
            memory_type=MemoryType.PROCEDURAL,
            importance=0.9,
            tags={"reinforced", "procedure", "success"},
        )

    async def _mark_avoid(self, action: str, context: Dict):
        """Mark action as to be avoided in context"""
        avoid_trace = await self.encode(
            content=f"AVOID: {action} in context {json.dumps(context)} - low success rate",
            memory_type=MemoryType.PROCEDURAL,
            importance=0.8,
            emotional_valence=-0.7,
            tags={"avoid", "warning", "failure"},
        )

    def get_strategy_success_rate(self, action: str) -> float:
        history = self.strategy_performance.get(action, [])
        if not history:
            return 0.5
        return sum(history) / len(history)

    def get_best_strategy(self, actions: List[str]) -> str:
        """Select best action based on learned success rates"""
        if not actions:
            return random.choice(actions) if actions else ""
        return max(actions, key=self.get_strategy_success_rate)


# ── Convenience Functions ──────────────────────────────────────────


async def create_memory_system(
    storage_path: Optional[Path] = None,
    config: Optional[Dict] = None,
) -> EnhancedMemorySystem:
    """Create and initialize memory system"""
    system = EnhancedMemorySystem(storage_path=storage_path, config=config)
    await system.start_background_tasks()
    return system


async def create_self_learning_memory(*args, **kwargs) -> SelfLearningMemory:
    system = SelfLearningMemory(*args, **kwargs)
    await system.start_background_tasks()
    return system


def create_working_memory(capacity: int = 7) -> WorkingMemory:
    return WorkingMemory(capacity=capacity)


def create_semantic_memory() -> SemanticMemory:
    return SemanticMemory()


def create_procedural_memory() -> ProceduralMemory:
    return ProceduralMemory()


# Export
__all__ = [
    "MemoryType",
    "MemoryPhase",
    "MemoryTrace",
    "MemoryQuery",
    "ConsolidationResult",
    "EnhancedMemorySystem",
    "WorkingMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "SelfLearningMemory",
    "create_memory_system",
    "create_self_learning_memory",
    "create_working_memory",
    "create_semantic_memory",
    "create_procedural_memory",
]