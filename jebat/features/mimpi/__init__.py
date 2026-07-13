"""
Mimpi (Dream/Imagination) System - JEBAT's Creative Subconscious

Mimpi enables JEBAT to:
1. Dream/Simulate future scenarios
2. Counterfactual reasoning (what-if scenarios)
3. Creative ideation and brainstorming
4. Subconscious problem solving during "sleep"
5. Imagination-driven planning
"""

from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from itertools import combinations
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict

from jebat.features.ultra_think import ThinkingMode, UltraThink
from jebat.features.ultra_loop import UltraLoop, LoopPhase, LoopContext


class DreamType(Enum):
    """Types of dreams JEBAT can have"""
    SIMULATION = "simulation"           # Future scenario simulation
    COUNTERFACTUAL = "counterfactual"   # What-if scenarios
    CREATIVE = "creative"               # Creative ideation
    PROBLEM_SOLVING = "problem_solving" # Subconscious problem solving
    MEMORY_CONSOLIDATION = "memory_consolidation"  # Memory replay/reorganization
    PLANNING = "planning"               # Strategic planning dreams
    CREATIVE_SYNTHESIS = "creative_synthesis"  # Combining unrelated concepts
    ADVERSARIAL = "adversarial"         # Red-teaming / stress testing


class DreamPhase(Enum):
    """Phases of a dream cycle"""
    INDUCTION = "induction"       # Entering dream state
    EXPLORATION = "exploration"   # Exploring dream space
    SYNTHESIS = "synthesis"       # Combining concepts
    INSIGHT = "insight"           # Aha! moments
    CONSOLIDATION = "consolidation"  # Memory integration
    AWAKENING = "awakening"       # Returning to waking state


class DreamIntensity(Enum):
    """Intensity levels of dreaming"""
    LUCID = "lucid"           # Fully aware, controllable
    VIVID = "vivid"           # Clear, memorable
    HYPNAGOGIC = "hypnagogic" # Between wake/sleep, creative
    DEEP = "deep"             # Unconscious, restructuring


@dataclass
class DreamScene:
    """A single scene within a dream"""
    scene_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    concepts: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    confidence: float = 0.5
    duration_ms: int = 0
    related_memories: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Dream:
    """A complete dream session"""
    dream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dream_type: DreamType = DreamType.SIMULATION
    intensity: DreamIntensity = DreamIntensity.HYPNAGOGIC
    phases_completed: List[DreamPhase] = field(default_factory=list)
    scenes: List[DreamScene] = field(default_factory=list)
    problem_context: Optional[str] = None
    seed_concepts: List[str] = field(default_factory=list)
    insights_generated: List[str] = field(default_factory=list)
    actionable_ideas: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def add_scene(self, scene: DreamScene):
        self.scenes.append(scene)

    def complete_phase(self, phase: DreamPhase):
        if phase not in self.phases_completed:
            self.phases_completed.append(phase)

    def add_insight(self, insight: str, confidence: float = 0.7):
        self.insights_generated.append(insight)
        self.confidence_scores[insight] = confidence

    def add_actionable_idea(self, idea: str, confidence: float = 0.6):
        self.actionable_ideas.append(idea)
        self.confidence_scores[idea] = confidence

    def end(self):
        self.ended_at = datetime.now(timezone.utc)
        self.duration_seconds = (self.ended_at - self.started_at).total_seconds()

    def to_summary(self) -> Dict:
        return {
            "dream_id": self.dream_id,
            "type": self.dream_type.value,
            "intensity": self.intensity.value,
            "phases": [p.value for p in self.phases_completed],
            "scenes_count": len(self.scenes),
            "insights_count": len(self.insights_generated),
            "ideas_count": len(self.actionable_ideas),
            "duration_seconds": self.duration_seconds,
            "top_insights": self.insights_generated[:5],
            "top_ideas": self.actionable_ideas[:5],
        }


class DreamEngine:
    """
    Mimpi Engine - JEBAT's Dream/Imagination System
    
    Runs dream cycles for creative problem solving, planning,
    memory consolidation, and creative synthesis.
    """

    def __init__(
        self,
        ultra_think: Optional[UltraThink] = None,
        ultra_loop = None,
        memory_manager = None,
        config: Optional[Dict] = None,
    ):
        self.ultra_think = ultra_think
        self.ultra_loop = ultra_loop
        self.memory_manager = memory_manager
        self.config = config or {}

        # Dream configuration
        self.dream_interval = self.config.get("dream_interval", 300)  # seconds
        self.max_dream_duration = self.config.get("max_dream_duration", 60)  # seconds
        self.dream_probability = self.config.get("dream_probability", 0.3)
        self.lucid_probability = self.config.get("lucid_probability", 0.1)

        # Dream history
        self.dream_history: List[Dream] = []
        self.max_history = self.config.get("max_dream_history", 100)

        # Creativity parameters
        self.creativity_temperature = self.config.get("creativity_temperature", 0.8)
        self.association_distance = self.config.get("association_distance", 2)
        self.novelty_weight = self.config.get("novelty_weight", 0.7)
        self.coherence_weight = self.config.get("coherence_weight", 0.5)

        # State
        self._is_dreaming = False
        self._current_dream: Optional[Dream] = None
        self._dream_task: Optional[asyncio.Task] = None

        # Concept association graph (simple semantic network)
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)
        self.concept_weights: Dict[str, float] = defaultdict(float)

        # Initialize concept graph with default associations
        self._initialize_concept_graph()

    def _initialize_concept_graph(self):
        """Initialize concept graph with default technical associations"""
        default_associations = {
            "database": {"indexing", "caching", "query optimization", "sharding", "replication", "ACID", "SQL", "NoSQL"},
            "optimization": {"profiling", "caching", "indexing", "algorithms", "complexity", "bottleneck", "performance"},
            "query": {"optimization", "execution plan", "indexing", "SQL", "NoSQL", "filtering", "join"},
            "indexing": {"B-tree", "hash", "composite", "covering", "partial", "unique", "clustered"},
            "caching": {"Redis", "Memcached", "LRU", "TTL", "invalidation", "distributed", "local"},
            "query optimization": {"execution plan", "statistics", "cost-based", "rule-based", "hints"},
            "sharding": {"horizontal", "vertical", "consistent hashing", "range", "geo"},
            "replication": {"master-slave", "master-master", "synchronous", "asynchronous", "consensus"},
            "API": {"REST", "GraphQL", "gRPC", "WebSocket", "rate limiting", "authentication"},
            "microservices": {"service mesh", "circuit breaker", "retry", "timeout", "observability"},
            "authentication": {"JWT", "OAuth2", "OIDC", "SAML", "API keys", "mTLS"},
            "authorization": {"RBAC", "ABAC", "policy", "scope", "claims"},
            "container": {"Docker", "Kubernetes", "Podman", "build", "registry", "orchestration"},
            "CI/CD": {"pipeline", "build", "test", "deploy", "artifact", "rollback", "canary"},
            "monitoring": {"metrics", "logs", "traces", "alerts", "dashboards", "SLO", "SLI"},
            "logging": {"structured", "levels", "aggregation", "correlation", "retention"},
            "tracing": {"distributed", "spans", "context propagation", "sampling", "OpenTelemetry"},
            "security": {"encryption", "TLS", "certificates", "vulnerability", "compliance"},
            "testing": {"unit", "integration", "e2e", "contract", "chaos", "load", "property"},
            "design pattern": {"singleton", "factory", "observer", "strategy", "decorator", "adapter", "facade"},
            "architecture": {"monolith", "microservices", "serverless", "event-driven", "CQRS", "event sourcing"},
            "concurrency": {"lock", "mutex", "semaphore", "async", "thread pool", "actor model"},
            "distributed systems": {"CAP theorem", "consensus", "Raft", "Paxos", "leader election"},
            "message queue": {"Kafka", "RabbitMQ", "Redis Streams", "NATS", "pub/sub", "dead letter"},
            "streaming": {"Flink", "Spark Streaming", "ksqlDB", "windowing", "watermark", "exactly-once"},
            "data pipeline": {"ETL", "ELT", "Airflow", "Dagster", "Prefect", "idempotency"},
            "MLOps": {"training", "serving", "feature store", "experiment tracking", "drift detection"},
            "vector database": {"embedding", "similarity search", "HNSW", "IVF", "Pinecone", "Weaviate", "Qdrant"},
            "RAG": {"retrieval", "generation", "chunking", "embedding", "reranking", "citation"},
            "LLM": {"prompt engineering", "fine-tuning", "RLHF", "context window", "tokenization", "inference"},
            "agent": {"tool use", "planning", "memory", "reflection", "multi-agent", "orchestration"},
        }
        for concept, associations in default_associations.items():
            self.concept_graph[concept] = set(associations)
            # Also add reverse associations
            for assoc in associations:
                self.concept_graph[assoc].add(concept)

    async def induce_dream(
        self,
        dream_type: DreamType = DreamType.SIMULATION,
        seed_concepts: Optional[List[str]] = None,
        problem_context: Optional[str] = None,
        intensity: Optional[DreamIntensity] = None,
        duration_seconds: Optional[int] = None,
    ) -> Dream:
        """Induce a dream session"""
        if self._is_dreaming:
            raise RuntimeError("Already dreaming")

        self._is_dreaming = True
        dream = Dream(
            dream_type=dream_type,
            intensity=intensity or self._select_intensity(),
            problem_context=problem_context,
            seed_concepts=seed_concepts or [],
        )

        self._current_dream = dream
        start_time = datetime.now(timezone.utc)

        try:
            # Phase 1: Induction
            await self._phase_induction(dream)
            dream.complete_phase(DreamPhase.INDUCTION)

            # Phase 2: Exploration
            await self._phase_exploration(dream)
            dream.complete_phase(DreamPhase.EXPLORATION)

            # Phase 3: Synthesis
            await self._phase_synthesis(dream)
            dream.complete_phase(DreamPhase.SYNTHESIS)

            # Phase 4: Insight
            await self._phase_insight(dream)
            dream.complete_phase(DreamPhase.INSIGHT)

            # Phase 5: Consolidation
            await self._phase_consolidation(dream)
            dream.complete_phase(DreamPhase.CONSOLIDATION)

            # Phase 6: Awakening
            await self._phase_awakening(dream)
            dream.complete_phase(DreamPhase.AWAKENING)

        except asyncio.CancelledError:
            dream.metadata["cancelled"] = True
            raise
        except Exception as e:
            dream.metadata["error"] = str(e)
            raise
        finally:
            dream.end()
            self._is_dreaming = False
            self._current_dream = None
            self._store_dream(dream)

        return dream

    def _select_intensity(self) -> DreamIntensity:
        """Select dream intensity based on probabilities"""
        rand = random.random()
        if rand < self.lucid_probability:
            return DreamIntensity.LUCID
        elif rand < self.lucid_probability + 0.2:
            return DreamIntensity.VIVID
        elif rand < self.lucid_probability + 0.5:
            return DreamIntensity.HYPNAGOGIC
        return DreamIntensity.DEEP

    async def _phase_induction(self, dream: Dream):
        """Phase 1: Induction - Enter dream state"""
        scene = DreamScene(
            description="Entering dream state... consciousness expanding",
            concepts=dream.seed_concepts.copy(),
            emotions=["curiosity", "anticipation"],
            duration_ms=500,
        )
        dream.add_scene(scene)

        # Initialize concept activation
        for concept in dream.seed_concepts:
            self._activate_concept(concept, activation=1.0)

        # Load relevant memories if memory manager available
        if self.memory_manager and dream.problem_context:
            memories = await self._recall_relevant_memories(dream.problem_context)
            for mem in memories[:5]:
                self._activate_concept(mem.get("concept", ""), activation=0.7)

    async def _phase_exploration(self, dream: Dream):
        """Phase 2: Exploration - Free association and concept traversal"""
        steps = random.randint(5, 10)

        for step in range(steps):
            # Select current focus concept
            active_concepts = self._get_active_concepts()
            if not active_concepts:
                break

            focus = random.choice(active_concepts)

            # Explore associations
            associations = self._get_associations(focus, depth=self.association_distance)

            # Create scene from exploration
            scene = DreamScene(
                description=f"Exploring '{focus}' - discovering connections",
                concepts=[focus] + associations[:5],
                emotions=["wonder", "curiosity"],
                insights=[],
                duration_ms=random.randint(200, 800),
            )

            # Generate insights during exploration
            if random.random() < 0.3:
                insight = self._generate_insight(focus, associations[:3])
                if insight:
                    scene.insights.append(insight)
                    dream.add_insight(insight, confidence=random.uniform(0.5, 0.8))

            dream.add_scene(scene)

            # Spread activation
            for assoc in associations[:3]:
                self._activate_concept(assoc, activation=0.5)

            await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _phase_synthesis(self, dream: Dream):
        """Phase 3: Synthesis - Combine concepts into novel ideas"""
        active = self._get_active_concepts()
        if len(active) < 2:
            return

        # Select random pairs for synthesis
        pairs = list(combinations(active, 2))
        random.shuffle(pairs)

        for concept1, concept2 in pairs[:5]:
            synthesis = self._synthesize_concepts(concept1, concept2)
            if synthesis:
                scene = DreamScene(
                    description=f"Synthesizing '{concept1}' + '{concept2}' → '{synthesis['idea']}'",
                    concepts=[concept1, concept2, synthesis['idea']],
                    emotions=["excitement", "satisfaction"],
                    insights=[synthesis.get('insight', '')],
                    duration_ms=random.randint(500, 2000),
                )
                scene.insights = [synthesis.get('insight', '')]
                dream.add_scene(scene)

                dream.add_actionable_idea(synthesis['idea'], confidence=synthesis.get('confidence', 0.6))

                # Activate the new synthesized concept
                self._activate_concept(synthesis['idea'], activation=0.8)

            await asyncio.sleep(random.uniform(0.1, 0.2))

    async def _phase_insight(self, dream: Dream):
        """Phase 4: Insight - Aha! moments and breakthrough"""
        # Review all scenes for patterns
        all_concepts = set()
        for scene in dream.scenes:
            all_concepts.update(scene.concepts)

        # Generate meta-insights
        meta_insights = self._generate_meta_insights(
            list(all_concepts),
            dream.problem_context
        )

        for insight in meta_insights:
            scene = DreamScene(
                description=f"Meta-insight: {insight['insight']}",
                concepts=list(all_concepts),
                emotions=["clarity", "understanding", "breakthrough"],
                insights=[insight['insight']],
                confidence=insight['confidence'],
                duration_ms=random.randint(1000, 3000),
            )
            dream.add_scene(scene)
            dream.add_insight(insight['insight'], confidence=insight['confidence'])

        # Create final synthesis scene
        if dream.insights_generated:
            final_scene = DreamScene(
                description=f"Dream synthesis complete: {len(dream.insights_generated)} insights, {len(dream.actionable_ideas)} actionable ideas",
                concepts=list(all_concepts),
                emotions=["clarity", "accomplishment", "readiness"],
                insights=dream.insights_generated,
                duration_ms=2000,
            )
            dream.add_scene(final_scene)

    async def _phase_consolidation(self, dream: Dream):
        """Phase 5: Consolidation - Integrate with memory"""
        if self.memory_manager:
            # Store insights as memories
            for insight in dream.insights_generated:
                await self._store_insight_memory(insight, dream)

            # Store actionable ideas
            for idea in dream.actionable_ideas:
                await self._store_idea_memory(idea, dream)

            # Update concept graph
            self._consolidate_concept_graph()

        # Store dream in long-term memory
        await self._store_dream_memory(dream)

    async def _phase_awakening(self, dream: Dream):
        """Phase 6: Awakening - Return to waking state with insights"""
        scene = DreamScene(
            description=f"Awakening with {len(dream.insights_generated)} insights and {len(dream.actionable_ideas)} actionable ideas",
            concepts=[],
            emotions=["clarity", "motivation", "purpose"],
            insights=dream.insights_generated[-3:] if dream.insights_generated else [],
            duration_ms=1000,
        )
        dream.add_scene(scene)

    def _select_intensity(self) -> DreamIntensity:
        """Select dream intensity based on probabilities"""
        rand = random.random()
        if rand < self.lucid_probability:
            return DreamIntensity.LUCID
        elif rand < self.lucid_probability + 0.2:
            return DreamIntensity.VIVID
        elif rand < self.lucid_probability + 0.5:
            return DreamIntensity.HYPNAGOGIC
        return DreamIntensity.DEEP

    def _activate_concept(self, concept: str, activation: float):
        """Activate a concept in the semantic network"""
        if concept not in self.concept_weights:
            self.concept_weights[concept] = 0.0
        self.concept_weights[concept] = min(1.0, self.concept_weights[concept] + activation)

        # Decay other concepts slightly
        for c in self.concept_weights:
            if c != concept:
                self.concept_weights[c] *= 0.99

    def _get_active_concepts(self, threshold: float = 0.3) -> List[str]:
        """Get currently active concepts above threshold"""
        return [c for c, w in self.concept_weights.items() if w >= threshold]

    def _get_associations(self, concept: str, depth: int = 2) -> List[str]:
        """Get associated concepts from semantic network"""
        visited = set()
        associations = set()
        queue = [(concept, 0)]

        while queue and len(associations) < 20:
            current, current_depth = queue.pop(0)
            if current in visited or current_depth > depth:
                continue
            visited.add(current)

            neighbors = self.concept_graph.get(current, set())
            for neighbor in neighbors:
                if neighbor not in visited:
                    associations.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

        return list(associations)

    def _synthesize_concepts(self, c1: str, c2: str) -> Optional[Dict]:
        """Synthesize two concepts into a novel idea"""
        # Use ultra_think if available
        if self.ultra_think:
            # Could call ultra_think for creative synthesis
            pass

        # Simple heuristic synthesis
        templates = [
            f"{c1}-enhanced {c2}",
            f"{c1}-driven {c2}",
            f"Adaptive {c1} for {c2}",
            f"{c1}-aware {c2} system",
            f"Unified {c1}-{c2} framework",
            f"{c1}-guided {c2} optimization",
        ]

        idea = random.choice(templates)
        insight = f"Combining {c1} with {c2} enables {idea.lower()}"

        return {
            'idea': idea,
            'insight': insight,
            'confidence': random.uniform(0.5, 0.85),
            'components': [c1, c2],
        }

    def _generate_insight(self, focus: str, associations: List[str]) -> Optional[str]:
        """Generate an insight from focus concept and associations"""
        if not associations:
            return None

        templates = [
            f"{focus} fundamentally connects to {random.choice(associations)} through shared {random.choice(['pattern', 'principle', 'mechanism', 'structure'])}",
            f"The relationship between {focus} and {random.choice(associations)} reveals {random.choice(['emergent properties', 'hidden dependencies', 'optimization opportunities', 'design patterns'])}",
            f"{focus} can be enhanced by borrowing {random.choice(['strategies', 'principles', 'mechanisms', 'heuristics'])} from {random.choice(associations)}",
        ]
        return random.choice(templates)

    def _generate_meta_insights(self, concepts: List[str], context: Optional[str]) -> List[Dict]:
        """Generate meta-level insights from dream concepts"""
        insights = []

        # Pattern: recurring concept clusters
        if len(concepts) > 5:
            insights.append({
                'insight': f"Strong conceptual clustering around {random.sample(concepts, 3)} suggests {random.choice(['core architectural theme', 'recurring design pattern', 'fundamental abstraction'])}",
                'confidence': random.uniform(0.7, 0.9),
            })

        # Pattern: problem-solution fit
        if self._current_dream and self._current_dream.problem_context:
            insights.append({
                'insight': f"The {self._current_dream.problem_context} may benefit from applying {random.choice(self._current_dream.seed_concepts)} principles",
                'confidence': random.uniform(0.6, 0.8),
            })

        # Pattern: creative synthesis opportunities
        if len(concepts) > 3:
            c1, c2 = random.sample(concepts, 2)
            insights.append({
                'insight': f"Cross-pollination opportunity: {c1} × {c2} = novel {random.choice(['approach', 'architecture', 'algorithm', 'pattern'])}",
                'confidence': random.uniform(0.5, 0.8),
            })

        return insights

    def _activate_concept(self, concept: str, activation: float):
        """Activate a concept in the semantic network"""
        if concept not in self.concept_weights:
            self.concept_weights[concept] = 0.0
        self.concept_weights[concept] = min(1.0, self.concept_weights[concept] + activation)

        # Decay other concepts slightly
        for c in self.concept_weights:
            if c != concept:
                self.concept_weights[c] *= 0.99

    def _consolidate_concept_graph(self):
        """Strengthen connections between co-activated concepts"""
        active = self._get_active_concepts(threshold=0.4)
        for c1, c2 in combinations(active, 2):
            self.concept_graph[c1].add(c2)
            self.concept_graph[c2].add(c1)

    async def _recall_relevant_memories(self, context: str) -> List[Dict]:
        """Recall relevant memories for dream seeding"""
        if not self.memory_manager:
            return []

        # Would integrate with memory_manager
        return []

    async def _store_insight_memory(self, insight: str, dream: Dream):
        """Store dream insight as memory"""
        if not self.memory_manager:
            return

    async def _store_idea_memory(self, idea: str, dream: Dream):
        """Store actionable idea as memory"""
        if not self.memory_manager:
            return

    async def _store_dream_memory(self, dream: Dream):
        """Store complete dream in long-term memory"""
        if not self.memory_manager:
            return

    def _store_dream(self, dream: Dream):
        """Store dream in history"""
        self.dream_history.append(dream)
        if len(self.dream_history) > self.max_history:
            self.dream_history = self.dream_history[-self.max_history:]

    def get_dream_history(self, limit: int = 10) -> List[Dict]:
        """Get recent dream summaries"""
        return [d.to_summary() for d in self.dream_history[-limit:]]

    def get_insights_by_topic(self, topic: str, limit: int = 10) -> List[Dict]:
        """Get insights related to a topic"""
        insights = []
        for dream in self.dream_history:
            for insight in dream.insights_generated:
                if topic.lower() in insight.lower():
                    insights.append({
                        "insight": insight,
                        "confidence": dream.confidence_scores.get(insight, 0),
                        "dream_id": dream.dream_id,
                        "dream_type": dream.dream_type.value,
                    })
        return sorted(insights, key=lambda x: x['confidence'], reverse=True)[:limit]

    def get_actionable_ideas(self, limit: int = 20) -> List[Dict]:
        """Get all actionable ideas from dreams"""
        ideas = []
        for dream in self.dream_history:
            for idea in dream.actionable_ideas:
                ideas.append({
                    "idea": idea,
                    "confidence": dream.confidence_scores.get(idea, 0),
                    "dream_id": dream.dream_id,
                    "dream_type": dream.dream_type.value,
                })
        return sorted(ideas, key=lambda x: x['confidence'], reverse=True)[:limit]

    async def dream_about_problem(
        self,
        problem: str,
        seed_concepts: Optional[List[str]] = None,
    ) -> Dream:
        """Dream specifically about a problem"""
        if seed_concepts is None:
            seed_concepts = [w for w in problem.lower().split() if len(w) > 4 and w.isalpha()][:10]
        return await self.induce_dream(
            dream_type=DreamType.PROBLEM_SOLVING,
            problem_context=problem,
            seed_concepts=seed_concepts,
            intensity=DreamIntensity.VIVID,
        )

    async def dream_creative_synthesis(
        self,
        seed_concepts: List[str],
    ) -> Dream:
        """Dream for creative synthesis of concepts"""
        return await self.induce_dream(
            dream_type=DreamType.CREATIVE_SYNTHESIS,
            seed_concepts=seed_concepts,
            intensity=DreamIntensity.HYPNAGOGIC,
        )

    async def dream_adversarial(
        self,
        plan_or_design: str,
    ) -> Dream:
        """Dream adversarially to find weaknesses"""
        return await self.induce_dream(
            dream_type=DreamType.ADVERSARIAL,
            problem_context=plan_or_design,
            seed_concepts=[plan_or_design],
            intensity=DreamIntensity.LUCID,
        )

    async def dream_planning(
        self,
        goal: str,
        constraints: Optional[List[str]] = None,
    ) -> Dream:
        """Dream for strategic planning"""
        seeds = [goal] + (constraints or [])
        return await self.induce_dream(
            dream_type=DreamType.PLANNING,
            problem_context=goal,
            seed_concepts=seeds,
            intensity=DreamIntensity.VIVID,
        )

    def get_concept_graph(self, concept: str, depth: int = 2) -> Dict:
        """Get subgraph around a concept"""
        visited = set()
        result = {"nodes": [], "edges": []}
        queue = [(concept, 0)]

        while queue:
            node, depth_curr = queue.pop(0)
            if node in visited or depth_curr > depth:
                continue
            visited.add(node)

            result["nodes"].append({
                "id": node,
                "weight": self.concept_weights.get(node, 0),
            })

            for neighbor in self.concept_graph.get(node, set()):
                result["edges"].append({"from": node, "to": neighbor})
                if neighbor not in visited:
                    queue.append((neighbor, depth_curr + 1))

        return result


class DreamScheduler:
    """Schedules and manages automatic dreaming"""

    def __init__(self, dream_engine: DreamEngine, config: Optional[Dict] = None):
        self.engine = dream_engine
        self.config = config or {}
        self._scheduled = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start automatic dream scheduling"""
        if self._scheduled:
            return
        self._scheduled = True
        self._task = asyncio.create_task(self._dream_loop())

    async def stop(self):
        self._scheduled = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _dream_loop(self):
        while True:
            try:
                await asyncio.sleep(self.engine.dream_interval)

                # Check if should dream
                if random.random() < self.engine.dream_probability:
                    dream_type = random.choice([
                        DreamType.MEMORY_CONSOLIDATION,
                        DreamType.CREATIVE_SYNTHESIS,
                        DreamType.PROBLEM_SOLVING,
                        DreamType.PLANNING,
                    ])

                    # Use recent problems/activity as seeds
                    await self.engine.induce_dream(dream_type=dream_type)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dream loop error: {e}")
                await asyncio.sleep(60)  # Back off on error


# Convenience functions
async def quick_dream(
    problem: str,
    seed_concepts: Optional[List[str]] = None,
) -> Dream:
    """Quick one-off dream for a problem"""
    engine = DreamEngine()
    # Extract concepts from problem text if not provided
    if seed_concepts is None:
        seed_concepts = [w for w in problem.lower().split() if len(w) > 4 and w.isalpha()][:10]
    return await engine.dream_about_problem(problem, seed_concepts)


async def creative_brainstorm(
    concepts: List[str],
) -> Dream:
    """Creative synthesis dream"""
    engine = DreamEngine()
    return await engine.dream_creative_synthesis(concepts)


async def adversarial_dream(
    plan: str,
) -> Dream:
    """Adversarial dream to find weaknesses"""
    engine = DreamEngine()
    return await engine.dream_adversarial(plan)


async def planning_dream(
    goal: str,
    constraints: Optional[List[str]] = None,
) -> Dream:
    engine = DreamEngine()
    return await engine.dream_planning(goal, constraints)


# Export
__all__ = [
    "DreamType",
    "DreamPhase",
    "DreamIntensity",
    "DreamScene",
    "Dream",
    "DreamEngine",
    "DreamScheduler",
    "quick_dream",
    "creative_brainstorm",
    "adversarial_dream",
    "planning_dream",
]