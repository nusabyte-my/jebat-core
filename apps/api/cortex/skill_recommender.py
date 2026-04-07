"""
🧠 JEBAT Cortex - Skill Recommendation Engine

Recommends skills based on context analysis using Cortex reasoning.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillRecommendation:
    """A skill recommendation."""

    skill_name: str
    confidence: float
    reason: str
    relevance_score: float
    category: str


class CortexSkillRecommender:
    """
    Cortex-powered Skill Recommendation Engine.

    Analyzes context and recommends relevant skills.
    """

    def __init__(self, cortex, skill_registry):
        """
        Initialize Skill Recommender.

        Args:
            cortex: JEBAT Cortex instance
            skill_registry: SkillRegistry instance
        """
        self.cortex = cortex
        self.registry = skill_registry
        self.recommendation_history: List[Dict[str, Any]] = []

        logger.info("CortexSkillRecommender initialized")

    async def recommend(
        self,
        context: Dict[str, Any],
        limit: int = 5,
    ) -> List[SkillRecommendation]:
        """
        Recommend skills based on context.

        Args:
            context: Current context (code, conversation, etc.)
            limit: Maximum recommendations

        Returns:
            List of SkillRecommendation
        """
        # Use Cortex to analyze context
        analysis = await self.cortex.think(
            problem="What skills would help with this context?",
            context=context,
            mode="analytical",
        )

        # Extract identified needs
        needs = self._extract_needs(analysis)

        # Find matching skills
        candidate_skills = []
        for need in needs:
            matches = self.registry.search_skills(need)
            for match in matches:
                candidate_skills.append(
                    {
                        "skill": match,
                        "matched_need": need,
                    }
                )

        # Rank skills using Cortex
        ranked = await self._rank_skills(candidate_skills, context)

        # Create recommendations
        recommendations = []
        for item in ranked[:limit]:
            rec = SkillRecommendation(
                skill_name=item["skill"].name,
                confidence=item["confidence"],
                reason=item["reason"],
                relevance_score=item["relevance"],
                category=item["skill"].category,
            )
            recommendations.append(rec)

        # Store in history
        self.recommendation_history.append(
            {
                "context": context,
                "recommendations": [r.skill_name for r in recommendations],
                "timestamp": datetime.now(),
            }
        )

        return recommendations

    def _extract_needs(self, analysis) -> List[str]:
        """Extract needs from Cortex analysis."""
        needs = []

        # Try to get needs from analysis conclusion
        conclusion = analysis.conclusion
        if isinstance(conclusion, dict):
            needs = conclusion.get("needs", [])
        elif isinstance(conclusion, str):
            # Parse needs from text
            needs = self._parse_needs_from_text(conclusion)

        # Fallback to reasoning steps
        if not needs:
            needs = [
                step.strip()
                for step in analysis.reasoning_steps
                if len(step.strip()) > 10
            ][:5]

        return needs

    def _parse_needs_from_text(self, text: str) -> List[str]:
        """Parse needs from text analysis."""
        # Simple extraction - look for key phrases
        keywords = [
            "need to",
            "should",
            "requires",
            "requires",
            "optimize",
            "improve",
            "fix",
            "create",
            "implement",
        ]

        needs = []
        for line in text.split("\n"):
            line = line.strip()
            if any(kw in line.lower() for kw in keywords):
                needs.append(line)

        return needs[:5]

    async def _rank_skills(
        self,
        candidate_skills: List[Dict],
        context: Dict[str, Any],
    ) -> List[Dict]:
        """Rank candidate skills using Cortex."""
        if not candidate_skills:
            return []

        # Use Cortex to rank
        ranking = await self.cortex.think(
            problem="Rank these skills by relevance to the context",
            context={
                "candidate_skills": [
                    {"name": c["skill"].name, "description": c["skill"].description}
                    for c in candidate_skills
                ],
                "user_context": context,
            },
            mode="deliberate",
        )

        # Parse ranking from Cortex
        ranked_names = self._parse_ranking(ranking)

        # Create ranked list
        ranked = []
        for i, name in enumerate(ranked_names):
            candidate = next(
                (c for c in candidate_skills if c["skill"].name == name),
                None,
            )
            if candidate:
                ranked.append(
                    {
                        "skill": candidate["skill"],
                        "confidence": 0.95 - (i * 0.05),  # Decreasing confidence
                        "reason": f"Best match for: {candidate['matched_need']}",
                        "relevance": 0.95 - (i * 0.05),
                    }
                )

        return ranked

    def _parse_ranking(self, ranking) -> List[str]:
        """Parse skill ranking from Cortex output."""
        skill_names = []

        conclusion = ranking.conclusion
        if isinstance(conclusion, list):
            skill_names = conclusion
        elif isinstance(conclusion, str):
            # Extract skill names from text
            for line in conclusion.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract first word or quoted text as skill name
                    if '"' in line:
                        name = line.split('"')[1] if len(line.split('"')) > 1 else line
                    else:
                        name = line.split()[0] if line.split() else line
                    skill_names.append(name)

        return skill_names[:10]

    async def recommend_for_file(
        self,
        file_path: str,
        file_content: str,
        language: str,
    ) -> List[SkillRecommendation]:
        """
        Recommend skills for a specific file.

        Args:
            file_path: Path to file
            file_content: File content
            language: Programming language

        Returns:
            List of SkillRecommendation
        """
        context = {
            "file_path": file_path,
            "file_content": file_content[:2000],  # Limit content
            "language": language,
            "task": "file_analysis",
        }

        # Add language-specific skills
        language_skills = self.registry.get_skills_by_tag(language)

        # Get general recommendations
        recommendations = await self.recommend(context)

        # Add language skills with high confidence
        for skill in language_skills[:3]:
            recommendations.append(
                SkillRecommendation(
                    skill_name=skill.name,
                    confidence=0.85,
                    reason=f"Expert in {language}",
                    relevance_score=0.85,
                    category=skill.category,
                )
            )

        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return recommendations[:5]

    async def recommend_for_task(
        self,
        task_description: str,
    ) -> List[SkillRecommendation]:
        """
        Recommend skills for a task.

        Args:
            task_description: Description of task

        Returns:
            List of SkillRecommendation
        """
        context = {
            "task": task_description,
            "task_type": "development",
        }

        return await self.recommend(context, limit=5)

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get recommendation statistics."""
        if not self.recommendation_history:
            return {"total_recommendations": 0}

        # Count recommended skills
        skill_counts = {}
        for rec in self.recommendation_history:
            for skill_name in rec.get("recommendations", []):
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1

        return {
            "total_recommendations": len(self.recommendation_history),
            "most_recommended": sorted(
                skill_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }
