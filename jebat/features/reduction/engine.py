"""
JEBAT Reduction Engine — the "Taming Sari" synthesis layer.

Merges multiple candidate outputs (from different agents/specialists) into a
single coherent result, scoring confidence and detecting conflicts between
structured claims. This is the top reduction layer described in the
orchestration doctrine: final reduction, conflict resolution, and merged
judgment across all agent outputs.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Claims sharing (subject, predicate) but differing on value are conflicts.
ClaimKey = Tuple[str, str]


@dataclass
class Claim:
    """A single structured assertion produced by a candidate."""

    subject: str
    predicate: str
    value: str


@dataclass
class Candidate:
    """A candidate answer from one agent/specialist."""

    source: str
    answer: str
    confidence: float
    claims: List[Claim] = field(default_factory=list)


@dataclass
class Conflict:
    """A contradiction between two candidates on the same (subject, predicate)."""

    subject: str
    predicate: str
    values: List[Tuple[str, str]]  # (source, value)


@dataclass
class ReductionResult:
    """The merged reduction output."""

    primary_source: str
    confidence: float
    synthesis: str
    conflicts: List[Conflict]
    candidates_count: int


def _claim_key(claim: Claim) -> ClaimKey:
    return (claim.subject.strip().lower(), claim.predicate.strip().lower())


def reduce_candidates(candidates: List[Candidate]) -> ReductionResult:
    """
    Reduce candidate outputs into one coherent result.

    - The highest-confidence candidate becomes the primary answer.
    - Structured claims are merged per (subject, predicate); the highest
      confidence source wins each value, and divergent values become conflicts.
    - The synthesis summarizes the chosen values and lists any conflicts.
    """
    if not candidates:
        return ReductionResult(
            primary_source="",
            confidence=0.0,
            synthesis="",
            conflicts=[],
            candidates_count=0,
        )

    ranked = sorted(candidates, key=lambda c: c.confidence, reverse=True)
    primary = ranked[0]

    best_value: dict[ClaimKey, Tuple[str, str, float]] = {}
    for cand in ranked:
        for claim in cand.claims:
            key = _claim_key(claim)
            existing = best_value.get(key)
            if existing is None or cand.confidence > existing[2]:
                best_value[key] = (claim.value, cand.source, cand.confidence)

    conflicts: List[Conflict] = []
    for cand in candidates:
        for claim in cand.claims:
            key = _claim_key(claim)
            chosen = best_value.get(key)
            if chosen is None:
                continue
            chosen_value, chosen_source, _ = chosen
            if claim.value != chosen_value and cand.source != chosen_source:
                conflicts.append(
                    Conflict(
                        subject=claim.subject,
                        predicate=claim.predicate,
                        values=[
                            (chosen_source, chosen_value),
                            (cand.source, claim.value),
                        ],
                    )
                )

    synthesis_lines = [f"Primary (from {primary.source}, conf {primary.confidence:.2f}): {primary.answer}"]
    if best_value:
        synthesis_lines.append("Merged claims:")
        for (subject, predicate), (value, source, _conf) in sorted(best_value.items()):
            synthesis_lines.append(f"  - {subject} {predicate}: {value} (via {source})")
    if conflicts:
        synthesis_lines.append("Conflicts resolved by highest confidence:")
        for c in conflicts:
            vals = "; ".join(f"{s}={v}" for s, v in c.values)
            synthesis_lines.append(f"  - {c.subject} {c.predicate}: {vals}")

    return ReductionResult(
        primary_source=primary.source,
        confidence=primary.confidence,
        synthesis="\n".join(synthesis_lines),
        conflicts=conflicts,
        candidates_count=len(candidates),
    )
