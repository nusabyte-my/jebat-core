"""Agentix ops — eval (golden tasks) and export (portability).

- `jebat agentix eval PATH [--live]` runs a solution's golden tasks plus
  structural checks. Code-runtime tasks execute deterministically; LLM
  runtime tasks are skipped unless --live (they need a real provider).
- `jebat agentix export PATH --format claude-subagent|skill [--out DIR]`
  ships the solution to other harnesses — the industry converges on
  markdown-in-folders; JEBAT's manifest is a superset of those formats.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jebat_cli_new.agentix import _load_manifest, _validate

# Claude Code tool-name equivalents for the native JEBAT tools.
CLAUDE_TOOL_MAP = {
    "read_file": "Read",
    "write_file": "Write",
    "search_files": "Grep",
    "terminal": "Bash",
    "list_dir": "Glob",
}

GOLDEN_DIR = "golden"
MAX_ALLOWLIST = 10  # tool-overload is the #1 splitting trigger — enforce at eval


# ── Golden tasks ────────────────────────────────────────────────────

def load_golden_tasks(sol: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse golden/*.json. Returns (tasks, errors)."""
    tasks: List[Dict[str, Any]] = []
    errors: List[str] = []
    golden_dir = sol / GOLDEN_DIR
    if not golden_dir.is_dir():
        return tasks, errors
    for path in sorted(golden_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"golden/{path.name}: unreadable ({exc})")
            continue
        if not isinstance(raw, dict) or not str(raw.get("task", "")).strip():
            errors.append(f"golden/{path.name}: missing non-empty 'task'")
            continue
        checks = raw.get("checks") or []
        if not isinstance(checks, list):
            errors.append(f"golden/{path.name}: 'checks' must be a list")
            continue
        bad = [c for c in checks if not isinstance(c, dict) or c.get("type") not in ("contains", "not_contains", "regex") or not str(c.get("value", ""))]
        if bad:
            errors.append(f"golden/{path.name}: malformed checks (need type contains|not_contains|regex + value)")
            continue
        tasks.append({"file": path.name, "task": str(raw["task"]), "checks": checks})
    return tasks, errors


def apply_checks(answer: str, checks: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], bool, str]]:
    results = []
    for check in checks:
        kind, value = check["type"], str(check["value"])
        if kind == "contains":
            ok = value.lower() in answer.lower()
            detail = f"expected to contain {value!r}"
        elif kind == "not_contains":
            ok = value.lower() not in answer.lower()
            detail = f"expected NOT to contain {value!r}"
        else:  # regex
            try:
                ok = re.search(value, answer) is not None
            except re.error as exc:
                ok, detail = False, f"invalid regex ({exc})"
            else:
                detail = f"expected to match /{value}/"
        results.append((check, ok, detail))
    return results


# ── Eval ────────────────────────────────────────────────────────────

def evaluate_solution(sol: Path, live: bool = False) -> Tuple[List[str], int]:
    """Run structural checks + golden tasks. Returns (lines, failure_count)."""
    lines: List[str] = []
    failures = 0

    mf = _load_manifest(sol)
    name = mf.get("name", "?")
    runtime = mf.get("runtime", "code")
    lines.append(f"[{name}] template={mf.get('template')} runtime={runtime}")

    errors = _validate(sol)
    for error in errors:
        lines.append(f"  FAIL structural: {error}")
        failures += 1
    if not errors:
        lines.append("  ok   structural (manifest, entrypoint, tools, deploy.allow)")

    allowlist = mf.get("llm_tools") or []
    if runtime == "llm":
        doctrine = sol / "agent.md"
        if not doctrine.is_file():
            lines.append("  FAIL structural: runtime llm requires agent.md (doctrine)")
            failures += 1
        else:
            lines.append("  ok   doctrine (agent.md present)")
        if len(allowlist) > MAX_ALLOWLIST:
            lines.append(
                f"  FAIL structural: llm_tools has {len(allowlist)} entries — cap is {MAX_ALLOWLIST}"
                " (tool overload is the #1 splitting trigger)"
            )
            failures += 1
        elif allowlist:
            lines.append(f"  ok   allowlist ({len(allowlist)} tools ≤ {MAX_ALLOWLIST})")

    tasks, golden_errors = load_golden_tasks(sol)
    for error in golden_errors:
        lines.append(f"  FAIL golden: {error}")
        failures += 1

    if not tasks:
        if not golden_errors:
            lines.append(f"  note no golden tasks — add {GOLDEN_DIR}/*.json so `eval` can guard this template")
        return lines, failures

    executed = skipped = 0
    for task_spec in tasks:
        label = task_spec["file"]
        if runtime == "llm" and not live:
            lines.append(f"  skip golden/{label}: llm runtime — rerun with --live to execute against the real provider")
            skipped += 1
            continue
        try:
            from jebat_cli_new.agentix import _run_solution

            answer, _info = _run_solution(sol, task_spec["task"], yolo=True)
        except (Exception, SystemExit) as exc:  # noqa: BLE001 — a crashing task IS a failing task
            lines.append(f"  FAIL golden/{label}: run raised {exc}")
            failures += 1
            executed += 1
            continue
        executed += 1
        task_failed = False
        for check, ok, detail in apply_checks(answer or "", task_spec["checks"]):
            if ok:
                lines.append(f"  ok   golden/{label}: {check['type']} {check['value']!r}")
            else:
                lines.append(f"  FAIL golden/{label}: {detail} — answer was: {(answer or '')[:120]!r}")
                task_failed = True
        if task_failed:
            failures += 1

    lines.append(f"  summary: {executed} executed, {skipped} skipped, {failures} failures")
    return lines, failures


# ── Export ──────────────────────────────────────────────────────────

def export_solution(sol: Path, fmt: str, out_dir: Optional[Path]) -> Path:
    mf = _load_manifest(sol)
    name = str(mf.get("name", "solution"))
    description = str(mf.get("description", "")).strip() or f"JEBAT agentix solution {name}"
    doctrine_path = sol / "agent.md"
    doctrine = doctrine_path.read_text(encoding="utf-8").strip() if doctrine_path.is_file() else ""
    if not doctrine:
        raise SystemExit("export requires agent.md (doctrine) — only llm-runtime solutions export")

    if out_dir is None:
        out_dir = Path.cwd() / "agentix-export"
    out_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "claude-subagent":
        tools = [CLAUDE_TOOL_MAP.get(t, t) for t in (mf.get("llm_tools") or [])]
        front = [
            "---",
            f"name: {name}",
            f"description: {description} Use proactively when the task matches this specialty.",
        ]
        if tools:
            front.append(f"tools: {', '.join(tools)}")
        front.append("model: inherit")
        front.append("---")
        body = doctrine
        out = out_dir / f"{name}.md"
        out.write_text("\n".join(front) + "\n\n" + body + "\n", encoding="utf-8", newline="\n")
        return out

    if fmt == "skill":
        out = out_dir / name / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "---\n"
            f'name: "{name}"\n'
            f'description: "{description}"\n'
            "---\n\n"
            f"# {name}\n\n"
            f"{doctrine}\n"
        )
        out.write_text(content, encoding="utf-8", newline="\n")
        return out

    raise SystemExit(f"unknown format {fmt!r} (use claude-subagent | skill)")
