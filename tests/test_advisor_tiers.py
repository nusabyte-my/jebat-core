"""Advisor tier contract tests.

The advisor routes a typed question set through up to three backends:
TypeSafe -> local model (Laya / HF pipeline) -> lexical fallback.

The Laya adapter is a boundary against an external schema that has already
shipped broken once: it read `raw[k]` and `res["answer"]` where Laya returns
`raw["answers"][k]` and `res["choice"]` / `["score"]` / `["noul"]`. Every
miss fell back to a default, so the endpoint answered with the FIRST
candidate for all input while reporting `backend: laya`. These tests pin the
schema mapping and, just as importantly, the refusal to fabricate an answer
when the envelope is not what Laya documents.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Dict

import pytest

from routers import advisor


@pytest.fixture
def isolated(monkeypatch):
    """Clear the model cache and pin a known env for one test."""
    advisor._MODEL_CACHE.clear()
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "laya")
    monkeypatch.setenv("JEBAT_ADVISOR_MODEL", "convaiinnovations/laya")
    yield advisor
    advisor._MODEL_CACHE.clear()


def _install_fake_laya(monkeypatch, predict_impl) -> None:
    """Put a stub `laya` module on sys.modules returning predict_impl()."""

    module = types.ModuleType("laya")

    class _Agent:
        def predict(self, state, questions):
            return predict_impl(state, questions)

    module.load = lambda model_id, device=None: _Agent()
    monkeypatch.setitem(sys.modules, "laya", module)


CHOICE = {
    "route": {
        "type": "Choice",
        "instructions": "Which team handles this?",
        "candidates": ["billing", "technical", "sales"],
    }
}


async def test_laya_choice_answer_is_read_from_the_choice_key(isolated, monkeypatch):
    """Laya names the winner `choice`; reading `answer` silently yields candidates[0]."""
    # Second candidate wins — deliberately NOT the first, so a regression to
    # the old default-to-first behaviour fails this test loudly.
    def predict(state, questions):
        return {
            "answers": {
                "route": {
                    "type": "choice",
                    "choice": "technical",
                    "probabilities": {"billing": 0.15, "technical": 0.70, "sales": 0.15},
                    "confidence": 0.62,
                    "action": {"act_probability": 0.9},
                }
            },
            "usage": {"input_tokens": 12, "output_tokens": 0},
        }

    _install_fake_laya(monkeypatch, predict)
    answers, backend = await isolated._decide("the app crashes on login", CHOICE)

    assert backend == "laya"
    assert answers["route"]["answer"] == "technical"
    assert answers["route"]["probabilities"]["technical"] == pytest.approx(0.70)
    assert sum(answers["route"]["probabilities"].values()) == pytest.approx(1.0, abs=0.01)


async def test_laya_choice_is_sent_as_a_criteria_dict(isolated, monkeypatch):
    """Laya's choice criteria must be {label: description}, not a bare list."""
    seen: Dict[str, Any] = {}

    def predict(state, questions):
        seen.update(questions)
        return {
            "answers": {
                "route": {
                    "type": "choice",
                    "choice": "billing",
                    "probabilities": {"billing": 1.0},
                    "confidence": 1.0,
                }
            }
        }

    _install_fake_laya(monkeypatch, predict)
    await isolated._decide("double charged, refund please", CHOICE)

    criteria = seen["route"]["criteria"]
    assert isinstance(criteria, dict), "choice criteria must be a dict of label -> description"
    assert list(criteria) == ["billing", "technical", "sales"]


async def test_laya_score_uses_expected_level_and_clamps_to_range(isolated, monkeypatch):
    """`score` is a float expected level; it must become a valid int index."""

    def predict(state, questions):
        return {
            "answers": {
                "q": {
                    "type": "score",
                    "score": 2.4,
                    "probabilities": {"0": 0.1, "1": 0.2, "2": 0.7},
                    "confidence": 0.71,
                }
            }
        }

    _install_fake_laya(monkeypatch, predict)
    answers, _ = await isolated._decide(
        "broke on day one", {"q": {"type": "Score", "instructions": "urgency", "criteria": ["a", "b", "c"]}}
    )

    assert answers["q"]["answer"] == 2
    assert isinstance(answers["q"]["answer"], int)

    # An out-of-range level from the model must not index past the criteria.
    def predict_high(state, questions):
        return {"answers": {"q": {"type": "score", "score": 99.0, "probabilities": {"0": 1.0}}}}

    _install_fake_laya(monkeypatch, predict_high)
    isolated._MODEL_CACHE.clear()
    answers, _ = await isolated._decide(
        "x", {"q": {"type": "Score", "instructions": "u", "criteria": ["a", "b", "c"]}}
    )
    assert answers["q"]["answer"] == 2


async def test_laya_noul_probability_is_read_from_the_noul_key(isolated, monkeypatch):
    def predict(state, questions):
        return {"answers": {"n": {"type": "noul", "noul": 0.83, "confidence": 0.83}}}

    _install_fake_laya(monkeypatch, predict)
    answers, _ = await isolated._decide("refund requested", {"n": {"type": "Noul", "instructions": "asked?"}})

    assert answers["n"]["probability"] == 0.83
    assert answers["n"]["answer"] is True


@pytest.mark.parametrize(
    "envelope",
    [
        {"unexpected": True},
        {"answers": {}},
        {"answers": {"route": {"type": "choice"}}},
        {"answers": {"route": {"type": "choice", "choice": "technical", "probabilities": {}}}},
    ],
    ids=["no-answers-key", "empty-answers", "missing-fields", "no-probabilities"],
)
async def test_unexpected_laya_envelope_falls_back_instead_of_guessing(
    isolated, monkeypatch, envelope
):
    """A malformed model reply must degrade to the lexical tier.

    The old adapter filled gaps with `candidates[0]`, which produced a
    confident-looking wrong answer while still claiming `backend: laya`.
    """
    _install_fake_laya(monkeypatch, lambda state, questions: envelope)
    answers, backend = await isolated._decide("the app crashes on login with a 500 error", CHOICE)

    assert backend == "local", "must not claim a model answered"
    assert answers["route"]["answer"] == "technical"


async def test_laya_failure_falls_back_when_only_laya_is_allowed(isolated, monkeypatch):
    """JEBAT_ADVISOR_BACKEND=laya with no importable laya must not invent output."""
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "laya")

    def boom(model_id, device=None):
        raise RuntimeError("weights unavailable")

    module = types.ModuleType("laya")
    module.load = boom
    monkeypatch.setitem(sys.modules, "laya", module)

    answers, backend = await isolated._decide("double charged, refund please", CHOICE)
    assert backend == "local"
    assert answers["route"]["answer"] == "billing"


@pytest.mark.parametrize(
    "pref,model,expected",
    [
        ("auto", "convaiinnovations/laya", True),
        ("auto", "typeform/distilbert-base-uncased-mnli", False),
        ("auto", None, False),
        ("auto", "", False),
        ("laya", None, True),
        ("transformers", "convaiinnovations/laya", False),
    ],
)
def test_laya_is_only_loaded_when_explicitly_intended(pref, model, expected):
    """`auto` must never reach for the 421M Laya checkpoint on its own.

    Laya measured >15 min of CPU inference for five questions on the 8-core
    API box. An unconditional auto-load means clearing JEBAT_ADVISOR_MODEL
    would hang the warm-up thread and starve the serving process, so the tier
    is gated on the model name actually naming laya (or an explicit backend).
    """
    assert advisor._wants_laya(pref, model) is expected


async def test_auto_with_non_laya_model_does_not_load_laya(isolated, monkeypatch):
    """A stray laya install plus an MNLI model name must not load Laya."""
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "auto")
    monkeypatch.setenv("JEBAT_ADVISOR_MODEL", "typeform/distilbert-base-uncased-mnli")

    def explode(model_id, device=None):  # pragma: no cover - must not run
        raise AssertionError("laya.load must not be called for a non-laya model")

    module = types.ModuleType("laya")
    module.load = explode
    monkeypatch.setitem(sys.modules, "laya", module)
    monkeypatch.setattr(advisor, "_is_transformers_available", lambda: False)

    answers, backend = await isolated._decide("double charged, refund please", CHOICE)
    assert backend == "local"
    assert answers["route"]["answer"] == "billing"


async def test_lexical_fallback_is_input_sensitive(isolated, monkeypatch):
    """The fallback must not be the old always-first-category stub."""
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "fallback")

    billing, _ = await isolated._decide("my invoice was double charged, refund please", CHOICE)
    technical, _ = await isolated._decide("the app crashes on login with a 500 error", CHOICE)

    assert billing["route"]["answer"] == "billing"
    assert technical["route"]["answer"] == "technical"
    assert sum(billing["route"]["probabilities"].values()) == pytest.approx(1.0, abs=0.01)


async def test_zero_signal_stays_uniform_and_low_confidence(isolated, monkeypatch):
    """No overlap must report uniform probabilities, never a fabricated winner."""
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "fallback")
    answers, _ = await isolated._decide("hello there", CHOICE)

    probs = answers["route"]["probabilities"]
    assert set(probs) == {"billing", "technical", "sales"}
    assert all(p == pytest.approx(1 / 3, abs=0.01) for p in probs.values())
    assert answers["route"]["confidence"] <= 0.34


async def test_shortcut_endpoints_report_the_answering_backend(isolated, monkeypatch):
    """Callers must be able to tell a model probability from a heuristic one."""
    monkeypatch.setenv("JEBAT_ADVISOR_BACKEND", "fallback")

    classified = await advisor.advisor_classify(
        advisor.ClassifyRequest(text="double charged, refund", categories=["billing", "technical", "sales"])
    )
    verified = await advisor.advisor_verify(
        advisor.VerifyRequest(text="please refund my money", claim="a refund is requested")
    )
    scored = await advisor.advisor_score(
        advisor.ScoreRequest(text="totally broken on day one", criteria=["calm", "furious"])
    )

    assert classified.backend
    assert verified.backend
    assert scored.backend
    assert 0 <= scored.score < 2
