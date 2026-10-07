"""Deterministic project learning advice, with evidence and feedback in the existing KB."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .automimpi import DreamReport, SelfLearn, project_traces
from jebat.features.wiki.wiki_core import WikiStore


def redact_learning_text(text: str) -> str:
    """Remove recognizable credentials before copying error/context text into learning stores."""
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", "[REDACTED PRIVATE KEY]", text, flags=re.DOTALL)
    text = re.sub(r"(?i)\b(bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|authorization)(\s*[=:]\s*)([^\s,;]+)", r"\1\2[REDACTED]", text)
    text = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    return text


class LearningAdvisor:
    """Advice is a proposal. Feedback never executes actions or changes source confidence."""

    def __init__(self, memory, kb: WikiStore, project_root: str):
        self.memory = memory
        self.kb = kb
        self.project_root = str(Path(project_root).resolve())
        self.project = Path(self.project_root).name or "workspace"

    def advise(self, focus: str = "", limit: int = 5, analysis: dict | None = None) -> dict[str, Any]:
        if not isinstance(focus, str) or len(focus) > 500:
            raise ValueError("focus must be a string of at most 500 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("limit must be an integer from 1 to 20")
        analysis = analysis if analysis is not None else SelfLearn(self.memory).analyze(self.project, self.project_root)
        traces = {t.trace_id: t for t in project_traces(self.memory, self.project, self.project_root)}
        feedback = self.kb.advice_feedback(self.project_root)
        recommendations, suppressed = [], 0
        for item in analysis["recommendations"]:
            evidence = [traces[tid] for tid in item["evidence_ids"] if tid in traces]
            if not evidence:
                continue
            if focus and not any(focus.casefold() in t.content.casefold() or any(focus.casefold() in tag.casefold() for tag in t.tags) for t in evidence):
                continue
            # A decision applies to this evidence version, not all future occurrences.
            source = json.dumps([item["type"], item["action"], item["evidence_count"], [
                [t.trace_id, t.content, t.confidence, t.created_at.isoformat(), t.last_accessed.isoformat()]
                for t in evidence
            ]], sort_keys=True)
            source_id = hashlib.sha256(source.encode()).hexdigest()
            title = redact_learning_text(item["message"])
            payload = {
                "type": item["type"], "priority": item["priority"], "action": item["action"],
                "evidence_count": item["evidence_count"], "evidence_ids": [t.trace_id for t in evidence],
                "citations": [{"memory_id": t.trace_id, "created_at": t.created_at.isoformat(),
                               "last_accessed": t.last_accessed.isoformat(),
                               "root_bound": bool(t.context.get("project_root"))} for t in evidence],
                "requires_review": True,
            }
            record_id = self.kb.record_learning(self.project_root, "advice", source_id, title,
                                                title + "\nProposed action: " + item["action"], payload, payload["evidence_ids"])
            outcome = feedback.get(record_id)
            if outcome in {"unhelpful", "dismissed"}:
                suppressed += 1
                continue
            recommendations.append({"record_id": record_id, "message": title, **payload, "feedback": outcome})
            if len(recommendations) >= limit:
                break
        return {
            "project": self.project, "project_root": self.project_root, "mode": "deterministic",
            "observed_at": analysis["observed_at"], "metric_basis": analysis["metric_basis"],
            "recommendations": recommendations, "suppressed_by_feedback": suppressed,
            "memory_count": analysis["knowledge_map"]["total_memories"],
            "legacy_unbound_count": analysis["scope"]["legacy_unbound_count"],
            "kb": self.kb.learning_status(self.project_root),
        }

    def record_dream(self, report: DreamReport, dream_count: int) -> str:
        if report.status != "completed":
            raise ValueError("Only completed dream cycles are persisted")
        payload = asdict(report)
        for suggestion in payload["suggestions"]:
            suggestion["suggestion_type"] = suggestion["suggestion_type"].value
            suggestion["urgency"] = suggestion["urgency"].value
        evidence_ids = sorted({tid for item in report.analysis["recommendations"] for tid in item["evidence_ids"]})
        title = f"AutoMimpi {report.date} cycle {dream_count}"
        content = "\n".join([title, f"Processed {report.memories_processed}; new patterns {report.patterns_extracted}; new generalizations {report.generalizations_created}; pruned {report.memories_pruned}.",
                             *[redact_learning_text(item["message"]) for item in report.analysis["recommendations"]]])
        return self.kb.record_learning(self.project_root, "dream", str(dream_count), title, content, payload, evidence_ids)

    def feedback(self, record_id: str, outcome: str, evidence: str) -> dict[str, Any]:
        if not isinstance(record_id, str) or not isinstance(evidence, str):
            raise ValueError("record_id and evidence must be strings")
        return self.kb.learning_feedback(self.project_root, record_id, outcome, redact_learning_text(evidence))
