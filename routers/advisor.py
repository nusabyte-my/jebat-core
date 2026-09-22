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

# A local model on a shared CPU box can stall for tens of seconds under load
# (measured: >75s for one classify while co-tenant mail processes saturated
# the machine). Bound it and stop hammering it after repeated misses.
def _advisor_timeout_s() -> float:
    try:
        return max(0.1, float(os.getenv("JEBAT_ADVISOR_TIMEOUT_S", "3")))
    except ValueError:
        return 3.0


def _advisor_cooldown_s() -> float:
    try:
        return max(1.0, float(os.getenv("JEBAT_ADVISOR_COOLDOWN_S", "60")))
    except ValueError:
        return 60.0


# Circuit-breaker: after a timeout/error the model tier is skipped for a
# cooldown window so one slow request cannot cascade across the traffic mix.
_MODEL_STATE: Dict[str, Any] = {"open_until": 0.0, "consecutive": 0}
_MODEL_STATE_LOCK = threading.Lock()


def _advisor_torch_threads() -> None:
    """Cap torch intra-op threads so inference cannot starve co-tenants."""
    try:
        import torch
        n = int(os.getenv("JEBAT_ADVISOR_THREADS", "2"))
        if n > 0:
            torch.set_num_threads(n)
    except Exception:
        pass


def _model_in_cooldown() -> bool:
    with _MODEL_STATE_LOCK:
        return time.time() < _MODEL_STATE.get("open_until", 0.0)


def _model_record_miss() -> None:
    with _MODEL_STATE_LOCK:
        _MODEL_STATE["consecutive"] = _MODEL_STATE.get("consecutive", 0) + 1
        if _MODEL_STATE["consecutive"] >= 2:
            _MODEL_STATE["open_until"] = time.time() + _advisor_cooldown_s()
            logger.warning(
                "advisor model tier cooling down for %.0fs after %d slow/failed calls",
                _advisor_cooldown_s(), _MODEL_STATE["consecutive"],
            )


def _model_record_hit() -> None:
    with _MODEL_STATE_LOCK:
        _MODEL_STATE["consecutive"] = 0
        _MODEL_STATE["open_until"] = 0.0


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


_AVAIL_CACHE: Dict[str, bool] = {}

# Packages whose *presence* we report without importing. torch's import is
# ~4.6s cold and runs on the event loop, so a status poll that imported it
# blew Cloudflare's timeout on the first request after every restart (the
# cache only helps once one call has already paid the cost). find_spec just
# locates the package on sys.path — milliseconds — and the real import still
# happens inside _get_or_load_model, guarded by the timeout + breaker.
_PROBE_MODULES = {
    "laya": ("laya",),
    "transformers": ("transformers", "torch"),
}


def _is_module_installed(module: str) -> bool:
    from importlib.util import find_spec
    try:
        return find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def _probe_available(name: str) -> bool:
    """Whether every module backing a tier is importable-by-path (cached)."""
    if name not in _AVAIL_CACHE:
        mods = _PROBE_MODULES.get(name, ())
        _AVAIL_CACHE[name] = bool(mods) and all(_is_module_installed(m) for m in mods)
    return _AVAIL_CACHE[name]


def _is_laya_available() -> bool:
    """Check if the laya package is installed (does not import it)."""
    return _probe_available("laya")


def _wants_laya(backend_pref: str, model_name: str | None) -> bool:
    """Single source of truth for whether the Laya tier should be attempted.

    The 421M Laya checkpoint is ~15+ min of CPU inference on an 8-core box,
    so `auto` only selects it when the configured model name actually says
    laya. An explicit backend=laya forces the attempt regardless. _decide and
    /status both call this so they can never disagree about which tier runs.
    """
    pref = (backend_pref or "auto").lower()
    if pref == "laya":
        return True
    return pref == "auto" and bool(model_name) and "laya" in model_name.lower()


def _is_transformers_available() -> bool:
    """Check if transformers and torch are installed (does not import them)."""
    return _probe_available("transformers")



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
        _advisor_torch_threads()
        # Laya proper: the PyPI `laya` package is the real typed-decision
        # engine (bidirectional encoder + decision heads, temperature
        # calibrated). Load ONE agent, never laya.Router(preload=True) which
        # keeps all three checkpoints (~2.5 GB) resident.
        #
        # GATED like the transformers tier: in `auto` mode we only attempt
        # Laya when the configured model name actually says laya. The 421M
        # checkpoint is ~15+ min of CPU inference on an 8-core box (measured:
        # a 5-question benchmark produced zero answers before timeout), so an
        # unconditional auto-load would let a cleared JEBAT_ADVISOR_MODEL hang
        # the API warm-up. Explicit backend=laya still forces the attempt.
        if _wants_laya(backend_pref, model_name):
            try:
                import laya as _laya

                load_fn = getattr(_laya, "load", None)
                if load_fn is not None:
                    target = model_name or "convaiinnovations/laya"
                    try:
                        instance = load_fn(target, device=device)
                    except TypeError:
                        instance = load_fn(target)  # signature without device
                    _MODEL_CACHE["instance"] = instance
                    _MODEL_CACHE["tier"] = "laya"
                    _MODEL_CACHE["model_id"] = target
                    logger.info("advisor: loaded Laya agent %s on %s", target, device)
                    return instance, "laya"
            except Exception as e:  # not installed, no weights, bad device
                logger.debug("laya load failed: %s", e)
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
            # Laya's schema differs from ours and the old code got all three
            # of these wrong, silently answering with candidates[0]:
            #   choice -> criteria is a {label: description} dict, answer key "choice"
            #   score  -> criteria is a list, answer key "score" (expected level, float)
            #   noul   -> answer key "noul" (P(true))
            # and answers arrive under raw["answers"], not at the top level.
            laya_questions: Dict[str, Any] = {}
            for k, q in questions.items():
                qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
                instructions = q.get("instructions", "") if isinstance(q, dict) else getattr(q, "instructions", "")
                if qtype == "Choice":
                    candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
                    if not candidates:
                        return None, None
                    laya_questions[k] = {
                        "type": "choice",
                        "instructions": instructions,
                        "criteria": {c: c for c in candidates},
                    }
                elif qtype == "Score":
                    criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
                    if not criteria:
                        return None, None
                    laya_questions[k] = {
                        "type": "score",
                        "instructions": instructions,
                        "criteria": list(criteria),
                    }
                elif qtype == "Noul":
                    laya_questions[k] = {"type": "noul", "instructions": instructions}
                else:
                    return None, None

            raw = instance.predict(state, laya_questions)
            # An unexpected envelope falls through to the lexical tier. Never
            # substitute a default answer — that is exactly how the previous
            # implementation produced a confident-looking wrong category.
            laya_answers = raw.get("answers") if isinstance(raw, dict) else None
            if not isinstance(laya_answers, dict) or any(k not in laya_answers for k in questions):
                logger.warning("laya returned an unexpected envelope; using lexical fallback")
                return None, None

            answers: Dict[str, Any] = {}
            for k, q in questions.items():
                qtype = q.get("type", "Noul") if isinstance(q, dict) else getattr(q, "type", "Noul")
                res = laya_answers[k]
                if not isinstance(res, dict):
                    return None, None
                probs_in = res.get("probabilities") or {}
                if qtype == "Choice":
                    candidates = q.get("candidates", []) if isinstance(q, dict) else getattr(q, "candidates", [])
                    if "choice" not in res or not probs_in:
                        return None, None
                    probs = {c: float(probs_in.get(c, 0.0)) for c in candidates}
                    total = sum(probs.values()) or 1.0
                    probs = {c: round(v / total, 4) for c, v in probs.items()}
                    answers[k] = {
                        "answer": str(res["choice"]),
                        "probabilities": probs,
                        "confidence": round(float(res.get("confidence", max(probs.values()))), 4),
                    }
                elif qtype == "Score":
                    criteria = q.get("criteria", []) if isinstance(q, dict) else getattr(q, "criteria", [])
                    if "score" not in res or not probs_in:
                        return None, None
                    probs = {str(i): float(probs_in.get(str(i), 0.0)) for i in range(len(criteria))}
                    total = sum(probs.values()) or 1.0
                    probs = {kk: round(v / total, 4) for kk, v in probs.items()}
                    level = max(0, min(int(round(float(res["score"]))), len(criteria) - 1))
                    answers[k] = {
                        "answer": level,
                        "probabilities": probs,
                        "confidence": round(float(res.get("confidence", max(probs.values()))), 4),
                        "expected_level": round(float(res["score"]), 4),
                    }
                else:
                    if "noul" not in res:
                        return None, None
                    prob = round(float(res["noul"]), 4)
                    answers[k] = {"answer": bool(prob >= 0.5), "probability": prob}
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

    # 2. Local transformer backend (Laya or ModernBERT sequence-classification).
    # Runs in a worker thread with a hard deadline: the inference is synchronous
    # and CPU-bound, so calling it directly on the event loop would freeze the
    # whole worker for its duration, and on a loaded shared box that duration
    # can be tens of seconds. A timeout or breaker trip falls through to the
    # lexical tier rather than hanging the request.
    if backend_pref in ("auto", "laya", "transformers") and not _model_in_cooldown():
        try:
            answers, tier = await asyncio.wait_for(
                asyncio.to_thread(_call_local_transformer, state, questions, backend_pref),
                timeout=_advisor_timeout_s(),
            )
        except asyncio.TimeoutError:
            logger.warning(
                "advisor model tier exceeded %.0fs; using lexical fallback", _advisor_timeout_s()
            )
            _model_record_miss()
            answers, tier = None, None
        except Exception as exc:
            logger.warning("advisor model tier failed (%s); using lexical fallback", exc)
            _model_record_miss()
            answers, tier = None, None
        else:
            if answers is not None and tier is not None:
                _model_record_hit()
                return answers, tier
            # None means either "no model configured" (nothing to cool down) or
            # "a loaded model produced nothing usable" (worth cooling down).
            if _MODEL_CACHE.get("instance") is not None:
                _model_record_miss()

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
        # Must mirror _get_or_load_model exactly, or /status advertises a
        # tier that _decide will never actually use.
        if _wants_laya("auto", model_env) and _is_laya_available():
            advisor_backend = "laya"
        elif model_env and _is_transformers_available():
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
