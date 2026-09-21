"""Advisor endpoint — Jev-style System One typed decisions.

Fast classify/route/score/verify without LLM prose generation.
Accepts unstructured state + typed questions, returns typed answers
with calibrated probabilities.

See docs/JEV_CONTEXT.md for integration rationale.
"""

from __future__ import annotations

import logging
import os
import time
from enum import Enum
from typing import Any, Dict, List, Literal, Union

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

# TypeSafe Jev endpoint — falls back to local heuristic if unset
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")


# ── Request / Response Models ──


class QuestionType(str, Enum):
    """Supported typed-decision question types."""

    NOUL = "Noul"       # Boolean — yes/no with probability
    CHOICE = "Choice"   # Pick one from candidates
    SCORE = "Score"     # Rate on a scale


class NoulQuestion(BaseModel):
    """Boolean verification question."""

    type: Literal["Noul"] = "Noul"
    instructions: str = Field(default="", description="What to evaluate")


class ChoiceQuestion(BaseModel):
    """Pick-one classification question."""

    type: Literal["Choice"] = "Choice"
    instructions: str = Field(default="", description="What to evaluate")
    candidates: List[str] = Field(..., min_length=2, max_length=255)


class ScoreQuestion(BaseModel):
    """Rating on a scale question."""

    type: Literal["Score"] = "Score"
    instructions: str = Field(default="", description="What to evaluate")
    criteria: List[str] = Field(..., min_length=2, description="Scale levels low→high")


class AdvisorRequest(BaseModel):
    """Jev-compatible typed decision request."""

    state: str = Field(..., min_length=1, max_length=128000,
                       description="Unstructured context/state to judge")
    questions: Dict[str, Union[NoulQuestion, ChoiceQuestion, ScoreQuestion]] = Field(
        ..., min_length=1, description="Named typed questions to answer in parallel")


class NoulAnswer(BaseModel):
    answer: bool
    probability: float


class ChoiceAnswer(BaseModel):
    answer: str
    probabilities: Dict[str, float]
    confidence: float


class ScoreAnswer(BaseModel):
    answer: int
    probabilities: Dict[str, float]
    confidence: float


class AdvisorResponse(BaseModel):
    answers: Dict[str, Any]
    latency_ms: float
    backend: str = Field(description="'typesafe' or 'local'")


# ── Shortcuts ──


class ClassifyRequest(BaseModel):
    """Shortcut: classify text into one of N categories."""

    text: str = Field(..., min_length=1)
    categories: List[str] = Field(..., min_length=2, max_length=255)
    instructions: str = Field(default="Classify this text into the most fitting category.")


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float


class VerifyRequest(BaseModel):
    """Shortcut: yes/no verification."""

    text: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1, description="The claim to verify")


class VerifyResponse(BaseModel):
    result: bool
    probability: float
    latency_ms: float


class ScoreRequest(BaseModel):
    """Shortcut: score text on a scale."""

    text: str = Field(..., min_length=1)
    criteria: List[str] = Field(..., min_length=2, description="Scale levels low→high")
    instructions: str = Field(default="Rate this text on the given scale.")


class ScoreResponse(BaseModel):
    score: int
    level: str
    confidence: float
    latency_ms: float


# ── Core logic ──


async def _call_typesafe(state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
    """Call TypeSafe Jev /v1/systemone endpoint."""
    headers = {
        "Authorization": f"Bearer {TYPESAFE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"state": state, "questions": questions}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{TYPESAFE_BASE_URL}/v1/systemone",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


def _local_fallback(state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
    """Simple heuristic fallback when no TypeSafe API key is configured.

    Returns uniform probabilities — useful for development/testing only.
    """
    answers = {}
    for key, q in questions.items():
        qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
        if qtype == "Noul":
            answers[key] = {"answer": True, "probability": 0.5}
        elif qtype == "Choice":
            candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
            n = len(candidates) or 1
            answers[key] = {
                "answer": candidates[0] if candidates else "unknown",
                "probabilities": {c: 1.0 / n for c in candidates},
                "confidence": 1.0 / n,
            }
        elif qtype == "Score":
            criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
            n = len(criteria) or 1
            answers[key] = {
                "answer": 0,
                "probabilities": {str(i): 1.0 / n for i in range(n)},
                "confidence": 1.0 / n,
            }
    return answers


async def _decide(state: str, questions: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """Route to TypeSafe or local fallback."""
    if TYPESAFE_API_KEY:
        try:
            result = await _call_typesafe(state, questions)
            return result.get("answers", result), "typesafe"
        except Exception as exc:
            logger.warning("TypeSafe API call failed, falling back to local: %s", exc)

    return _local_fallback(state, questions), "local"


# ── Endpoints ──


@router.post("", response_model=AdvisorResponse)
async def advisor_decide(req: AdvisorRequest) -> AdvisorResponse:
    """Full typed-decision endpoint — Jev-compatible.

    Send unstructured state + typed questions, get typed answers
    with calibrated probabilities in a single parallel pass.
    """
    t0 = time.perf_counter()
    # Serialize questions to dict form
    q_dict = {}
    for key, q in req.questions.items():
        q_dict[key] = q.model_dump()

    answers, backend = await _decide(req.state, q_dict)
    latency = (time.perf_counter() - t0) * 1000

    return AdvisorResponse(answers=answers, latency_ms=round(latency, 1), backend=backend)


@router.post("/classify", response_model=ClassifyResponse)
async def advisor_classify(req: ClassifyRequest) -> ClassifyResponse:
    """Shortcut: classify text into one category."""
    t0 = time.perf_counter()
    questions = {
        "category": {
            "type": "Choice",
            "instructions": req.instructions,
            "candidates": req.categories,
        }
    }
    answers, _ = await _decide(req.text, questions)
    result = answers.get("category", {})
    latency = (time.perf_counter() - t0) * 1000

    return ClassifyResponse(
        category=result.get("answer", "unknown"),
        confidence=result.get("confidence", 0.0),
        probabilities=result.get("probabilities", {}),
        latency_ms=round(latency, 1),
    )


@router.post("/verify", response_model=VerifyResponse)
async def advisor_verify(req: VerifyRequest) -> VerifyResponse:
    """Shortcut: yes/no verification of a claim against text."""
    t0 = time.perf_counter()
    questions = {
        "check": {
            "type": "Noul",
            "instructions": req.claim,
        }
    }
    answers, _ = await _decide(req.text, questions)
    result = answers.get("check", {})
    latency = (time.perf_counter() - t0) * 1000

    return VerifyResponse(
        result=result.get("answer", False),
        probability=result.get("probability", 0.5),
        latency_ms=round(latency, 1),
    )


@router.post("/score", response_model=ScoreResponse)
async def advisor_score(req: ScoreRequest) -> ScoreResponse:
    """Shortcut: rate text on a scale."""
    t0 = time.perf_counter()
    questions = {
        "rating": {
            "type": "Score",
            "instructions": req.instructions,
            "criteria": req.criteria,
        }
    }
    answers, _ = await _decide(req.text, questions)
    result = answers.get("rating", {})
    score_idx = result.get("answer", 0)
    latency = (time.perf_counter() - t0) * 1000

    return ScoreResponse(
        score=score_idx,
        level=req.criteria[score_idx] if score_idx < len(req.criteria) else "unknown",
        confidence=result.get("confidence", 0.0),
        latency_ms=round(latency, 1),
    )


@router.get("/status")
async def advisor_status() -> Dict[str, Any]:
    """Check advisor backend availability."""
    return {
        "backend": "typesafe" if TYPESAFE_API_KEY else "local_fallback",
        "typesafe_configured": bool(TYPESAFE_API_KEY),
        "base_url": TYPESAFE_BASE_URL if TYPESAFE_API_KEY else None,
        "capabilities": ["classify", "route", "score", "verify", "gate", "triage"],
        "question_types": ["Noul", "Choice", "Score"],
    }
