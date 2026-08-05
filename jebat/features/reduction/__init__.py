"""Reduction Engine package — Taming Sari synthesis layer."""

from jebat.features.reduction.engine import (
    Candidate,
    Claim,
    Conflict,
    ReductionResult,
    reduce_candidates,
)

__all__ = [
    "Candidate",
    "Claim",
    "Conflict",
    "ReductionResult",
    "reduce_candidates",
]
