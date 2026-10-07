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
import os
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import (
    MemoryType,
    MemoryTrace,
    EnhancedMemorySystem,
    SelfLearningMemory,
    is_bookkeeping_tag,
)

MEMORY_BASE_DIR: Path = Path.home() / ".jebat" / "memory"


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def project_traces(memory: EnhancedMemorySystem, project: Optional[str] = None, project_root: Optional[str] = None) -> List[MemoryTrace]:
    """Legacy named facts remain visible; explicitly rooted facts must match."""
    root = str(Path(project_root).resolve()) if project_root else None
    return [
        trace for trace in memory.traces.values()
        if (project is None or f"project:{project}" in trace.tags)
        and (root is None or not trace.context.get("project_root") or str(Path(trace.context["project_root"]).resolve()) == root)
    ]


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
    memory_quality_avg: float = 0.5

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
    status: str = "completed"
    reason: str = ""
    analysis: Dict[str, Any] = field(default_factory=dict)


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

# ── Canonical dream state ────────────────────────────────────────────────────
# One file is authoritative: the engine persists it on every successful dream(),
# whichever entry point started the dream. The CLI session gate and the
# workspace mirror are views of it. They used to keep private counters, and the
# three files disagreed at the same moment — 68 / 52 / 2 dreams.

DREAM_STATE_FILE: Path = Path.home() / ".jebat" / "dream_state.json"

_EMPTY_DREAM_STATE: Dict[str, Any] = {
    "sessions_since_dream": 0,
    "last_dream": None,
    "dream_count": 0,
}


def load_dream_state() -> Dict[str, Any]:
    """Read the canonical dream state, tolerating both historical schemas.

    Accepts the engine schema (snake_case) and the older workspace-mirror schema
    (camelCase) so state written by either epoch still loads. Missing, corrupt,
    or non-dict state starts fresh — boot must never raise on this file.
    """
    state = dict(_EMPTY_DREAM_STATE)
    if not DREAM_STATE_FILE.exists():
        return state
    try:
        raw = json.loads(DREAM_STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Dream state load error (starting fresh): {e}")
        return state
    if not isinstance(raw, dict):
        return state

    count = raw.get("dream_count", raw.get("totalDreams"))
    if isinstance(count, int) and count >= 0:
        state["dream_count"] = count
    last = raw.get("last_dream", raw.get("lastDreamAt"))
    if isinstance(last, str) and last:
        state["last_dream"] = last
    sessions = raw.get("sessions_since_dream", raw.get("sessionsSinceDream"))
    if isinstance(sessions, int) and sessions >= 0:
        state["sessions_since_dream"] = sessions
    return state


def save_dream_state(state: Dict[str, Any]) -> None:
    """Atomically write the canonical state, stamping `updated_at`.

    Write UTF-8 to a temp file in the same directory, then os.replace. A failed
    save must never zero the file (corrupt-in-place): on error the old file stays
    untouched and the caller surfaces it. `updated_at` is stamped here so both
    the engine and the CLI keep it without having to remember.
    """
    DREAM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(state)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = DREAM_STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, DREAM_STATE_FILE)


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
        self._dream_lock = asyncio.Lock()
        self._last_scope_dream: Dict[Tuple[Optional[str], Optional[str]], datetime] = {}
        # Dream state persistence (2026-08-18): dream() previously updated
        # last_dream_at/dream_count in memory ONLY — no writer existed for
        # ~/.jebat/dream_state.json, so consecutive dreams looked "stuck"
        # (two sessions assumed persistence that no code performed). The
        # engine now owns the canonical state file: loaded here, saved
        # atomically at the end of every successful dream().
        self.state_file: Path = DREAM_STATE_FILE
        self._load_state()

    # ── Dream state persistence ─────────────────────────────────────

    def _load_state(self) -> None:
        """Restore dream counters from the canonical state file."""
        state = load_dream_state()
        self.dream_count = state["dream_count"]
        last = state.get("last_dream")
        if last:
            try:
                self.last_dream_at = datetime.fromisoformat(last.replace("Z", "+00:00"))
            except ValueError:
                pass

    def _save_state(self, sessions_since_dream: int = 0) -> None:
        """Persist dream counters to the canonical state file."""
        try:
            save_dream_state(
                {
                    "sessions_since_dream": sessions_since_dream,
                    "last_dream": (
                        self.last_dream_at.isoformat() if self.last_dream_at else None
                    ),
                    "dream_count": self.dream_count,
                }
            )
        except Exception as e:
            print(f"Dream state save error: {e}")
            raise

    async def dream(self, force: bool = False, project: Optional[str] = None, project_root: Optional[str] = None) -> DreamReport:
        """Serialize cycles, scope mutations, and record only successful consolidation."""
        async with self._dream_lock:
            now = datetime.now(timezone.utc)
            scope = (project, project_root)
            last = self._last_scope_dream.get(scope) if project is not None else self.last_dream_at
            report = DreamReport(date=now.date().isoformat(), memories_processed=0,
                                 patterns_extracted=0, generalizations_created=0, memories_pruned=0)
            if not force and last and (now - _utc(last)).total_seconds() < self.memory.consolidation_interval:
                report.status = "skipped"
                report.reason = "Consolidation interval has not elapsed"
            else:
                traces = project_traces(self.memory, project, project_root)
                ids = {trace.trace_id for trace in traces} if project is not None or project_root is not None else None
                consolidation = await self.memory.consolidate(force=force, trace_ids=ids)
                if consolidation.errors:
                    raise RuntimeError("; ".join(consolidation.errors))
                report.memories_processed = consolidation.consolidated_count
                report.memories_pruned = consolidation.pruned_count
                report.patterns_extracted = consolidation.patterns_extracted
                report.generalizations_created = len(consolidation.generalized_concepts)
            report.analysis = SelfLearn(self.memory).analyze(project, project_root)
            report.profile = self._build_learning_profile(report.analysis)
            report.suggestions = self._generate_suggestions(report.profile, report.analysis)
            quote_idx = (self.dream_count + len(self.memory.traces)) % len(DREAM_QUOTES)
            report.laksamana_quote = DREAM_QUOTES[quote_idx]
            if report.status == "completed":
                previous = (self.last_dream_at, self.dream_count)
                self.last_dream_at = now
                self.dream_count = max(self.dream_count, load_dream_state()["dream_count"]) + 1
                try:
                    self._save_state(sessions_since_dream=0)
                except Exception:
                    self.last_dream_at, self.dream_count = previous
                    raise
                self._last_scope_dream[scope] = now
                self.dream_history.append(report)
                self.dream_history = self.dream_history[-self._max_history:]
            return report

    def quality_score(self, trace: MemoryTrace) -> float:
        """Public alias for _compute_memory_quality."""
        return self._compute_memory_quality(trace)

    def _compute_memory_quality(self, trace: MemoryTrace) -> float:
        """Compute quality score for a memory trace."""
        strength = trace.calculate_current_strength()
        now = datetime.now(timezone.utc)
        created_at = trace.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        last_accessed = trace.last_accessed
        if last_accessed.tzinfo is None:
            last_accessed = last_accessed.replace(tzinfo=timezone.utc)
        access_frequency = trace.access_count / max(1, (now - created_at).days)
        recency = 1.0 / max(1, (now - last_accessed).days)
        link_bonus = min(0.2, len(trace.linked_traces) * 0.05)
        confidence = getattr(trace, "confidence", 0.8)
        return min(1.0, strength * 0.4 + min(1.0, access_frequency) * 0.2 + recency * 0.2 + confidence * 0.1 + link_bonus * 0.1)

    def record_failure(self, tool_name: str, error: str, context: str = "",
                       project: str = "", project_root: str = "") -> Tuple[MemoryTrace, List[MemoryTrace]]:
        """Each observation is distinct; identical failures survive reload deduplication."""
        from .learning_advisor import redact_learning_text

        tags = {"failure", f"tool:{tool_name}", "pattern-watch"}
        if project:
            tags.add(f"project:{project}")
        metadata = {"tool_name": tool_name, "event_id": uuid.uuid4().hex}
        if project_root:
            metadata["project_root"] = str(Path(project_root).resolve())
        trace = self.memory.store(
            content=redact_learning_text(f"Tool {tool_name} failed: {error}. Context: {context}")[:8000],
            memory_type=MemoryType.EPISODIC, tags=tags, context=metadata, confidence=0.8,
        )
        similar = [t for t in project_traces(self.memory, project or None, project_root or None)
                   if "failure" in t.tags and t.context.get("tool_name") == tool_name]
        return trace, similar

    def commit_session_learning(
        self, summary: str, key_facts: Optional[List[str]] = None,
        session_id: str = "", project: str = "", project_root: str = "",
    ) -> List[str]:
        """Deduplicate a session's durable facts and persist the batch once."""
        context = {"project_root": str(Path(project_root).resolve())} if project_root else {}
        base = {f"project:{project}"} if project else set()
        if session_id:
            base.add(f"session:{session_id}")
        entries = [(f"Session summary: {summary}", MemoryType.EPISODIC, base | {"session", "summary"}, 0.7)]
        entries.extend((f"[{project}][other] {fact}" if project else fact, MemoryType.SEMANTIC,
                        base | {"session", "fact", "project", "category:other"}, 0.8) for fact in key_facts or [])
        known = {self.memory._identity_key(trace): trace for trace in self.memory.traces.values()}
        stored, added = [], []
        for content, kind, tags, confidence in entries:
            trace = MemoryTrace(content=content.strip(), memory_type=kind, tags=tags,
                                context=dict(context), confidence=confidence,
                                decay_rate=self.memory._calculate_decay_rate(kind, 0.5))
            key = self.memory._identity_key(trace)
            if key not in known:
                self.memory._store_trace(trace)
                known[key] = trace
                added.append(trace.trace_id)
            stored.append(known[key].trace_id)
        if added:
            try:
                self.memory._save()
            except Exception:
                for trace_id in added:
                    self.memory._remove_trace(trace_id)
                raise
        return stored

    def _build_learning_profile(self, analysis: Optional[Dict[str, Any]] = None) -> LearningProfile:
        """Build the profile from the same single-pass evidence as SelfLearn."""
        analysis = analysis if analysis is not None else SelfLearn(self.memory).analyze()
        domains = analysis["domains"]
        weak = sorted((name for name, d in domains.items() if d["memory_count"] >= 2 and d["avg_strength"] < 0.3), key=lambda name: (domains[name]["avg_strength"], name))
        strong = sorted((name for name, d in domains.items() if d["memory_count"] >= 3 and d["avg_strength"] > 0.7), key=lambda name: (-domains[name]["avg_strength"], name))
        gaps = sorted(name for name, d in domains.items() if d["memory_count"] < 3)
        total = analysis["knowledge_map"]["total_memories"]
        diversity = len(analysis["knowledge_map"]["by_type"]) / len(MemoryType)
        return LearningProfile(
            skill_level=max(1, min(10, int(1 + diversity * 4 + min(1.0, total / 500) * 5))),
            weak_areas=weak, strong_areas=strong, knowledge_gaps=gaps,
            recommended_focus=(weak or gaps or ["review_verified_evidence"])[0],
            learning_velocity=analysis["learning_velocity"]["per_hour_24h"],
            consolidation_health=analysis["retention_health"]["avg_strength"],
            pattern_count=analysis["pattern_count"],
            strategy_success_rates=analysis["strategy_success_rates"],
            memory_quality_avg=analysis["quality"]["average"],
        )

    def _generate_suggestions(self, profile: LearningProfile, analysis: Optional[Dict[str, Any]] = None) -> List[DreamSuggestion]:
        """Prioritize actual evidence, not a manufactured daily-learning streak."""
        analysis = analysis if analysis is not None else SelfLearn(self.memory).analyze()
        kinds = {"recurring_failure": SuggestionType.AVOID_FAILURE, "low_confidence": SuggestionType.KNOWLEDGE_GAP,
                 "future_timestamp": SuggestionType.KNOWLEDGE_GAP, "at_risk": SuggestionType.WEAK_AREA,
                 "stale": SuggestionType.DAILY_REVIEW, "associate": SuggestionType.PATTERN_EMERGING}
        return [DreamSuggestion(
            suggestion_type=kinds[item["type"]], title=item["message"],
            reason=f"{item['evidence_count']} supporting memory record(s); verify sources before acting.",
            urgency=SuggestionUrgency(item["priority"]), action=item["action"],
            context={"evidence_ids": item["evidence_ids"], "evidence_count": item["evidence_count"]},
        ) for item in analysis["recommendations"][:5]]

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
    return is_bookkeeping_tag(tag) or tag.startswith(("session:", "tool:", "outcome:", "root:")) or tag in {"session", "summary", "fact", "failure", "success", "pattern-watch", "verified"}


def _learning_tags(trace) -> List[str]:
    """Return only non-metadata tags for learning-domain analysis."""
    return [t for t in trace.tags if not _is_meta_tag(t)]


class SelfLearn:
    """Deterministic evidence analysis; memory strength is not task competence."""

    def __init__(self, memory_system: EnhancedMemorySystem):
        self.memory = memory_system

    def analyze(self, project: Optional[str] = None, project_root: Optional[str] = None) -> Dict[str, Any]:
        traces = project_traces(self.memory, project, project_root)
        now = datetime.now(timezone.utc)
        domains: Dict[str, Dict[str, Any]] = {}
        by_type: Dict[str, int] = {}
        evidence = {"stale": [], "low_confidence": [], "at_risk": [], "isolated": [], "future_timestamp": []}
        failures: Dict[str, List[str]] = {}
        total_strength = quality_sum = 0.0
        healthy = last_24h = last_7d = last_30d = unbound = 0
        for trace in traces:
            strength = trace.calculate_current_strength()
            total_strength += strength
            healthy += strength > 0.5
            created_age = (now - _utc(trace.created_at)).total_seconds()
            accessed_age = (now - _utc(trace.last_accessed)).total_seconds()
            last_24h += 0 <= created_age < 86400
            last_7d += 0 <= created_age < 7 * 86400
            last_30d += 0 <= created_age < 30 * 86400
            unbound += not bool(trace.context.get("project_root"))
            by_type[trace.memory_type.value] = by_type.get(trace.memory_type.value, 0) + 1
            if created_age < 0 or accessed_age < 0:
                evidence["future_timestamp"].append(trace.trace_id)
            if accessed_age > 7 * 86400:
                evidence["stale"].append(trace.trace_id)
            if trace.confidence < 0.5:
                evidence["low_confidence"].append(trace.trace_id)
            if strength < 0.2:
                evidence["at_risk"].append(trace.trace_id)
            if not trace.linked_traces:
                evidence["isolated"].append(trace.trace_id)
            quality_sum += min(1.0, strength * 0.4 + min(1.0, trace.access_count / max(1, created_age / 86400)) * 0.2 + (1 / max(1, accessed_age / 86400)) * 0.2 + trace.confidence * 0.1 + min(0.2, len(trace.linked_traces) * 0.05) * 0.1)
            for tag in _learning_tags(trace):
                domain = domains.setdefault(tag, {"memory_count": 0, "strength_sum": 0.0, "evidence_ids": []})
                domain["memory_count"] += 1
                domain["strength_sum"] += strength
                if len(domain["evidence_ids"]) < 10:
                    domain["evidence_ids"].append(trace.trace_id)
            if "failure" in trace.tags:
                tool = trace.context.get("tool_name")
                if isinstance(tool, str) and tool:
                    failures.setdefault(tool, []).append(trace.trace_id)
        for domain in domains.values():
            domain["avg_strength"] = domain.pop("strength_sum") / domain["memory_count"]
            domain["level"] = min(10, max(1, int(domain["avg_strength"] * 10)))
        recommendations = []
        rules = [
            ("future_timestamp", "high", "Review future-dated evidence before using velocity estimates", "check_clock"),
            ("low_confidence", "high", "Verify low-confidence memories against their sources", "verify_sources"),
            ("at_risk", "medium", "Review weak evidence before relying on it", "review_evidence"),
            ("stale", "medium", "Revalidate stale evidence; age alone does not prove it false", "revalidate_sources"),
        ]
        for kind, priority, message, action in rules:
            ids = sorted(evidence[kind])
            if ids:
                recommendations.append({"type": kind, "priority": priority, "message": message, "action": action, "evidence_count": len(ids), "evidence_ids": ids[:10]})
        for tool, ids in sorted(failures.items()):
            if len(ids) >= 3:
                recommendations.append({"type": "recurring_failure", "priority": "high", "message": f"Review {tool} prerequisites: {len(ids)} recorded failures; no success rate inferred", "action": f"review_tool:{tool}", "evidence_count": len(ids), "evidence_ids": sorted(ids)[:10]})
        if traces and len(evidence["isolated"]) > len(traces) * 0.3:
            recommendations.append({"type": "associate", "priority": "low", "message": "Review isolated memories for genuine related evidence", "action": "review_links", "evidence_count": len(evidence["isolated"]), "evidence_ids": sorted(evidence["isolated"])[:10]})
        recommendations.sort(key=lambda item: ({"high": 0, "medium": 1, "low": 2}[item["priority"]], item["type"], item["action"]))
        selected = {trace.trace_id for trace in traces}
        patterns = sum(bool(p.get("traces")) and set(p["traces"]).issubset(selected) for p in self.memory.extracted_patterns.values())
        strategies = {}
        if project is None and isinstance(self.memory, SelfLearningMemory):
            strategies = {action: sum(history) / len(history) for action, history in self.memory.strategy_performance.items() if history}
        total = len(traces)
        return {
            "observed_at": now.isoformat(),
            "scope": {"project": project, "project_root": project_root, "legacy_unbound_count": unbound},
            "metric_basis": "memory coverage and retention, not measured task competence",
            "domains": dict(sorted(domains.items())),
            "skill_assessment": {key: value for key, value in sorted(domains.items()) if value["memory_count"] >= 2},
            "knowledge_map": {"total_memories": total, "by_type": by_type, "coverage": {key: f"{count / total:.0%}" for key, count in by_type.items()} if total else {}},
            "learning_velocity": {"per_hour_24h": last_24h / 24, "per_day_7d": last_7d / 7, "per_day_30d": last_30d / 30},
            "retention_health": {"avg_strength": total_strength / total if total else 0.0, "healthy_ratio": healthy / total if total else 0.0, "at_risk": len(evidence["at_risk"])},
            "quality": {"average": round(quality_sum / total, 3) if total else 0.0},
            "pattern_count": patterns, "strategy_success_rates": strategies,
            "evidence": {key: {"count": len(ids), "ids": sorted(ids)[:10]} for key, ids in evidence.items()},
            "recommendations": recommendations,
        }


# ────────────────────────────────────────────────────────────
#  Convenience
# ────────────────────────────────────────────────────────────

def create_automimpi(memory_system: Optional[EnhancedMemorySystem] = None) -> AutoMimpi:
    """Create an AutoMimpi engine."""
    if memory_system is None:
        memory_system = EnhancedMemorySystem(storage_path=MEMORY_BASE_DIR)
    return AutoMimpi(memory_system)


def create_selflearn(memory_system: Optional[EnhancedMemorySystem] = None) -> SelfLearn:
    """Create a SelfLearn engine."""
    if memory_system is None:
        memory_system = EnhancedMemorySystem(storage_path=MEMORY_BASE_DIR)
    return SelfLearn(memory_system)


def _enhanced_memory_store(
    self: EnhancedMemorySystem,
    content: str,
    memory_type: Any = MemoryType.EPISODIC,
    tags: Optional[Any] = None,
    confidence: float = 0.8,
    importance: float = 0.5,
    context: Optional[Dict[str, Any]] = None,
) -> MemoryTrace:
    """Store a memory trace synchronously with persistence."""
    from . import coerce_memory_type
    m_type = coerce_memory_type(memory_type)
    tag_set = set(tags) if tags else set()
    normalized_content = content.strip()
    normalized_context = context or {}
    trace = MemoryTrace(
        memory_type=m_type,
        content=normalized_content,
        context=normalized_context,
        tags=tag_set,
        importance=importance,
        confidence=confidence,
        decay_rate=self._calculate_decay_rate(m_type, importance),
    )
    self._store_trace(trace)
    self._activate_trace(trace.trace_id, activation=1.0)
    if m_type in (MemoryType.EPISODIC, MemoryType.WORKING):
        self._add_to_working_memory(trace.trace_id)
    self._save()
    return trace

if not hasattr(EnhancedMemorySystem, "store"):
    EnhancedMemorySystem.store = _enhanced_memory_store

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
    "MEMORY_BASE_DIR",
]
