"""Advisor endpoint — Jev-style System One typed decisions.

Fast classify/route/score/verify without LLM prose generation.
Accepts unstructured state + typed questions, returns typed answers
with calibrated probabilities.

Supports three backend tiers:
1. TypeSafe Jev API (if TYPESAFE_API_KEY is configured)
2. Local Transformer backend (Laya / ModernBERT sequence-classification via transformers)
3. Deterministic lexical heuristic fallback (zero external ML dependencies)

See docs/JEV_CONTEXT.md for integration rationale.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import re
import threading
import time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

# TypeSafe Jev endpoint — falls back to local heuristic if unset
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")

# Module-level model cache and lock for local transformer/laya models
_MODEL_CACHE: Dict[str, Any] = {}
_MODEL_LOCK = threading.Lock()


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
    backend: str = Field(description="'typesafe', 'laya', 'transformers', or 'local'")


# ── Shortcuts ──


class ClassifyRequest(BaseModel):
    """Shortcut: classify text into one of N categories."""

    text: str = Field(..., min_length=1)
    categories: List[str] = Field(..., min_length=2, max_length=255)
    instructions: str = Field(
        default="Which single category best describes the situation described in the text?",
        description="Zero-shot hypothesis framing. Specific instructions materially "
        "improve accuracy on the NLI-based transformer tier.",
    )


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
    backend: str = Field(description="'typesafe', 'laya', 'transformers', or 'local'")


class VerifyRequest(BaseModel):
    """Shortcut: yes/no verification."""

    text: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1, description="The claim to verify")


class VerifyResponse(BaseModel):
    result: bool
    probability: float
    latency_ms: float
    backend: str = Field(description="'typesafe', 'laya', 'transformers', or 'local'")


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
    backend: str = Field(description="'typesafe', 'laya', 'transformers', or 'local'")


# ── Heuristic Fallback Support ──

_DOMAIN_KEYWORDS: Dict[str, set[str]] = {
    "billing": {
        "invoice", "bill", "billing", "billed", "charge", "charged", "charging",
        "refund", "payment", "pay", "paid", "cost", "fee", "fees", "receipt",
        "subscription", "price", "pricing", "credit", "card", "stripe", "transaction", "double"
    },
    "technical": {
        "tech", "crash", "crashes", "crashed", "crashing", "error", "errors", "500",
        "404", "bug", "bugs", "fail", "failed", "failing", "failure", "broken",
        "issue", "issues", "exception", "glitch", "stack", "trace", "timeout",
        "login", "auth", "server", "code", "app", "database", "down"
    },
    "sales": {
        "sale", "sales", "buy", "buying", "bought", "purchase", "quote", "demo",
        "pricing", "enterprise", "discount", "lead", "leads", "deal", "pitch",
        "upgrade", "tier", "plan", "contact", "talk"
    },
    "safe": {
        "safe", "read", "get", "fetch", "list", "show", "inspect", "check", "view",
        "query", "status", "info", "help", "preview"
    },
    "risky": {
        "risk", "risky", "update", "modify", "patch", "edit", "change", "write",
        "restart", "deploy", "sync", "upload"
    },
    "dangerous": {
        "danger", "dangerous", "delete", "drop", "destroy", "truncate", "purge",
        "rm", "kill", "remove", "wipe", "uninstall", "terminate", "format"
    },
}


def _tokenize(text: str) -> List[str]:
    """Extract alphanumeric tokens from text."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _score_candidate(candidate: str, state_lower: str, state_tokens: set[str], state_token_list: List[str]) -> float:
    """Score a candidate string against state text using lexical and domain heuristics."""
    c_lower = candidate.lower().strip()
    score = 0.0

    # 1. Verbatim appearance boost
    if c_lower in state_lower:
        score += 3.0

    # 2. Token overlap and stem matching
    c_tokens = _tokenize(c_lower)
    for ct in c_tokens:
        if ct in state_tokens:
            score += 2.0
        elif len(ct) >= 4:
            prefix = ct[:4]
            if any(st.startswith(prefix) for st in state_tokens):
                score += 1.5

    # 3. Domain keyword expansion
    for key, kw_set in _DOMAIN_KEYWORDS.items():
        if c_lower == key or any(ct == key or (len(ct) >= 4 and ct.startswith(key[:4])) for ct in c_tokens):
            matches = kw_set.intersection(state_tokens)
            score += 1.0 * len(matches)

    return score


def _softmax_probs(scores: List[float], candidates: List[str]) -> Tuple[str, Dict[str, float], float]:
    """Convert scores to normalized probabilities and confidence."""
    n = len(candidates)
    if n == 0:
        return "unknown", {}, 0.0

    max_s = max(scores)
    if max_s <= 0.0:
        # Zero signal -> uniform distribution
        u = round(1.0 / n, 4)
        probs = {c: u for c in candidates}
        diff = round(1.0 - sum(probs.values()), 4)
        probs[candidates[-1]] = round(probs[candidates[-1]] + diff, 4)
        return candidates[0], probs, round(1.0 / n, 4)

    exp_scores = [math.exp(s - max_s) for s in scores]
    sum_exp = sum(exp_scores)
    raw_probs = [s / sum_exp for s in exp_scores]

    best_idx = int(max(range(n), key=lambda i: (scores[i], raw_probs[i])))
    best_cand = candidates[best_idx]

    probs = {c: round(p, 4) for c, p in zip(candidates, raw_probs)}
    diff = round(1.0 - sum(probs.values()), 4)
    probs[best_cand] = round(probs[best_cand] + diff, 4)

    conf = min(0.85, round(probs[best_cand], 4))
    return best_cand, probs, conf


def _eval_score(state_lower: str, s_tokens: set[str], s_list: List[str], criteria: List[str]) -> Tuple[int, Dict[str, float], float]:
    """Score criteria on a scale."""
    n = len(criteria)
    if n == 0:
        return 0, {}, 0.0

    scores = [_score_candidate(c, state_lower, s_tokens, s_list) for c in criteria]
    max_s = max(scores)
    if max_s <= 0.0:
        u = round(1.0 / n, 4)
        probs = {str(i): u for i in range(n)}
        diff = round(1.0 - sum(probs.values()), 4)
        probs[str(n - 1)] = round(probs[str(n - 1)] + diff, 4)
        return 0, probs, round(1.0 / n, 4)

    exp_scores = [math.exp(s - max_s) for s in scores]
    sum_exp = sum(exp_scores)
    raw_probs = [s / sum_exp for s in exp_scores]
    best_idx = int(max(range(n), key=lambda i: (scores[i], raw_probs[i])))
    probs = {str(i): round(p, 4) for i, p in enumerate(raw_probs)}
    diff = round(1.0 - sum(probs.values()), 4)
    probs[str(best_idx)] = round(probs[str(best_idx)] + diff, 4)
    conf = min(0.85, round(probs[str(best_idx)], 4))
    return best_idx, probs, conf


def _eval_noul(state_lower: str, s_tokens: set[str], instructions: str) -> Tuple[bool, float]:
    """Evaluate boolean question via lexical overlap and polarity."""
    stop_words = {"is", "are", "the", "a", "an", "this", "that", "it", "to", "in", "on", "for", "of", "and", "or", "what"}
    i_tokens = set(_tokenize(instructions))
    sig_claim = i_tokens - stop_words
    if not sig_claim:
        return True, 0.5

    matches = sig_claim.intersection(s_tokens)
    if not matches:
        return True, 0.5

    neg_words = {"not", "never", "no", "false", "fail", "failed", "fails", "failure", "neither", "nor", "none", "cannot", "cant", "wont"}
    has_neg = bool(neg_words.intersection(s_tokens))
    r = len(matches) / len(sig_claim)
    if has_neg:
        prob = max(0.15, round(0.5 - 0.35 * r, 4))
    else:
        prob = min(0.85, round(0.5 + 0.35 * r, 4))

    return bool(prob >= 0.5), float(prob)


class FallbackResult(tuple):
    """2-tuple (answers, backend) that also supports dict-like key and attribute access."""

    def __new__(cls, answers: Dict[str, Any], backend: str = "local"):
        return super().__new__(cls, (answers, backend))

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            return self[0][item]
        return super().__getitem__(item)

    def get(self, key: str, default: Any = None) -> Any:
        return self[0].get(key, default)

    def keys(self):
        return self[0].keys()

    def values(self):
        return self[0].values()

    def items(self):
        return self[0].items()

    def __contains__(self, key: Any) -> bool:
        return key in self[0]


# ── Core logic ──


async def _call_typesafe(state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
    """Call TypeSafe Jev /v1/systemone endpoint."""
    headers = {
        "Authorization": f"Bearer {os.getenv('TYPESAFE_API_KEY', TYPESAFE_API_KEY)}",
        "Content-Type": "application/json",
    }
    payload = {"state": state, "questions": questions}

    base_url = os.getenv("TYPESAFE_BASE_URL", TYPESAFE_BASE_URL)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/v1/systemone",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


def _is_typesafe_available() -> bool:
    """Check if TypeSafe API key is configured."""
    return bool(os.getenv("TYPESAFE_API_KEY", TYPESAFE_API_KEY))


def _is_laya_available() -> bool:
    """Check if laya package is importable."""
    try:
        import laya  # noqa: F401
        return True
    except (ImportError, Exception):
        return False


def _is_transformers_available() -> bool:
    """Check if transformers and torch are importable and functional."""
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
        return True
    except (ImportError, Exception):
        return False


def _get_or_load_model(backend_pref: str) -> Tuple[Any, Optional[str]]:
    """Load and cache the configured model under _MODEL_LOCK.

    Returns (model_instance, tier_name) where tier_name is 'laya' or 'transformers',
    or (None, None) if no model can be loaded.
    """
    model_name = os.getenv("JEBAT_ADVISOR_MODEL", "").strip() or None
    device = os.getenv("JEBAT_ADVISOR_DEVICE", "cpu")

    # Fast path: check cache without lock
    if _MODEL_CACHE.get("instance") is not None:
        cached_tier = _MODEL_CACHE.get("tier", "transformers")
        if backend_pref in ("auto", cached_tier):
            return _MODEL_CACHE["instance"], cached_tier

    with _MODEL_LOCK:
        if _MODEL_CACHE.get("instance") is not None:
            cached_tier = _MODEL_CACHE.get("tier", "transformers")
            if backend_pref in ("auto", cached_tier):
                return _MODEL_CACHE["instance"], cached_tier

        # Try laya if requested or auto
        if backend_pref in ("auto", "laya"):
            try:
                import laya
                router_cls = getattr(laya, "Router", None)
                if router_cls is not None:
                    instance = router_cls(preload=True)
                    _MODEL_CACHE["instance"] = instance
                    _MODEL_CACHE["tier"] = "laya"
                    _MODEL_CACHE["model_id"] = model_name or "laya-default"
                    return instance, "laya"
            except (ImportError, Exception) as e:
                logger.debug("laya package load failed: %s", e)

            # Try loading Laya via transformers if model_name specifies laya or backend_pref is laya
            if (model_name and "laya" in model_name.lower()) or backend_pref == "laya":
                target_model = model_name or "convaiinnovations/laya"
                try:
                    from transformers import pipeline
                    instance = pipeline(
                        "zero-shot-classification",
                        model=target_model,
                        device=device if device != "cpu" else -1,
                    )
                    _MODEL_CACHE["instance"] = instance
                    _MODEL_CACHE["tier"] = "laya"
                    _MODEL_CACHE["model_id"] = target_model
                    return instance, "laya"
                except (ImportError, Exception) as e:
                    logger.debug("transformers laya pipeline load failed: %s", e)
                    if backend_pref == "laya":
                        return None, None

        # Try generic ModernBERT / sequence-classification via transformers
        if backend_pref in ("auto", "transformers"):
            target_model = model_name or "answerdotai/ModernBERT-base"
            # In auto mode, only attempt transformers if a model is explicitly configured
            if backend_pref == "auto" and not model_name:
                return None, None
            try:
                from transformers import pipeline
                instance = pipeline(
                    "zero-shot-classification",
                    model=target_model,
                    device=device if device != "cpu" else -1,
                )
                _MODEL_CACHE["instance"] = instance
                _MODEL_CACHE["tier"] = "transformers"
                _MODEL_CACHE["model_id"] = target_model
                return instance, "transformers"
            except (ImportError, Exception) as e:
                logger.debug("transformers generic pipeline load failed: %s", e)

    return None, None


def _call_local_transformer(
    state: str,
    questions: Dict[str, Any],
    backend_pref: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Execute decision using local transformer model (laya or transformers pipeline)."""
    instance, tier = _get_or_load_model(backend_pref)
    if instance is None or tier is None:
        return None, None

    try:
        # Check if instance is a Laya router (has predict method)
        if tier == "laya" and hasattr(instance, "predict"):
            laya_questions = {}
            for k, q in questions.items():
                qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
                instructions = q.get("instructions", "") if isinstance(q, dict) else getattr(q, "instructions", "")
                if qtype == "Choice":
                    candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
                    laya_questions[k] = {
                        "type": "choice",
                        "instructions": instructions,
                        "criteria": candidates,
                        "candidates": candidates,
                    }
                elif qtype == "Score":
                    criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
                    laya_questions[k] = {
                        "type": "score",
                        "instructions": instructions,
                        "criteria": criteria,
                    }
                elif qtype == "Noul":
                    laya_questions[k] = {
                        "type": "noul",
                        "instructions": instructions,
                    }

            raw_res = instance.predict(state, laya_questions)
            answers: Dict[str, Any] = {}
            for k, q in questions.items():
                qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
                res = raw_res.get(k, {})
                if qtype == "Choice":
                    candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
                    ans = res.get("answer", candidates[0] if candidates else "unknown")
                    raw_probs = res.get("probabilities", {})
                    probs = {c: round(float(raw_probs.get(c, 1.0 / len(candidates))), 4) for c in candidates}
                    diff = round(1.0 - sum(probs.values()), 4)
                    probs[ans] = round(probs.get(ans, 0.0) + diff, 4)
                    conf = round(float(res.get("confidence", max(probs.values()))), 4)
                    answers[k] = {"answer": ans, "probabilities": probs, "confidence": conf}
                elif qtype == "Score":
                    criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
                    ans = int(res.get("answer", 0))
                    raw_probs = res.get("probabilities", {})
                    probs = {str(i): round(float(raw_probs.get(str(i), 1.0 / len(criteria))), 4) for i in range(len(criteria))}
                    diff = round(1.0 - sum(probs.values()), 4)
                    probs[str(ans)] = round(probs.get(str(ans), 0.0) + diff, 4)
                    conf = round(float(res.get("confidence", max(probs.values()))), 4)
                    answers[k] = {"answer": ans, "probabilities": probs, "confidence": conf}
                elif qtype == "Noul":
                    prob = round(float(res.get("probability", 0.5)), 4)
                    ans = bool(res.get("answer", prob >= 0.5))
                    answers[k] = {"answer": ans, "probability": prob}
            return answers, "laya"

        # Otherwise use Hugging Face pipeline
        answers = {}
        for k, q in questions.items():
            qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
            instructions = q.get("instructions", "") if isinstance(q, dict) else getattr(q, "instructions", "")

            if qtype == "Choice":
                candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
                template = instructions if "{}" in instructions else f"{instructions}: {{}}." if instructions else "This text is about {}."
                out = instance(state, candidate_labels=candidates, hypothesis_template=template)
                labels = out["labels"]
                scores = [float(s) for s in out["scores"]]
                best_label = labels[0]
                probs = {l: round(s, 4) for l, s in zip(labels, scores)}
                diff = round(1.0 - sum(probs.values()), 4)
                probs[best_label] = round(probs[best_label] + diff, 4)
                conf = round(scores[0], 4)
                answers[k] = {"answer": best_label, "probabilities": probs, "confidence": conf}

            elif qtype == "Score":
                criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
                crit_to_idx = {c: i for i, c in enumerate(criteria)}
                out = instance(state, candidate_labels=criteria)
                labels = out["labels"]
                scores = [float(s) for s in out["scores"]]
                best_label = labels[0]
                best_idx = crit_to_idx.get(best_label, 0)
                probs = {str(crit_to_idx.get(l, i)): round(s, 4) for i, (l, s) in enumerate(zip(labels, scores))}
                diff = round(1.0 - sum(probs.values()), 4)
                probs[str(best_idx)] = round(probs.get(str(best_idx), 0.0) + diff, 4)
                conf = round(scores[0], 4)
                answers[k] = {"answer": best_idx, "probabilities": probs, "confidence": conf}

            elif qtype == "Noul":
                claim = instructions or "is accurate"
                candidate_labels = ["yes", "no"]
                template = f"Does the following hold true: '{claim}'? {{}}"
                out = instance(state, candidate_labels=candidate_labels, hypothesis_template=template)
                labels = out["labels"]
                scores = [float(s) for s in out["scores"]]
                yes_idx = labels.index("yes") if "yes" in labels else 0
                prob = round(scores[yes_idx], 4)
                answers[k] = {"answer": bool(prob >= 0.5), "probability": prob}

        return answers, tier

    except Exception as exc:
        logger.warning("Local transformer decision failed: %s", exc)
        return None, None


def _local_fallback(state: str, questions: Dict[str, Any]) -> FallbackResult:
    """Deterministic, input-sensitive lexical heuristic fallback when no real model is configured.

    NOTE: This is a lexical heuristic (token/keyword overlap, verbatim matching,
    and domain-term expansion), NOT a trained machine learning model.
    It provides input-sensitive routing and calibrated-looking probabilities for development,
    offline testing, and fallback scenarios. For production accuracy and true System One
    decision quality, configure TYPESAFE_API_KEY or install transformers/laya and set
    JEBAT_ADVISOR_MODEL.
    """
    answers: Dict[str, Any] = {}
    state_lower = state.lower()
    s_tokens = set(_tokenize(state))
    s_list = _tokenize(state)

    for key, q in questions.items():
        qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
        if qtype == "Noul":
            instructions = q.get("instructions", "") if isinstance(q, dict) else getattr(q, "instructions", "")
            ans, prob = _eval_noul(state_lower, s_tokens, instructions)
            answers[key] = {"answer": ans, "probability": prob}
        elif qtype == "Choice":
            candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
            scores = [_score_candidate(c, state_lower, s_tokens, s_list) for c in candidates]
            best_cand, probs, conf = _softmax_probs(scores, candidates)
            answers[key] = {
                "answer": best_cand,
                "probabilities": probs,
                "confidence": conf,
            }
        elif qtype == "Score":
            criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
            best_idx, probs, conf = _eval_score(state_lower, s_tokens, s_list, criteria)
            answers[key] = {
                "answer": best_idx,
                "probabilities": probs,
                "confidence": conf,
            }

    return FallbackResult(answers, "local")


async def _decide(state: str, questions: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Route to TypeSafe, local transformer backend, or lexical fallback."""
    backend_pref = os.getenv("JEBAT_ADVISOR_BACKEND", "auto").lower()
    typesafe_key = os.getenv("TYPESAFE_API_KEY", TYPESAFE_API_KEY)

    # 1. TypeSafe Jev tier
    if backend_pref in ("auto", "typesafe") and typesafe_key:
        try:
            result = await _call_typesafe(state, questions)
            return result.get("answers", result), "typesafe"
        except Exception as exc:
            logger.warning("TypeSafe API call failed, falling back to local: %s", exc)

    # 2. Local transformer backend (Laya or generic ModernBERT / sequence-classification)
    if backend_pref in ("auto", "laya", "transformers"):
        answers, tier = _call_local_transformer(state, questions, backend_pref)
        if answers is not None and tier is not None:
            return answers, tier

    # 3. Deterministic lexical fallback
    res = _local_fallback(state, questions)
    return res[0], res[1]


def warm_advisor() -> bool:
    """Pre-load the configured advisor model into memory.

    Returns True if a local model was successfully loaded into _MODEL_CACHE,
    or False if no local model is configured/available.
    """
    backend_pref = os.getenv("JEBAT_ADVISOR_BACKEND", "auto").lower()
    if backend_pref in ("auto", "laya", "transformers"):
        instance, tier = _get_or_load_model(backend_pref)
        return instance is not None
    return False


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
    answers, backend = await _decide(req.text, questions)
    result = answers.get("category", {})
    latency = (time.perf_counter() - t0) * 1000

    return ClassifyResponse(
        category=result.get("answer", "unknown"),
        confidence=result.get("confidence", 0.0),
        probabilities=result.get("probabilities", {}),
        latency_ms=round(latency, 1),
        backend=backend,
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
    answers, backend = await _decide(req.text, questions)
    result = answers.get("check", {})
    latency = (time.perf_counter() - t0) * 1000

    return VerifyResponse(
        result=bool(result.get("answer", False)),
        probability=result.get("probability", 0.5),
        latency_ms=round(latency, 1),
        backend=backend,
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
    answers, backend = await _decide(req.text, questions)
    result = answers.get("rating", {})
    # Tiers may return a float expected-level; index must be an int in range.
    try:
        score_idx = int(round(float(result.get("answer", 0) or 0)))
    except (TypeError, ValueError):
        score_idx = 0
    score_idx = max(0, min(score_idx, len(req.criteria) - 1))
    latency = (time.perf_counter() - t0) * 1000

    return ScoreResponse(
        score=score_idx,
        level=req.criteria[score_idx],
        confidence=result.get("confidence", 0.0),
        latency_ms=round(latency, 1),
        backend=backend,
    )

@router.get("/status")
async def advisor_status() -> Dict[str, Any]:
    """Check advisor backend availability."""
    backend_env = os.getenv("JEBAT_ADVISOR_BACKEND", "auto").lower()
    typesafe_key = os.getenv("TYPESAFE_API_KEY", TYPESAFE_API_KEY)
    typesafe_url = os.getenv("TYPESAFE_BASE_URL", TYPESAFE_BASE_URL)
    model_env = os.getenv("JEBAT_ADVISOR_MODEL", "").strip() or None

    available_backends: List[str] = []
    if typesafe_key:
        available_backends.append("typesafe")
    if _is_laya_available():
        available_backends.append("laya")
    if _is_transformers_available():
        available_backends.append("transformers")

    with _MODEL_LOCK:
        model_loaded = bool(_MODEL_CACHE.get("instance") is not None)
        cached_tier = _MODEL_CACHE.get("tier")
        cached_model = _MODEL_CACHE.get("model_id")

    # Resolve active backend
    if backend_env == "typesafe" or (backend_env == "auto" and typesafe_key):
        advisor_backend = "typesafe"
    elif model_loaded:
        advisor_backend = cached_tier or "transformers"
    elif backend_env == "laya" and _is_laya_available():
        advisor_backend = "laya"
    elif backend_env == "transformers" and _is_transformers_available():
        advisor_backend = "transformers"
    elif backend_env == "auto":
        if "laya" in available_backends and model_env:
            advisor_backend = "laya"
        elif "transformers" in available_backends and model_env:
            advisor_backend = "transformers"
        else:
            advisor_backend = "local"
    else:
        advisor_backend = "local"

    active_model = cached_model or model_env

    return {
        "backend": "typesafe" if typesafe_key else "local_fallback",
        "typesafe_configured": bool(typesafe_key),
        "base_url": typesafe_url if typesafe_key else None,
        "capabilities": ["classify", "route", "score", "verify", "gate", "triage"],
        "question_types": ["Noul", "Choice", "Score"],
        "advisor_backend": advisor_backend,
        "model": active_model,
        "model_loaded": model_loaded,
        "available_backends": available_backends,
    }
