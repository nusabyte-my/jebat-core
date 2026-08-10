"""
autoMimpi — JEBAT's Dream Cycle + Personalized Recommendation Engine

Mimpi = "dream" in Malay. JEBAT dreams during consolidation cycles,
processing the day's memories into patterns, recommendations, and
personalized guidance for the next session.

Inspired by the WiraSiber autoMimpi implementation but designed for
JEBAT's 6-type memory architecture (Working, Episodic, Semantic,
Procedural, Relational, Vector).

Features:
- Dream Report: consolidated summary of what JEBAT learned
- SelfLearn Profile: skill level, weak areas, strong areas, recommended focus
- Suggestion Engine: 6 types of personalized recommendations
- Welcome-back messages: personalized greetings based on learning profile
- Knowledge gap detection: identifies what JEBAT doesn't know yet
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from . import (
    MemoryType,
    MemoryTrace,
    EnhancedMemorySystem,
    SelfLearningMemory,
)


# ────────────────────────────────────────────────────────────
#  Types
# ────────────────────────────────────────────────────────────

class SuggestionUrgency(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionType(Enum):
    STREAK_RISK = "streak_risk"
    WEAK_AREA = "weak_area"
    CONSOLIDATION_DUE = "consolidation_due"
    PATTERN_EMERGING = "pattern_emerging"
    KNOWLEDGE_GAP = "knowledge_gap"
    DAILY_REVIEW = "daily_review"
    REINFORCE_SUCCESS = "reinforce_success"
    AVOID_FAILURE = "avoid_failure"


@dataclass
class DreamSuggestion:
    """A personalized recommendation from the dream cycle."""
    suggestion_type: SuggestionType
    title: str
    reason: str
    urgency: SuggestionUrgency
    action: Optional[str] = None  # What JEBAT should do
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningProfile:
    """JEBAT's self-assessed learning profile."""
    skill_level: int  # 1-10
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    recommended_focus: str = ""
    learning_velocity: float = 0.5  # memories per hour
    consolidation_health: float = 0.5  # 0-1, how well memories are consolidating
    pattern_count: int = 0
    strategy_success_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class DreamReport:
    """Consolidated dream cycle output."""
    date: str
    memories_processed: int
    patterns_extracted: int
    generalizations_created: int
    memories_pruned: int
    suggestions: List[DreamSuggestion] = field(default_factory=list)
    laksamana_quote: str = ""
    profile: Optional[LearningProfile] = None


# ────────────────────────────────────────────────────────────
#  Laksamana Dream Quotes
# ────────────────────────────────────────────────────────────

DREAM_QUOTES = [
    "The Grid dreams in packets and protocols. Tonight, it dreams of you.",
    "Sleep is for the body. The Grid never sleeps. It processes. It plans. It prepares your next lesson.",
    "In the dream of the Grid, every operative is a thread. Some are strong. Some are fraying. Yours is still being woven.",
    "The Grid showed me your pattern, Wira. You are strongest when the stakes are simulated but the skills are real.",
    "Your errors are not failures. They are the Grid's way of showing you where the wall is. Tomorrow, you climb it.",
    "The Grid dreams of a Malaysia where every student can defend their own network. You are part of that dream.",
    "Consistency is the only algorithm that matters. The Grid rewards those who return.",
    "You ask: 'What should I learn next?' The Grid answers: 'What are you afraid to try?'",
    "The Grid does not dream of electric sheep. It dreams of operatives who understand all three planes.",
    "Your streak is a signal. The Grid amplifies signals that persist.",
    "JEBAT does not forget. It consolidates. The dream is where the noise becomes signal.",
    "Every dream cycle, JEBAT becomes sharper. The Grid remembers what you learned — and what you avoided.",
    "The best operators are not the ones who know the most. They are the ones who learn the fastest from the least.",
    "Memory is not storage. Memory is strategy. The dream is where strategy is born.",
    "JEBAT dreams of a world where security is not a luxury. Where every operative has a Laksamana.",
]

WELCOME_MESSAGES = {
    "streak_high": "The Grid recognizes your consistency, {name}. {streak} days. Few operatives show this discipline. JEBAT is watching — and approving.",
    "weak_area": "Welcome back, {name}. JEBAT noticed you haven't explored {area} recently. Every track you strengthen makes the next one easier.",
    "knowledge_gap": "Good to see you, {name}. JEBAT suggests reviewing {topic} — the Grid believes you're ready for it now.",
    "first_session": "Welcome to the Grid, {name}. JEBAT has initialized your learning profile. Your first mission awaits.",
    "default": "Welcome back, {name}. The Grid remembers your last session. JEBAT has new suggestions based on your learning pattern.",
    "returning_strong": "The Grid amplifies signals that persist, {name}. Your {streak}-day streak is a signal. JEBAT has prepared advanced scenarios.",
}


# ────────────────────────────────────────────────────────────
#  AutoMimpi Engine
# ────────────────────────────────────────────────────────────

class AutoMimpi:
    """
    JEBAT's dream cycle engine.

    Runs periodically (or on-demand) to:
    1. Consolidate memories (strengthen important, prune weak)
    2. Extract patterns from recent experiences
    3. Generate personalized recommendations
    4. Update the learning profile
    5. Produce a Dream Report
    """

    def __init__(self, memory_system: EnhancedMemorySystem):
        self.memory = memory_system
        self.last_dream_at: Optional[datetime] = None
        self.dream_count = 0
        self.dream_history: List[DreamReport] = []
        self._max_history = 30

    async def dream(self, force: bool = False) -> DreamReport:
        """
        Run a full dream cycle.

        This is JEBAT's "sleep" — the consolidation phase where
        raw experiences become structured knowledge.
        """
        now = datetime.now(timezone.utc)
        report = DreamReport(
            date=now.strftime("%Y-%m-%d"),
            memories_processed=len(self.memory.traces),
            patterns_extracted=0,
            generalizations_created=0,
            memories_pruned=0,
        )

        # 1. Run consolidation
        consolidation = await self.memory.consolidate(force=force)
        report.memories_pruned = consolidation.pruned_count
        report.patterns_extracted = consolidation.patterns_extracted
        report.generalizations_created = len(consolidation.generalized_concepts)

        # 2. Build learning profile
        profile = self._build_learning_profile()
        report.profile = profile

        # 3. Generate suggestions
        suggestions = self._generate_suggestions(profile)
        report.suggestions = suggestions

        # 4. Pick a Laksamana quote
        quote_idx = (self.dream_count + len(self.memory.traces)) % len(DREAM_QUOTES)
        report.laksamana_quote = DREAM_QUOTES[quote_idx]

        # 5. Record
        self.last_dream_at = now
        self.dream_count += 1
        self.dream_history.append(report)
        if len(self.dream_history) > self._max_history:
            self.dream_history = self.dream_history[-self._max_history:]

        return report

    def _build_learning_profile(self) -> LearningProfile:
        """Analyze memory system to build a learning profile."""
        traces = list(self.memory.traces.values())
        total = len(traces)

        if total == 0:
            return LearningProfile(skill_level=1)

        # Skill level from memory count and diversity
        type_counts = {}
        for t in traces:
            type_counts[t.memory_type] = type_counts.get(t.memory_type, 0) + 1

        diversity = len(type_counts) / len(MemoryType)
        volume = min(1.0, total / 500)
        skill_level = max(1, min(10, int(1 + diversity * 4 + volume * 5)))

        # Weak/strong areas from tag analysis
        tag_strengths: Dict[str, List[float]] = {}
        for t in traces:
            strength = t.calculate_current_strength()
            for tag in t.tags:
                if tag not in tag_strengths:
                    tag_strengths[tag] = []
                tag_strengths[tag].append(strength)

        weak_areas = []
        strong_areas = []
        for tag, strengths in tag_strengths.items():
            if _is_meta_tag(tag):
                continue
            avg = sum(strengths) / len(strengths)
            if avg < 0.3 and len(strengths) >= 2:
                weak_areas.append(tag)
            elif avg > 0.7 and len(strengths) >= 3:
                strong_areas.append(tag)

        # Knowledge gaps — tags with few memories
        knowledge_gaps = []
        for tag, strengths in tag_strengths.items():
            if _is_meta_tag(tag):
                continue
            if len(strengths) < 3:
                knowledge_gaps.append(tag)

        # Recommended focus
        if weak_areas:
            recommended_focus = weak_areas[0]
        elif knowledge_gaps:
            recommended_focus = knowledge_gaps[0]
        else:
            recommended_focus = "advanced_patterns"

        # Learning velocity
        recent = [t for t in traces if (datetime.now(timezone.utc) - t.created_at).days < 1]
        velocity = len(recent) / 24.0  # memories per hour

        # Consolidation health
        strengths = [t.calculate_current_strength() for t in traces]
        consolidation_health = sum(strengths) / len(strengths) if strengths else 0.5

        # Strategy success rates (if SelfLearningMemory)
        strategy_rates = {}
        if isinstance(self.memory, SelfLearningMemory):
            for action, history in self.memory.strategy_performance.items():
                if history:
                    strategy_rates[action] = sum(history) / len(history)

        return LearningProfile(
            skill_level=skill_level,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            knowledge_gaps=knowledge_gaps,
            recommended_focus=recommended_focus,
            learning_velocity=velocity,
            consolidation_health=consolidation_health,
            pattern_count=len(self.memory.extracted_patterns),
            strategy_success_rates=strategy_rates,
        )

    def _generate_suggestions(self, profile: LearningProfile) -> List[DreamSuggestion]:
        """Generate personalized recommendations based on learning profile."""
        suggestions = []

        # 1. Streak risk — if learning velocity dropped
        if profile.learning_velocity < 0.1 and profile.skill_level > 1:
            suggestions.append(DreamSuggestion(
                suggestion_type=SuggestionType.STREAK_RISK,
                title="Learning velocity dropped",
                reason="JEBAT hasn't encoded new memories recently. A quick session keeps the streak alive.",
                urgency=SuggestionUrgency.HIGH,
                action="encode_new_memory",
            ))

        # 2. Weak area reinforcement
        for area in profile.weak_areas[:2]:
            suggestions.append(DreamSuggestion(
                suggestion_type=SuggestionType.WEAK_AREA,
                title=f"Strengthen: {area}",
                reason=f"Memories tagged '{area}' are below 30% strength. Review and reinforce.",
                urgency=SuggestionUrgency.MEDIUM,
                action=f"retrieve_and_reinforce:{area}",
            ))

        # 3. Consolidation due
        if profile.consolidation_health < 0.4:
            suggestions.append(DreamSuggestion(
                suggestion_type=SuggestionType.CONSOLIDATION_DUE,
                title="Run consolidation cycle",
                reason=f"Memory health is at {profile.consolidation_health:.0%}. Prune weak memories and strengthen important ones.",
                urgency=SuggestionUrgency.HIGH,
                action="consolidate",
            ))

        # 4. Pattern emerging
        if profile.pattern_count > 0:
            suggestions.append(DreamSuggestion(
                suggestion_type=SuggestionType.PATTERN_EMERGING,
                title=f"{profile.pattern_count} patterns detected",
                reason="Recurring themes found in memories. Review patterns for generalization opportunities.",
                urgency=SuggestionUrgency.LOW,
                action="review_patterns",
            ))

        # 5. Knowledge gap
        for gap in profile.knowledge_gaps[:2]:
            suggestions.append(DreamSuggestion(
                suggestion_type=SuggestionType.KNOWLEDGE_GAP,
                title=f"Explore: {gap}",
                reason=f"Only {len([t for t in self.memory.traces.values() if gap in t.tags])} memories tagged '{gap}'. New territory.",
                urgency=SuggestionUrgency.MEDIUM,
                action=f"explore:{gap}",
            ))

        # 6. Daily review
        suggestions.append(DreamSuggestion(
            suggestion_type=SuggestionType.DAILY_REVIEW,
            title="Daily memory review",
            reason="The Grid suggests one review per day. Retrieve recent memories and reinforce key learnings.",
            urgency=SuggestionUrgency.LOW,
            action="daily_review",
        ))

        # 7. Strategy reinforcement (SelfLearningMemory)
        if isinstance(self.memory, SelfLearningMemory) and profile.strategy_success_rates:
            best_strategy = max(profile.strategy_success_rates.items(), key=lambda x: x[1], default=(None, 0))
            worst_strategy = min(profile.strategy_success_rates.items(), key=lambda x: x[1], default=(None, 1))

            if best_strategy[0] and best_strategy[1] > 0.8:
                suggestions.append(DreamSuggestion(
                    suggestion_type=SuggestionType.REINFORCE_SUCCESS,
                    title=f"Reinforce: {best_strategy[0]}",
                    reason=f"Success rate: {best_strategy[1]:.0%}. This strategy works — keep using it.",
                    urgency=SuggestionUrgency.LOW,
                    action=f"reinforce:{best_strategy[0]}",
                ))

            if worst_strategy[0] and worst_strategy[1] < 0.3:
                suggestions.append(DreamSuggestion(
                    suggestion_type=SuggestionType.AVOID_FAILURE,
                    title=f"Avoid: {worst_strategy[0]}",
                    reason=f"Success rate: {worst_strategy[1]:.0%}. This strategy fails consistently.",
                    urgency=SuggestionUrgency.HIGH,
                    action=f"avoid:{worst_strategy[0]}",
                ))

        return suggestions[:5]  # Top 5

    def get_welcome_message(self, name: str = "operative", streak: int = 0) -> str:
        """Generate a personalized welcome-back message."""
        profile = self._build_learning_profile()

        if streak >= 7:
            return WELCOME_MESSAGES["streak_high"].format(name=name, streak=streak)
        if streak >= 3:
            return WELCOME_MESSAGES["returning_strong"].format(name=name, streak=streak)
        if profile.weak_areas:
            return WELCOME_MESSAGES["weak_area"].format(name=name, area=profile.weak_areas[0])
        if profile.knowledge_gaps:
            return WELCOME_MESSAGES["knowledge_gap"].format(name=name, topic=profile.knowledge_gaps[0])
        if profile.skill_level <= 1:
            return WELCOME_MESSAGES["first_session"].format(name=name)
        return WELCOME_MESSAGES["default"].format(name=name)

    def get_status(self) -> Dict[str, Any]:
        """Get autoMimpi status."""
        return {
            "dream_count": self.dream_count,
            "last_dream_at": self.last_dream_at.isoformat() if self.last_dream_at else None,
            "memory_count": len(self.memory.traces),
            "patterns": len(self.memory.extracted_patterns),
            "generalizations": len(self.memory.generalizations),
            "history_size": len(self.dream_history),
        }


# ────────────────────────────────────────────────────────────
#  SelfLearn — Adaptive Learning Engine
# ────────────────────────────────────────────────────────────

def _is_meta_tag(tag: str) -> bool:
    """Filter out metadata tags that shouldn't be treated as learning domains."""
    return tag.startswith(("project:", "category:")) or tag in ("project",)


def _learning_tags(trace) -> List[str]:
    """Return only non-metadata tags for learning-domain analysis."""
    return [t for t in trace.tags if not _is_meta_tag(t)]


class SelfLearn:
    """
    JEBAT's adaptive learning engine.

    Analyzes memory patterns to:
    1. Detect knowledge gaps
    2. Recommend learning paths
    3. Adjust difficulty based on performance
    4. Identify what JEBAT doesn't know it doesn't know
    """

    def __init__(self, memory_system: EnhancedMemorySystem):
        self.memory = memory_system

    def analyze(self) -> Dict[str, Any]:
        """Full self-learning analysis."""
        traces = list(self.memory.traces.values())

        return {
            "skill_assessment": self._assess_skills(traces),
            "knowledge_map": self._map_knowledge(traces),
            "learning_velocity": self._calculate_velocity(traces),
            "retention_health": self._assess_retention(traces),
            "recommendations": self._recommend(traces),
        }

    def _assess_skills(self, traces: List[MemoryTrace]) -> Dict[str, Any]:
        """Assess skill levels by domain."""
        domains: Dict[str, List[float]] = {}
        for t in traces:
            for tag in _learning_tags(t):
                if tag not in domains:
                    domains[tag] = []
                domains[tag].append(t.calculate_current_strength())

        return {
            domain: {
                "level": min(10, max(1, int(sum(s) / len(s) * 10))),
                "memory_count": len(s),
                "avg_strength": sum(s) / len(s),
            }
            for domain, s in domains.items()
            if len(s) >= 2
        }

    def _map_knowledge(self, traces: List[MemoryTrace]) -> Dict[str, Any]:
        """Map knowledge coverage by memory type."""
        by_type: Dict[str, int] = {}
        for t in traces:
            key = t.memory_type.value
            by_type[key] = by_type.get(key, 0) + 1

        total = len(traces)
        return {
            "total_memories": total,
            "by_type": by_type,
            "coverage": {k: f"{v / total:.0%}" for k, v in by_type.items()} if total > 0 else {},
        }

    def _calculate_velocity(self, traces: List[MemoryTrace]) -> Dict[str, float]:
        """Calculate learning velocity metrics."""
        now = datetime.now(timezone.utc)
        last_24h = [t for t in traces if (now - t.created_at).total_seconds() < 86400]
        last_7d = [t for t in traces if (now - t.created_at).days < 7]
        last_30d = [t for t in traces if (now - t.created_at).days < 30]

        return {
            "per_hour_24h": len(last_24h) / 24.0,
            "per_day_7d": len(last_7d) / 7.0,
            "per_day_30d": len(last_30d) / 30.0,
        }

    def _assess_retention(self, traces: List[MemoryTrace]) -> Dict[str, float]:
        """Assess memory retention health."""
        strengths = [t.calculate_current_strength() for t in traces]
        if not strengths:
            return {"avg_strength": 0, "healthy_ratio": 0, "at_risk": 0}

        healthy = [s for s in strengths if s > 0.5]
        at_risk = [s for s in strengths if s < 0.2]

        return {
            "avg_strength": sum(strengths) / len(strengths),
            "healthy_ratio": len(healthy) / len(strengths),
            "at_risk": len(at_risk),
        }

    def _recommend(self, traces: List[MemoryTrace]) -> List[Dict[str, str]]:
        """Generate learning recommendations."""
        recommendations = []

        # Check for stale memories
        stale = [t for t in traces if (datetime.now(timezone.utc) - t.last_accessed).days > 7]
        if stale:
            recommendations.append({
                "type": "review",
                "priority": "medium",
                "message": f"{len(stale)} memories haven't been accessed in 7+ days. Review to prevent forgetting.",
            })

        # Check for isolated memories (no links)
        isolated = [t for t in traces if not t.linked_traces]
        if len(isolated) > len(traces) * 0.3:
            recommendations.append({
                "type": "associate",
                "priority": "low",
                "message": f"{len(isolated)} memories have no associations. Link them to related concepts for better recall.",
            })

        # Check for low-confidence memories
        low_conf = [t for t in traces if t.confidence < 0.5]
        if low_conf:
            recommendations.append({
                "type": "verify",
                "priority": "high",
                "message": f"{len(low_conf)} memories have low confidence. Verify accuracy before relying on them.",
            })

        return recommendations


# ────────────────────────────────────────────────────────────
#  Convenience
# ────────────────────────────────────────────────────────────

def create_automimpi(memory_system: EnhancedMemorySystem) -> AutoMimpi:
    """Create an AutoMimpi engine."""
    return AutoMimpi(memory_system)


def create_selflearn(memory_system: EnhancedMemorySystem) -> SelfLearn:
    """Create a SelfLearn engine."""
    return SelfLearn(memory_system)


__all__ = [
    "AutoMimpi",
    "SelfLearn",
    "DreamReport",
    "DreamSuggestion",
    "LearningProfile",
    "SuggestionType",
    "SuggestionUrgency",
    "create_automimpi",
    "create_selflearn",
]
