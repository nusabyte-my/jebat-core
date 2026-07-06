"""
♾️ JEBAT Continuum - Skill Learning System

Skills that learn and improve through Continuum cycles.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LearningCycle:
    """A learning cycle record."""

    skill_name: str
    cycle_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    executions_analyzed: int = 0
    patterns_found: List[Dict[str, Any]] = field(default_factory=list)
    improvements_applied: List[Dict[str, Any]] = field(default_factory=list)
    success_rate_before: float = 0.0
    success_rate_after: float = 0.0


class ContinuumSkillLearning:
    """
    Continuum-based Skill Learning System.

    Skills improve through continuous learning cycles:
    1. Collect executions
    2. Analyze patterns
    3. Generate improvements
    4. Apply improvements
    5. Measure results
    """

    def __init__(self, continuum, skill):
        """
        Initialize Skill Learning System.

        Args:
            continuum: JEBAT Continuum instance
            skill: Skill to improve
        """
        self.continuum = continuum
        self.skill = skill
        self.learning_cycles: List[LearningCycle] = []
        self.execution_buffer: List[Dict[str, Any]] = []
        self.cycle_threshold = 10  # Analyze after N executions

        logger.info(f"ContinuumSkillLearning initialized for: {skill.name}")

    async def record_execution(self, execution_data: Dict[str, Any]):
        """
        Record a skill execution for learning.

        Args:
            execution_data: Execution data
        """
        self.execution_buffer.append(
            {
                "timestamp": datetime.now(),
                **execution_data,
            }
        )

        # Trigger learning cycle if threshold reached
        if len(self.execution_buffer) >= self.cycle_threshold:
            await self._start_learning_cycle()

    async def _start_learning_cycle(self):
        """Start a new learning cycle."""
        cycle = LearningCycle(
            skill_name=self.skill.name,
            cycle_number=len(self.learning_cycles) + 1,
            start_time=datetime.now(),
            executions_analyzed=len(self.execution_buffer),
        )

        logger.info(
            f"Starting learning cycle {cycle.cycle_number} for {self.skill.name}"
        )

        # Analyze patterns
        cycle.patterns_found = await self._analyze_patterns()

        # Calculate success rate before
        cycle.success_rate_before = self._calculate_success_rate()

        # Generate improvements
        improvements = await self._generate_improvements(cycle.patterns_found)

        # Apply improvements
        for improvement in improvements:
            applied = await self._apply_improvement(improvement)
            if applied:
                cycle.improvements_applied.append(improvement)

        # Calculate success rate after (if possible)
        cycle.success_rate_after = self._calculate_success_rate()

        # End cycle
        cycle.end_time = datetime.now()

        # Store cycle
        self.learning_cycles.append(cycle)

        # Clear buffer
        self.execution_buffer.clear()

        logger.info(
            f"Learning cycle {cycle.cycle_number} complete: "
            f"{len(cycle.improvements_applied)} improvements applied"
        )

    async def _analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in execution buffer using Continuum."""
        if not self.execution_buffer:
            return []

        # Use Continuum for pattern analysis
        patterns = await self.continuum.analyze_cycles(
            data=self.execution_buffer,
            cycle_type="skill_execution",
        )

        # Extract meaningful patterns
        extracted = []
        for pattern in patterns:
            extracted.append(
                {
                    "type": pattern.get("type", "unknown"),
                    "description": pattern.get("description", ""),
                    "frequency": pattern.get("frequency", 0),
                    "success_correlation": pattern.get("success_correlation", 0),
                }
            )

        return extracted

    async def _generate_improvements(
        self,
        patterns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate improvements based on patterns."""
        improvements = []

        for pattern in patterns:
            # Low success rate pattern
            if pattern.get("success_correlation", 0) < 0.5:
                improvement = await self._generate_improvement_for_pattern(pattern)
                if improvement:
                    improvements.append(improvement)

        # Use Cortex for sophisticated improvements
        if self.continuum.cortex:
            cortex_improvements = await self.continuum.cortex.think(
                problem="Generate improvements for this skill based on patterns",
                context={
                    "skill": self.skill.name,
                    "patterns": patterns,
                },
                mode="creative",
            )

            if cortex_improvements.conclusion:
                improvements.extend(
                    cortex_improvements.conclusion.get("improvements", [])
                )

        return improvements

    async def _generate_improvement_for_pattern(
        self,
        pattern: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Generate improvement for a specific pattern."""
        pattern_type = pattern.get("type")

        if pattern_type == "context_mismatch":
            return {
                "type": "prompt_adjustment",
                "reason": f"Pattern: {pattern.get('description')}",
                "action": "Add context handling for edge cases",
            }

        elif pattern_type == "parameter_suboptimal":
            return {
                "type": "parameter_tuning",
                "reason": f"Pattern: {pattern.get('description')}",
                "action": "Adjust temperature or max_tokens",
            }

        elif pattern_type == "user_confusion":
            return {
                "type": "prompt_clarification",
                "reason": f"Pattern: {pattern.get('description')}",
                "action": "Add clarifying examples to prompt",
            }

        return None

    async def _apply_improvement(self, improvement: Dict[str, Any]) -> bool:
        """Apply an improvement to the skill."""
        try:
            improvement_type = improvement.get("type")

            if improvement_type == "prompt_adjustment":
                # Adjust skill prompt
                current_prompt = self.skill.base_prompt
                # Add improvement
                self.skill.base_prompt = (
                    f"{current_prompt}\n\n# Improvement: {improvement.get('action')}\n"
                )
                return True

            elif improvement_type == "parameter_tuning":
                # Tune parameters
                if "temperature" in improvement:
                    self.skill.temperature = improvement["temperature"]
                if "max_tokens" in improvement:
                    self.skill.max_tokens = improvement["max_tokens"]
                return True

            elif improvement_type == "prompt_clarification":
                # Add examples
                examples = improvement.get("examples", [])
                if examples:
                    self.skill.base_prompt += f"\n\n## Examples:\n" + "\n".join(
                        f"- {ex}" for ex in examples
                    )
                return True

        except Exception as e:
            logger.error(f"Failed to apply improvement: {e}")

        return False

    def _calculate_success_rate(self) -> float:
        """Calculate success rate from execution buffer."""
        if not self.execution_buffer:
            return 0.0

        successful = sum(
            1
            for e in self.execution_buffer
            if e.get("result", {}).get("success", False)
        )

        return successful / len(self.execution_buffer)

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self.learning_cycles:
            return {
                "total_cycles": 0,
                "total_improvements": 0,
            }

        total_improvements = sum(
            len(c.improvements_applied) for c in self.learning_cycles
        )

        avg_success_rate_before = sum(
            c.success_rate_before for c in self.learning_cycles
        ) / len(self.learning_cycles)

        avg_success_rate_after = sum(
            c.success_rate_after for c in self.learning_cycles
        ) / len(self.learning_cycles)

        return {
            "total_cycles": len(self.learning_cycles),
            "total_improvements": total_improvements,
            "avg_success_rate_before": avg_success_rate_before,
            "avg_success_rate_after": avg_success_rate_after,
            "improvement_rate": (avg_success_rate_after - avg_success_rate_before)
            / avg_success_rate_before
            if avg_success_rate_before > 0
            else 0,
        }

    async def force_learning_cycle(self):
        """Force a learning cycle regardless of threshold."""
        if self.execution_buffer:
            await self._start_learning_cycle()

    def get_recent_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent patterns from learning cycles."""
        patterns = []
        for cycle in reversed(self.learning_cycles[:limit]):
            patterns.extend(cycle.patterns_found)
        return patterns[:limit]
