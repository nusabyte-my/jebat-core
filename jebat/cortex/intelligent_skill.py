"""
🧠 JEBAT Cortex - Intelligent Skill System

Intelligent skills that adapt and learn using Cortex reasoning.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillExecution:
    """Record of a skill execution."""

    skill_name: str
    context: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    user_feedback: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class UserStyleProfile:
    """User's coding/interaction style."""

    expertise_level: str = "intermediate"  # beginner, intermediate, expert
    preferred_language: str = "english"
    code_style: str = "verbose"  # concise, verbose, balanced
    common_patterns: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)


class IntelligentSkill:
    """
    Intelligent Skill with Cortex adaptation.

    Unlike static skills, IntelligentSkills:
    - Adapt to user's style and expertise
    - Learn from each execution
    - Improve over time with Continuum
    """

    def __init__(
        self,
        name: str,
        base_prompt: str,
        cortex=None,
        memory=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Intelligent Skill.

        Args:
            name: Skill name
            base_prompt: Base system prompt
            cortex: JEBAT Cortex instance
            memory: JEBAT Memory instance
            config: Skill configuration
        """
        self.name = name
        self.base_prompt = base_prompt
        self.cortex = cortex
        self.memory = memory
        self.config = config or {}

        self.execution_history: List[SkillExecution] = []
        self.user_profiles: Dict[str, UserStyleProfile] = {}

        # Adaptation parameters
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 4096)

        logger.info(f"IntelligentSkill initialized: {name}")

    async def execute(
        self,
        context: Dict[str, Any],
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Execute skill with adaptation.

        Args:
            context: Execution context
            user_id: User identifier

        Returns:
            Execution result
        """
        start_time = datetime.now()

        # Get or create user profile
        user_profile = await self._get_user_profile(user_id)

        # Adapt prompt to user
        adapted_prompt = await self._adapt_prompt(
            base_prompt=self.base_prompt,
            user_profile=user_profile,
            context=context,
        )

        # Execute with adapted prompt
        result = await self._execute(adapted_prompt, context)

        # Record execution
        execution = SkillExecution(
            skill_name=self.name,
            context=context,
            result=result,
            timestamp=datetime.now(),
            execution_time=(datetime.now() - start_time).total_seconds(),
            tokens_used=result.get("tokens_used", 0),
        )
        self.execution_history.append(execution)

        # Store in memory if available
        if self.memory:
            await self.memory.store(
                {
                    "type": "skill_execution",
                    "skill": self.name,
                    "user": user_id,
                    "execution": execution,
                }
            )

        # Trigger learning if enough executions
        if len(self.execution_history) >= 10:
            await self._analyze_and_improve()

        return result

    async def _get_user_profile(self, user_id: str) -> UserStyleProfile:
        """Get or create user profile."""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]

        # Try to load from memory
        if self.memory:
            profile_data = await self.memory.search(
                query=f"user profile {user_id}",
                layer="semantic",
            )
            if profile_data:
                profile = UserStyleProfile(**profile_data.get("data", {}))
                self.user_profiles[user_id] = profile
                return profile

        # Create default profile
        profile = UserStyleProfile()
        self.user_profiles[user_id] = profile
        return profile

    async def _adapt_prompt(
        self,
        base_prompt: str,
        user_profile: UserStyleProfile,
        context: Dict[str, Any],
    ) -> str:
        """Adapt prompt to user's style and context."""
        adapted = base_prompt

        # Use Cortex for sophisticated adaptation
        if self.cortex:
            adaptation = await self.cortex.think(
                problem="Adapt this prompt to the user's style",
                context={
                    "base_prompt": base_prompt,
                    "user_profile": {
                        "expertise": user_profile.expertise_level,
                        "style": user_profile.code_style,
                    },
                    "context": context,
                },
                mode="deliberate",
            )
            adapted = adaptation.conclusion
        else:
            # Simple adaptation without Cortex
            if user_profile.expertise_level == "beginner":
                adapted += "\n\nExplain concepts clearly and provide examples."
            elif user_profile.expertise_level == "expert":
                adapted += "\n\nBe concise and focus on advanced patterns."

            if user_profile.code_style == "concise":
                adapted += "\n\nProvide minimal, focused code."
            elif user_profile.code_style == "verbose":
                adapted += "\n\nInclude detailed comments and explanations."

        return adapted

    async def _execute(
        self,
        prompt: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute skill with prompt and context."""
        # This would integrate with actual LLM
        # For now, return simulated result
        return {
            "success": True,
            "output": f"Executed {self.name} with adapted prompt",
            "tokens_used": 150,
        }

    async def _analyze_and_improve(self):
        """Analyze executions and improve skill."""
        if len(self.execution_history) < 10:
            return

        # Analyze patterns
        successful = [e for e in self.execution_history if e.result.get("success")]
        failed = [e for e in self.execution_history if not e.result.get("success")]

        success_rate = len(successful) / len(self.execution_history)

        logger.info(f"Skill {self.name} success rate: {success_rate:.2%}")

        # Use Cortex to identify improvement areas
        if self.cortex and success_rate < 0.8:
            analysis = await self.cortex.think(
                problem="How to improve this skill's success rate?",
                context={
                    "success_rate": success_rate,
                    "failed_executions": [
                        {"context": e.context, "result": e.result}
                        for e in failed[-5:]  # Last 5 failures
                    ],
                },
                mode="analytical",
            )

            # Apply improvements
            improvements = analysis.conclusion.get("improvements", [])
            for improvement in improvements:
                await self._apply_improvement(improvement)

    async def _apply_improvement(self, improvement: Dict[str, Any]):
        """Apply an improvement to the skill."""
        improvement_type = improvement.get("type")

        if improvement_type == "prompt_adjustment":
            # Adjust base prompt
            self.base_prompt = improvement.get("new_prompt", self.base_prompt)
            logger.info(f"Applied prompt adjustment to {self.name}")

        elif improvement_type == "parameter_tuning":
            # Tune parameters
            params = improvement.get("parameters", {})
            if "temperature" in params:
                self.temperature = params["temperature"]
            if "max_tokens" in params:
                self.max_tokens = params["max_tokens"]
            logger.info(f"Applied parameter tuning to {self.name}")

    async def collect_feedback(
        self,
        execution_index: int,
        feedback: str,
        rating: int = None,
    ):
        """Collect user feedback for an execution."""
        if 0 <= execution_index < len(self.execution_history):
            self.execution_history[execution_index].user_feedback = feedback

            if rating:
                self.execution_history[execution_index].result["rating"] = rating

            logger.info(f"Collected feedback for {self.name}: {feedback}")

    def get_stats(self) -> Dict[str, Any]:
        """Get skill execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0}

        successful = sum(1 for e in self.execution_history if e.result.get("success"))
        total = len(self.execution_history)

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_execution_time": sum(e.execution_time for e in self.execution_history)
            / total,
            "total_tokens": sum(e.tokens_used for e in self.execution_history),
        }
