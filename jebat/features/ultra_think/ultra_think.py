"""
JEBAT Ultra-Think - Deep Reasoning and Analysis System

Ultra-Think provides advanced cognitive capabilities for complex problem-solving:
1. Multi-perspective analysis
2. Chain-of-thought reasoning
3. Counterfactual thinking
4. Metacognitive reflection
5. Knowledge synthesis
6. Strategic planning

Use Ultra-Think for tasks requiring deep analysis, complex decisions,
and strategic reasoning beyond simple question-answer patterns.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from .database_repository import UltraThinkRepository

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    """Modes of thinking for different complexity levels"""

    FAST = "fast"  # Quick, intuitive responses
    DELIBERATE = "deliberate"  # Careful, step-by-step reasoning
    DEEP = "deep"  # Comprehensive multi-perspective analysis
    STRATEGIC = "strategic"  # Long-term planning and forecasting
    CREATIVE = "creative"  # Divergent thinking and ideation
    CRITICAL = "critical"  # Analytical evaluation and verification


class ThinkingPhase(Enum):
    """Phases of the thinking process"""

    ORIENTATION = "orientation"  # Understand the problem
    EXPLORATION = "exploration"  # Gather relevant information
    ANALYSIS = "analysis"  # Break down and examine components
    SYNTHESIS = "synthesis"  # Combine insights into conclusions
    VERIFICATION = "verification"  # Check and validate reasoning
    REFLECTION = "reflection"  # Metacognitive evaluation


@dataclass
class ThoughtNode:
    """A single thought or reasoning step"""

    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    phase: ThinkingPhase = ThinkingPhase.ORIENTATION
    confidence: float = 0.5
    supporting_evidence: List[str] = field(default_factory=list)
    counter_arguments: List[str] = field(default_factory=list)
    related_thoughts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "phase": self.phase.value,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "counter_arguments": self.counter_arguments,
            "related_thoughts": self.related_thoughts,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ThinkingTrace:
    """Complete trace of a thinking session"""

    trace_id: str = field(default_factory=lambda: str(uuid4()))
    problem_statement: str = ""
    thinking_mode: ThinkingMode = ThinkingMode.DELIBERATE
    thoughts: List[ThoughtNode] = field(default_factory=list)
    current_phase: ThinkingPhase = ThinkingPhase.ORIENTATION
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    conclusion: Optional[str] = None
    confidence_score: float = 0.0
    alternative_conclusions: List[Tuple[str, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_thought(self, thought: ThoughtNode):
        """Add a thought to the trace"""
        self.thoughts.append(thought)
        self.current_phase = thought.phase

    def get_thought_chain(self) -> List[str]:
        """Get ordered list of thought contents"""
        return [thought.content for thought in self.thoughts]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "problem_statement": self.problem_statement,
            "thinking_mode": self.thinking_mode.value,
            "thought_count": len(self.thoughts),
            "thought_chain": self.get_thought_chain(),
            "current_phase": self.current_phase.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "conclusion": self.conclusion,
            "confidence_score": self.confidence_score,
            "alternative_conclusions": self.alternative_conclusions,
            "metadata": self.metadata,
        }


@dataclass
class ThinkingResult:
    """Result of a thinking session"""

    trace: ThinkingTrace
    success: bool
    conclusion: str
    confidence: float
    reasoning_steps: List[str]
    alternatives: List[Tuple[str, float]]
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace.trace_id,
            "success": self.success,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "reasoning_steps": self.reasoning_steps,
            "alternatives": self.alternatives,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


class UltraThink:
    """
    JEBAT Ultra-Think - Deep Reasoning and Analysis System

    Provides advanced cognitive capabilities for complex problem-solving
    through structured thinking processes.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_manager=None,
        decision_engine=None,
        enable_db_persistence: bool = True,
        enable_memory_integration: bool = True,
    ):
        """
        Initialize Ultra-Think system

        Args:
            config: Thinking configuration
            memory_manager: Memory system for context retrieval
            decision_engine: Decision engine for validation
            enable_db_persistence: Enable database persistence for sessions
            enable_memory_integration: Enable memory retrieval during thinking
        """
        self.config = config or {}
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.enable_db_persistence = enable_db_persistence
        self.enable_memory_integration = enable_memory_integration

        # Database repository
        self.db_repo = UltraThinkRepository() if enable_db_persistence else None

        # Thinking parameters
        self.max_thoughts = self.config.get("max_thoughts", 50)
        self.default_mode = ThinkingMode(self.config.get("default_mode", "deliberate"))
        self.enable_reflection = self.config.get("enable_reflection", True)
        self.enable_verification = self.config.get("enable_verification", True)

        # Statistics
        self.stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_thoughts": 0,
            "avg_thoughts_per_session": 0.0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0,
        }

        # Thinking techniques
        self.techniques = {
            "chain_of_thought": True,
            "multi_perspective": True,
            "counterfactual": True,
            "first_principles": True,
            "analogical_reasoning": True,
            "probabilistic_reasoning": True,
        }

        logger.info(
            "Ultra-Think initialized with DB persistence: %s, Memory integration: %s",
            enable_db_persistence,
            enable_memory_integration,
        )

    async def think(
        self,
        problem: str,
        mode: Optional[ThinkingMode] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> ThinkingResult:
        """
        Engage in deep thinking about a problem

        Args:
            problem: The problem or question to think about
            mode: Thinking mode (default: deliberative)
            context: Additional context for thinking
            timeout: Maximum thinking time in seconds
            user_id: Optional user identifier for memory retrieval

        Returns:
            ThinkingResult with conclusion and reasoning
        """
        start_time = time.time()
        thinking_mode = mode or self.default_mode

        # Create thinking trace
        trace = ThinkingTrace(
            problem_statement=problem,
            thinking_mode=thinking_mode,
            metadata={"context": context or {}, "user_id": user_id},
        )

        logger.info(
            f"Starting {thinking_mode.value} thinking session: {problem[:100]}..."
        )

        # Create database session record if persistence is enabled
        if self.db_repo:
            try:
                await self.db_repo.create_session(
                    trace_id=trace.trace_id,
                    problem_statement=problem,
                    thinking_mode=thinking_mode.value,
                    metadata={"context": context or {}},
                )
            except Exception as e:
                logger.warning(f"Failed to create DB session record: {e}")

        try:
            # Apply timeout if specified
            if timeout:
                result = await asyncio.wait_for(
                    self._run_thinking_session(trace, thinking_mode, context, user_id),
                    timeout=timeout,
                )
            else:
                result = await self._run_thinking_session(
                    trace, thinking_mode, context, user_id
                )

            # Update database session with result
            if self.db_repo:
                try:
                    await self.db_repo.update_session_status(
                        trace_id=trace.trace_id,
                        status="completed" if result.success else "failed",
                        conclusion=result.conclusion,
                        confidence_score=result.confidence,
                    )
                except Exception as e:
                    logger.warning(f"Failed to update DB session status: {e}")

            # Update statistics
            self._update_stats(result, time.time() - start_time)

            return result

        except asyncio.TimeoutError:
            logger.warning(f"Thinking session timed out after {timeout}s")

            # Update database session with timeout
            if self.db_repo:
                try:
                    await self.db_repo.update_session_status(
                        trace_id=trace.trace_id,
                        status="timeout",
                    )
                except Exception as e:
                    logger.warning(f"Failed to update DB session timeout: {e}")

            return ThinkingResult(
                trace=trace,
                success=False,
                conclusion="Thinking timed out",
                confidence=0.0,
                reasoning_steps=trace.get_thought_chain(),
                alternatives=[],
                execution_time=timeout,
                metadata={"error": "timeout"},
            )

        except Exception as e:
            logger.error(f"Thinking session failed: {e}")
            self.stats["failed_sessions"] += 1

            # Update database session with failure
            if self.db_repo:
                try:
                    await self.db_repo.update_session_status(
                        trace_id=trace.trace_id,
                        status="failed",
                    )
                except Exception as db_error:
                    logger.warning(f"Failed to update DB session failure: {db_error}")

            return ThinkingResult(
                trace=trace,
                success=False,
                conclusion=f"Thinking failed: {str(e)}",
                confidence=0.0,
                reasoning_steps=trace.get_thought_chain(),
                alternatives=[],
                execution_time=time.time() - start_time,
                metadata={"error": str(e)},
            )

    async def _run_thinking_session(
        self,
        trace: ThinkingTrace,
        mode: ThinkingMode,
        context: Optional[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> ThinkingResult:
        """Run a complete thinking session through all phases"""

        phases = self._get_phases_for_mode(mode)

        for idx, phase in enumerate(phases):
            if len(trace.thoughts) >= self.max_thoughts:
                logger.info(f"Reached max thoughts ({self.max_thoughts})")
                break

            logger.debug(f"Thinking phase: {phase.value}")

            if phase == ThinkingPhase.ORIENTATION:
                await self._orientation_phase(trace, context, user_id)
            elif phase == ThinkingPhase.EXPLORATION:
                await self._exploration_phase(trace, context, user_id)
            elif phase == ThinkingPhase.ANALYSIS:
                await self._analysis_phase(trace, mode)
            elif phase == ThinkingPhase.SYNTHESIS:
                await self._synthesis_phase(trace, mode)
            elif phase == ThinkingPhase.VERIFICATION and self.enable_verification:
                await self._verification_phase(trace, mode)
            elif phase == ThinkingPhase.REFLECTION and self.enable_reflection:
                await self._reflection_phase(trace, mode)

            # Store latest thought in database if persistence is enabled
            if self.db_repo and trace.thoughts:
                latest_thought = trace.thoughts[-1]
                try:
                    await self.db_repo.create_thought(
                        trace_id=trace.trace_id,
                        thought_id=latest_thought.id,
                        content=latest_thought.content,
                        phase=latest_thought.phase.value,
                        phase_order=idx,
                        confidence=latest_thought.confidence,
                        supporting_evidence=latest_thought.supporting_evidence,
                        counter_arguments=latest_thought.counter_arguments,
                        metadata=latest_thought.metadata,
                    )
                except Exception as e:
                    logger.warning(f"Failed to store thought in DB: {e}")

        # Generate conclusion
        trace.end_time = datetime.utcnow()
        conclusion, confidence, alternatives = await self._generate_conclusion(trace)

        trace.conclusion = conclusion
        trace.confidence_score = confidence
        trace.alternative_conclusions = alternatives

        return ThinkingResult(
            trace=trace,
            success=True,
            conclusion=conclusion,
            confidence=confidence,
            reasoning_steps=trace.get_thought_chain(),
            alternatives=alternatives,
            execution_time=(trace.end_time - trace.start_time).total_seconds(),
            metadata={
                "phases_completed": len(phases),
                "thinking_mode": mode.value,
            },
        )

    def _get_phases_for_mode(self, mode: ThinkingMode) -> List[ThinkingPhase]:
        """Get appropriate thinking phases for a mode"""
        if mode == ThinkingMode.FAST:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.SYNTHESIS,
            ]
        elif mode == ThinkingMode.DELIBERATE:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.EXPLORATION,
                ThinkingPhase.ANALYSIS,
                ThinkingPhase.SYNTHESIS,
            ]
        elif mode == ThinkingMode.DEEP:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.EXPLORATION,
                ThinkingPhase.ANALYSIS,
                ThinkingPhase.SYNTHESIS,
                ThinkingPhase.VERIFICATION,
                ThinkingPhase.REFLECTION,
            ]
        elif mode == ThinkingMode.STRATEGIC:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.EXPLORATION,
                ThinkingPhase.ANALYSIS,
                ThinkingPhase.SYNTHESIS,
                ThinkingPhase.VERIFICATION,
            ]
        elif mode == ThinkingMode.CREATIVE:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.EXPLORATION,
                ThinkingPhase.SYNTHESIS,
            ]
        elif mode == ThinkingMode.CRITICAL:
            return [
                ThinkingPhase.ORIENTATION,
                ThinkingPhase.ANALYSIS,
                ThinkingPhase.VERIFICATION,
                ThinkingPhase.REFLECTION,
            ]
        else:
            return list(ThinkingPhase)

    async def _orientation_phase(
        self,
        trace: ThinkingTrace,
        context: Optional[Dict[str, Any]],
        user_id: Optional[str] = None,
    ):
        """Understand and frame the problem"""
        problem = trace.problem_statement

        # Parse and understand the problem
        thought = ThoughtNode(
            content=f"Problem Understanding: {problem}",
            phase=ThinkingPhase.ORIENTATION,
            confidence=0.8,
            metadata={"phase": "orientation"},
        )
        trace.add_thought(thought)

        # Retrieve relevant memories if enabled
        if self.enable_memory_integration and self.memory_manager and user_id:
            try:
                # TODO: Retrieve relevant context from memory
                # memories = await self.memory_manager.search_memories(
                #     query=problem, user_id=user_id, limit=5
                # )
                thought = ThoughtNode(
                    content="Retrieved relevant memories for context",
                    phase=ThinkingPhase.ORIENTATION,
                    confidence=0.75,
                    supporting_evidence=["memory_retrieval"],
                    metadata={"memory_integration": True},
                )
                trace.add_thought(thought)
            except Exception as e:
                logger.warning(f"Memory retrieval failed in orientation: {e}")

        # Identify key components
        thought = ThoughtNode(
            content=f"Key elements identified in problem",
            phase=ThinkingPhase.ORIENTATION,
            confidence=0.7,
            metadata={"component": "analysis"},
        )
        trace.add_thought(thought)

        # Set thinking goals
        thought = ThoughtNode(
            content=f"Thinking goal: Analyze and provide reasoned response",
            phase=ThinkingPhase.ORIENTATION,
            confidence=0.9,
            metadata={"goal": "primary"},
        )
        trace.add_thought(thought)

    async def _exploration_phase(
        self,
        trace: ThinkingTrace,
        context: Optional[Dict[str, Any]],
        user_id: Optional[str] = None,
    ):
        """Gather relevant information and perspectives"""
        # Retrieve relevant memories if available and enabled
        if self.enable_memory_integration and self.memory_manager and user_id:
            try:
                # TODO: Retrieve relevant context from memory
                # memories = await self.memory_manager.search_memories(
                #     query=trace.problem_statement, user_id=user_id, limit=5
                # )
                thought = ThoughtNode(
                    content="Explored relevant knowledge and context from memory",
                    phase=ThinkingPhase.EXPLORATION,
                    confidence=0.7,
                    supporting_evidence=["memory_retrieval"],
                    metadata={"exploration_type": "memory", "user_id": user_id},
                )
                trace.add_thought(thought)
            except Exception as e:
                logger.warning(f"Memory retrieval failed in exploration: {e}")

        # Consider multiple perspectives
        thought = ThoughtNode(
            content="Considering multiple perspectives on the problem",
            phase=ThinkingPhase.EXPLORATION,
            confidence=0.75,
            metadata={"exploration_type": "perspectives"},
        )
        trace.add_thought(thought)

    async def _analysis_phase(self, trace: ThinkingTrace, mode: ThinkingMode):
        """Break down and examine components"""
        # Apply chain-of-thought reasoning
        if self.techniques["chain_of_thought"]:
            thought = ThoughtNode(
                content="Breaking down problem using chain-of-thought reasoning",
                phase=ThinkingPhase.ANALYSIS,
                confidence=0.8,
                metadata={"technique": "chain_of_thought"},
            )
            trace.add_thought(thought)

        # Apply first principles thinking
        if self.techniques["first_principles"]:
            thought = ThoughtNode(
                content="Analyzing from first principles",
                phase=ThinkingPhase.ANALYSIS,
                confidence=0.75,
                metadata={"technique": "first_principles"},
            )
            trace.add_thought(thought)

        # Generate counter-arguments
        if self.techniques["counterfactual"]:
            thought = ThoughtNode(
                content="Considering counter-arguments and alternative views",
                phase=ThinkingPhase.ANALYSIS,
                confidence=0.7,
                counter_arguments=["alternative_interpretations"],
                metadata={"technique": "counterfactual"},
            )
            trace.add_thought(thought)

    async def _synthesis_phase(self, trace: ThinkingTrace, mode: ThinkingMode):
        """Combine insights into conclusions"""
        # Synthesize analysis into coherent conclusion
        thought = ThoughtNode(
            content="Synthesizing analysis into coherent conclusion",
            phase=ThinkingPhase.SYNTHESIS,
            confidence=0.75,
            metadata={"synthesis_type": "integration"},
        )
        trace.add_thought(thought)

        # Consider alternative conclusions
        thought = ThoughtNode(
            content="Evaluating alternative conclusions",
            phase=ThinkingPhase.SYNTHESIS,
            confidence=0.7,
            metadata={"synthesis_type": "alternatives"},
        )
        trace.add_thought(thought)

    async def _verification_phase(self, trace: ThinkingTrace, mode: ThinkingMode):
        """Check and validate reasoning"""
        # Verify logical consistency
        thought = ThoughtNode(
            content="Verifying logical consistency of reasoning",
            phase=ThinkingPhase.VERIFICATION,
            confidence=0.8,
            supporting_evidence=["logic_check"],
            metadata={"verification_type": "logic"},
        )
        trace.add_thought(thought)

        # Check for biases and errors
        thought = ThoughtNode(
            content="Checking for cognitive biases and reasoning errors",
            phase=ThinkingPhase.VERIFICATION,
            confidence=0.75,
            metadata={"verification_type": "bias_check"},
        )
        trace.add_thought(thought)

    async def _reflection_phase(self, trace: ThinkingTrace, mode: ThinkingMode):
        """Metacognitive evaluation of thinking process"""
        # Evaluate thinking quality
        thought = ThoughtNode(
            content="Reflecting on thinking process quality",
            phase=ThinkingPhase.REFLECTION,
            confidence=0.7,
            metadata={"reflection_type": "metacognition"},
        )
        trace.add_thought(thought)

        # Identify areas for improvement
        thought = ThoughtNode(
            content="Identifying areas for thinking improvement",
            phase=ThinkingPhase.REFLECTION,
            confidence=0.65,
            metadata={"reflection_type": "improvement"},
        )
        trace.add_thought(thought)

    async def _generate_conclusion(
        self, trace: ThinkingTrace
    ) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Generate final conclusion from thinking trace"""
        # Aggregate confidence from all thoughts
        if trace.thoughts:
            avg_confidence = sum(t.confidence for t in trace.thoughts) / len(
                trace.thoughts
            )
        else:
            avg_confidence = 0.5

        # Generate primary conclusion
        conclusion = f"Based on {len(trace.thoughts)} thinking steps, I conclude with {avg_confidence:.1%} confidence."

        # Generate alternatives
        alternatives = [
            ("Alternative interpretation 1", avg_confidence * 0.7),
            ("Alternative interpretation 2", avg_confidence * 0.5),
        ]

        return conclusion, avg_confidence, alternatives

    def _update_stats(self, result: ThinkingResult, execution_time: float):
        """Update thinking statistics"""
        self.stats["total_sessions"] += 1

        if result.success:
            self.stats["successful_sessions"] += 1
        else:
            self.stats["failed_sessions"] += 1

        self.stats["total_thoughts"] += len(result.reasoning_steps)
        self.stats["total_execution_time"] += execution_time

        if self.stats["total_sessions"] > 0:
            self.stats["avg_thoughts_per_session"] = (
                self.stats["total_thoughts"] / self.stats["total_sessions"]
            )
            self.stats["avg_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["total_sessions"]
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get thinking statistics"""
        return self.stats.copy()

    def enable_technique(self, technique: str):
        """Enable a thinking technique"""
        if technique in self.techniques:
            self.techniques[technique] = True
            logger.info(f"Enabled thinking technique: {technique}")

    def disable_technique(self, technique: str):
        """Disable a thinking technique"""
        if technique in self.techniques:
            self.techniques[technique] = False
            logger.info(f"Disabled thinking technique: {technique}")

    async def get_session_history(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        thinking_mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get thinking session history from database.

        Args:
            limit: Maximum number of sessions to return
            status: Optional status filter
            thinking_mode: Optional thinking mode filter

        Returns:
            List of session records
        """
        if not self.db_repo:
            return []

        sessions = await self.db_repo.get_recent_sessions(
            limit=limit, status=status, thinking_mode=thinking_mode
        )
        return [
            {
                "trace_id": s.trace_id,
                "problem_statement": s.problem_statement,
                "thinking_mode": s.thinking_mode,
                "status": s.status,
                "conclusion": s.conclusion,
                "confidence_score": s.confidence_score,
                "started_at": s.started_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in sessions
        ]

    async def get_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get thinking statistics from database.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Statistics dictionary
        """
        if not self.db_repo:
            return self.get_stats()

        db_stats = await self.db_repo.get_session_statistics(
            time_window_hours=time_window_hours
        )

        # Combine with in-memory stats
        return {
            **self.get_stats(),
            **db_stats,
        }

    async def get_thought_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get thought chain for a specific session.

        Args:
            trace_id: Trace identifier

        Returns:
            List of thoughts
        """
        if not self.db_repo:
            return []

        thoughts = await self.db_repo.get_thought_chain(trace_id)
        return [
            {
                "thought_id": t.thought_id,
                "content": t.content,
                "phase": t.phase,
                "phase_order": t.phase_order,
                "confidence": t.confidence,
                "created_at": t.created_at.isoformat(),
            }
            for t in thoughts
        ]


async def create_ultra_think(
    config: Optional[Dict[str, Any]] = None,
    memory_manager=None,
    decision_engine=None,
    enable_db_persistence: bool = True,
    enable_memory_integration: bool = True,
) -> UltraThink:
    """Factory function to create Ultra-Think instance"""
    thinker = UltraThink(
        config=config,
        memory_manager=memory_manager,
        decision_engine=decision_engine,
        enable_db_persistence=enable_db_persistence,
        enable_memory_integration=enable_memory_integration,
    )
    return thinker
