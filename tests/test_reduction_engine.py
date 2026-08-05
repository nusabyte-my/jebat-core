"""Unit tests for the Reduction Engine (Taming Sari synthesis layer)."""

import pytest

from jebat.features.reduction import (
    Candidate,
    Claim,
    Conflict,
    reduce_candidates,
)

pytestmark = pytest.mark.unit


def _c(source, answer, confidence, claims=None):
    return Candidate(source=source, answer=answer, confidence=confidence, claims=claims or [])


def test_empty_candidates():
    res = reduce_candidates([])
    assert res.candidates_count == 0
    assert res.primary_source == ""
    assert res.confidence == 0.0


def test_picks_highest_confidence_primary():
    res = reduce_candidates([
        _c("low", "A", 0.3),
        _c("high", "B", 0.9),
        _c("mid", "C", 0.6),
    ])
    assert res.primary_source == "high"
    assert res.confidence == 0.9
    assert "B" in res.synthesis


def test_merges_claims_by_highest_confidence():
    res = reduce_candidates([
        _c("a", "ans-a", 0.4, [Claim("weather", "is", "sunny")]),
        _c("b", "ans-b", 0.8, [Claim("weather", "is", "rainy")]),
    ])
    assert res.candidates_count == 2
    # b (higher confidence) wins weather/is, and the divergence is a conflict
    assert "rainy (via b)" in res.synthesis
    assert len(res.conflicts) == 1
    assert res.conflicts[0].values[0] == ("b", "rainy")


def test_detects_conflict_between_divergent_claims():
    res = reduce_candidates([
        _c("a", "ans-a", 0.9, [Claim("status", "equals", "ready")]),
        _c("b", "ans-b", 0.5, [Claim("status", "equals", "blocked")]),
    ])
    assert len(res.conflicts) == 1
    c: Conflict = res.conflicts[0]
    assert c.subject == "status"
    assert c.predicate == "equals"
    # highest confidence (a) wins
    assert c.values[0][0] == "a" and c.values[0][1] == "ready"
    assert c.values[1][0] == "b" and c.values[1][1] == "blocked"


def test_no_conflict_when_claims_agree():
    res = reduce_candidates([
        _c("a", "ans-a", 0.7, [Claim("port", "is", "443")]),
        _c("b", "ans-b", 0.6, [Claim("port", "is", "443")]),
    ])
    assert res.conflicts == []


def test_case_insensitive_claim_keys():
    res = reduce_candidates([
        _c("a", "ans-a", 0.9, [Claim("Host", "IS", "up")]),
        _c("b", "ans-b", 0.4, [Claim("host", "is", "down")]),
    ])
    assert len(res.conflicts) == 1
