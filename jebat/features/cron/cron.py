"""JEBAT Cron / Scheduled Jobs — persistent task scheduler with SQLite backend.

Supports two execution modes:
- Agent mode (default): LLM runs the prompt each tick
- Watchdog mode (no_agent=True): script at script_path runs, stdout delivered verbatim

Schedule formats:
- '30m'          -> every 30 minutes
- 'every 2h'     -> every 2 hours
- 'every 5m'     -> every 5 minutes
- '0 9 * * *'    -> standard cron expression
- ISO timestamp  -> one-shot at that time

Jobs are persisted in ~/.jebat/cron.db and checked/executed on demand
(e.g. `jebat cron run --all` or REPL startup).
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jebat.tools import register_tool


# ── Database ──────────────────────────────────────────────────────────────────

DB_PATH = Path.home() / ".jebat" / "cron.db"

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS cron_jobs (
    id TEXT PRIMARY KEY,
    name TEXT,
    schedule TEXT,
    prompt TEXT,
    script_path TEXT DEFAULT '',
    no_agent INTEGER DEFAULT 0,
    deliver TEXT DEFAULT '',
    enabled INTEGER DEFAULT 1,
    created_at REAL,
    updated_at REAL,
    last_run REAL,
    last_output TEXT,
    run_count INTEGER DEFAULT 0,
    skills TEXT DEFAULT '[]',
    model TEXT DEFAULT '',
    workdir TEXT DEFAULT ''
);
"""


def _get_conn() -> sqlite3.Connection:
    """Return a connection to the cron database, creating it if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict with JSON fields parsed."""
    d = dict(row)
    # Parse JSON-encoded fields
    for key in ("skills",):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    # Convert integer booleans
    for key in ("no_agent", "enabled"):
        if key in d:
            d[key] = bool(d[key])
    return d


# ── Schedule Parsing ──────────────────────────────────────────────────────────

# Matches simple interval patterns
_INTERVAL_RE = re.compile(
    r"^(?:every\s+)?(\d+)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|s|sec|secs|second|seconds)$",
    re.IGNORECASE,
)

# Standard 5-field cron expression
_CRON_RE = re.compile(
    r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$"
)


def parse_schedule(schedule: str) -> dict[str, Any]:
    """Parse a schedule string into a normalized descriptor.

    Returns a dict with:
        type: 'interval' | 'cron' | 'once'
        For interval: seconds (int)
        For cron: expr (str, original 5-field expression)
        For once: at (float, unix timestamp)
    """
    s = schedule.strip()

    # Try interval pattern first: '30m', 'every 2h', etc.
    m = _INTERVAL_RE.match(s)
    if m:
        value = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith("s"):
            seconds = value
        elif unit.startswith("m"):
            seconds = value * 60
        elif unit.startswith("h"):
            seconds = value * 3600
        elif unit.startswith("d"):
            seconds = value * 86400
        else:
            seconds = value * 60  # default to minutes
        return {"type": "interval", "seconds": seconds}

    # Try standard cron expression (5 fields)
    m = _CRON_RE.match(s)
    if m:
        return {"type": "cron", "expr": s}

    # Try ISO timestamp for one-shot
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return {"type": "once", "at": dt.timestamp()}
    except (ValueError, TypeError):
        pass

    raise ValueError(
        f"Invalid schedule format: '{schedule}'. "
        "Supported: '30m', 'every 2h', '0 9 * * *', or ISO timestamp."
    )


def next_run_time(parsed: dict[str, Any], after: float | None = None) -> float | None:
    """Calculate the next run time from a parsed schedule descriptor.

    Returns None for one-shot jobs that have already passed.
    """
    now = after or time.time()

    if parsed["type"] == "interval":
        return now + parsed["seconds"]

    if parsed["type"] == "once":
        ts = parsed["at"]
        return ts if ts > now else None

    if parsed["type"] == "cron":
        # Basic cron next-run calculation
        return _next_cron_time(parsed["expr"], now)

    return None


def _next_cron_time(expr: str, after: float) -> float | None:
    """Compute next run time for a 5-field cron expression.

    Fields: minute hour day-of-month month day-of-week
    Supports: *, */N, N, N-M, comma-separated values.
    """
    fields = expr.split()
    if len(fields) != 5:
        return None

    def _expand(field_str: str, min_val: int, max_val: int) -> set[int]:
        """Expand a single cron field into a set of matching values."""
        values: set[int] = set()
        for part in field_str.split(","):
            if "/" in part:
                base, step = part.split("/", 1)
                step = int(step)
                if base == "*":
                    start = min_val
                elif "-" in base:
                    start = int(base.split("-")[0])
                else:
                    start = int(base)
                values.update(range(start, max_val + 1, step))
            elif "-" in part:
                lo, hi = part.split("-", 1)
                values.update(range(int(lo), int(hi) + 1))
            elif part == "*":
                values.update(range(min_val, max_val + 1))
            else:
                values.add(int(part))
        return values

    try:
        minutes = _expand(fields[0], 0, 59)
        hours = _expand(fields[1], 0, 23)
        doms = _expand(fields[2], 1, 31)
        months = _expand(fields[3], 1, 12)
        dows = _expand(fields[4], 0, 6)  # 0=Sunday
    except (ValueError, IndexError):
        return None

    # Search forward up to 366 days
    dt = datetime.fromtimestamp(after, tz=timezone.utc)
    for _ in range(366 * 24 * 60):  # minute-by-minute for up to a year
        dt = dt.replace(second=0, microsecond=0)
        from datetime import timedelta
        dt += timedelta(minutes=1)

        if dt.month not in months:
            continue
        if dt.day not in doms:
            continue
        # Python weekday: Monday=0..Sunday=6; cron: Sunday=0..Saturday=6
        py_dow = dt.weekday()
        cron_dow = (py_dow + 1) % 7
        if cron_dow not in dows:
            continue
        if dt.hour not in hours:
            continue
        if dt.minute not in minutes:
            continue

        return dt.timestamp()

    return None


def is_due(job: dict[str, Any]) -> bool:
    """Check whether a job is due to run based on its schedule and last_run."""
    if not job.get("enabled", True):
        return False

    parsed = parse_schedule(job["schedule"])

    if parsed["type"] == "once":
        # One-shot: due if we haven't run yet and the time has arrived
        if job.get("run_count", 0) > 0:
            return False
        return parsed["at"] <= time.time()

    if job.get("last_run") is None:
        return True  # Never run before

    nxt = next_run_time(parsed, job["last_run"])
    if nxt is None:
        return False
    return nxt <= time.time()


# ── Tool: cron_create ────────────────────────────────────────────────────────

@register_tool(
    "cron_create",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Job name"},
            "schedule": {
                "type": "string",
                "description": "Schedule: '30m', 'every 2h', '0 9 * * *', or ISO timestamp",
            },
            "prompt": {"type": "string", "description": "Prompt for agent mode or description"},
            "deliver": {
                "type": "string",
                "description": "Delivery target (e.g. channel, webhook URL)",
                "default": "",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Skills to load for agent mode",
                "default": [],
            },
            "model": {"type": "string", "description": "Model override", "default": ""},
            "no_agent": {
                "type": "boolean",
                "description": "If true, run script_path as watchdog instead of agent",
                "default": False,
            },
            "script_path": {
                "type": "string",
                "description": "Path to script for watchdog mode",
                "default": "",
            },
            "workdir": {
                "type": "string",
                "description": "Working directory for script execution",
                "default": "",
            },
        },
        "required": ["name", "schedule", "prompt"],
    },
    safety_tier="auto",
    description="Create a new scheduled cron job",
)
async def cron_create(
    name: str,
    schedule: str,
    prompt: str,
    deliver: str = "",
    skills: list[str] | None = None,
    model: str = "",
    no_agent: bool = False,
    script_path: str = "",
    workdir: str = "",
) -> dict[str, Any]:
    """Create a new scheduled job and persist it to cron.db."""
    # Validate schedule
    try:
        parse_schedule(schedule)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    skills_json = json.dumps(skills or [])

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO cron_jobs
               (id, name, schedule, prompt, script_path, no_agent, deliver,
                enabled, created_at, updated_at, last_run, last_output,
                run_count, skills, model, workdir)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, NULL, 0, ?, ?, ?)""",
            (job_id, name, schedule, prompt, script_path, int(no_agent),
             deliver, now, now, skills_json, model, workdir),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "id": job_id,
        "name": name,
        "schedule": schedule,
        "mode": "watchdog" if no_agent else "agent",
        "message": f"Cron job '{name}' created with ID {job_id}",
    }


# ── Tool: cron_list ──────────────────────────────────────────────────────────

@register_tool(
    "cron_list",
    schema={
        "type": "object",
        "properties": {},
    },
    safety_tier="auto",
    description="List all scheduled cron jobs",
)
async def cron_list() -> dict[str, Any]:
    """List all scheduled jobs with status, schedule, and last run info."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM cron_jobs ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    jobs = [_row_to_dict(r) for r in rows]

    # Add human-readable status and next_run
    for job in jobs:
        job["status"] = "active" if job["enabled"] else "paused"
        try:
            parsed = parse_schedule(job["schedule"])
            nxt = next_run_time(parsed, job.get("last_run"))
            if nxt:
                job["next_run"] = datetime.fromtimestamp(
                    nxt, tz=timezone.utc
                ).isoformat()
            else:
                job["next_run"] = None
        except ValueError:
            job["next_run"] = None

        if job.get("last_run"):
            job["last_run_iso"] = datetime.fromtimestamp(
                job["last_run"], tz=timezone.utc
            ).isoformat()
        else:
            job["last_run_iso"] = None

    return {"ok": True, "count": len(jobs), "jobs": jobs}


# ── Tool: cron_pause ─────────────────────────────────────────────────────────

@register_tool(
    "cron_pause",
    schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Cron job ID to pause"},
        },
        "required": ["job_id"],
    },
    safety_tier="auto",
    description="Pause a scheduled cron job without deleting it",
)
async def cron_pause(job_id: str) -> dict[str, Any]:
    """Pause a job by setting enabled=0."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "UPDATE cron_jobs SET enabled = 0, updated_at = ? WHERE id = ?",
            (time.time(), job_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"ok": False, "error": f"Job '{job_id}' not found"}
    finally:
        conn.close()

    return {"ok": True, "id": job_id, "message": f"Job '{job_id}' paused"}


# ── Tool: cron_resume ────────────────────────────────────────────────────────

@register_tool(
    "cron_resume",
    schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Cron job ID to resume"},
        },
        "required": ["job_id"],
    },
    safety_tier="auto",
    description="Resume a paused cron job",
)
async def cron_resume(job_id: str) -> dict[str, Any]:
    """Resume a paused job by setting enabled=1."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "UPDATE cron_jobs SET enabled = 1, updated_at = ? WHERE id = ?",
            (time.time(), job_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"ok": False, "error": f"Job '{job_id}' not found"}
    finally:
        conn.close()

    return {"ok": True, "id": job_id, "message": f"Job '{job_id}' resumed"}


# ── Tool: cron_remove ────────────────────────────────────────────────────────

@register_tool(
    "cron_remove",
    schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Cron job ID to delete"},
        },
        "required": ["job_id"],
    },
    safety_tier="confirm",
    description="Delete a cron job permanently",
)
async def cron_remove(job_id: str) -> dict[str, Any]:
    """Permanently delete a cron job."""
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM cron_jobs WHERE id = ?", (job_id,))
        conn.commit()
        if cur.rowcount == 0:
            return {"ok": False, "error": f"Job '{job_id}' not found"}
    finally:
        conn.close()

    return {"ok": True, "id": job_id, "message": f"Job '{job_id}' deleted"}


# ── Tool: cron_update ────────────────────────────────────────────────────────

@register_tool(
    "cron_update",
    schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Cron job ID to update"},
            "name": {"type": "string", "description": "New name"},
            "schedule": {"type": "string", "description": "New schedule expression"},
            "prompt": {"type": "string", "description": "New prompt"},
            "deliver": {"type": "string", "description": "New delivery target"},
            "skills": {"type": "array", "items": {"type": "string"}, "description": "New skills list"},
            "model": {"type": "string", "description": "New model override"},
            "no_agent": {"type": "boolean", "description": "Toggle watchdog mode"},
            "script_path": {"type": "string", "description": "New script path"},
            "workdir": {"type": "string", "description": "New working directory"},
        },
        "required": ["job_id"],
    },
    safety_tier="auto",
    description="Update parameters of an existing cron job",
)
async def cron_update(
    job_id: str,
    name: str | None = None,
    schedule: str | None = None,
    prompt: str | None = None,
    deliver: str | None = None,
    skills: list[str] | None = None,
    model: str | None = None,
    no_agent: bool | None = None,
    script_path: str | None = None,
    workdir: str | None = None,
) -> dict[str, Any]:
    """Update one or more fields of an existing cron job."""
    # Validate schedule if provided
    if schedule is not None:
        try:
            parse_schedule(schedule)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    updates: list[tuple[str, Any]] = []
    if name is not None:
        updates.append(("name", name))
    if schedule is not None:
        updates.append(("schedule", schedule))
    if prompt is not None:
        updates.append(("prompt", prompt))
    if deliver is not None:
        updates.append(("deliver", deliver))
    if skills is not None:
        updates.append(("skills", json.dumps(skills)))
    if model is not None:
        updates.append(("model", model))
    if no_agent is not None:
        updates.append(("no_agent", int(no_agent)))
    if script_path is not None:
        updates.append(("script_path", script_path))
    if workdir is not None:
        updates.append(("workdir", workdir))

    if not updates:
        return {"ok": False, "error": "No fields to update"}

    updates.append(("updated_at", time.time()))

    set_clause = ", ".join(f"{col} = ?" for col, _ in updates)
    values = [v for _, v in updates] + [job_id]

    conn = _get_conn()
    try:
        cur = conn.execute(
            f"UPDATE cron_jobs SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"ok": False, "error": f"Job '{job_id}' not found"}
    finally:
        conn.close()

    updated_fields = [col for col, _ in updates if col != "updated_at"]
    return {
        "ok": True,
        "id": job_id,
        "updated": updated_fields,
        "message": f"Job '{job_id}' updated: {', '.join(updated_fields)}",
    }


# ── Tool: cron_run ───────────────────────────────────────────────────────────

@register_tool(
    "cron_run",
    schema={
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "Specific job ID to run, or omit for --all",
            },
            "all": {
                "type": "boolean",
                "description": "Run all due jobs",
                "default": False,
            },
        },
    },
    safety_tier="auto",
    timeout=300,
    description="Manually trigger a cron job or run all due jobs",
)
async def cron_run(
    job_id: str | None = None,
    all: bool = False,
) -> dict[str, Any]:
    """Execute a specific job now, or all due jobs if all=True."""
    conn = _get_conn()
    try:
        if job_id:
            row = conn.execute(
                "SELECT * FROM cron_jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if row is None:
                return {"ok": False, "error": f"Job '{job_id}' not found"}
            jobs = [_row_to_dict(row)]
        elif all:
            rows = conn.execute(
                "SELECT * FROM cron_jobs WHERE enabled = 1"
            ).fetchall()
            jobs = [_row_to_dict(r) for r in rows]
            # Filter to only due jobs
            jobs = [j for j in jobs if is_due(j)]
        else:
            return {
                "ok": False,
                "error": "Provide job_id or set all=true to run due jobs",
            }
    finally:
        conn.close()

    if not jobs:
        return {"ok": True, "ran": 0, "message": "No jobs to run"}

    results = []
    for job in jobs:
        result = await _execute_job(job)
        results.append(result)

    succeeded = sum(1 for r in results if r.get("ok"))
    failed = len(results) - succeeded

    return {
        "ok": True,
        "ran": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


async def _execute_job(job: dict[str, Any]) -> dict[str, Any]:
    """Execute a single cron job and record the result."""
    job_id = job["id"]
    now = time.time()

    try:
        if job.get("no_agent"):
            output = _run_watchdog(job)
        else:
            output = await _run_agent(job)

        # Record success
        _record_run(job_id, output, success=True)
        return {
            "ok": True,
            "id": job_id,
            "name": job["name"],
            "output": output,
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        _record_run(job_id, error_msg, success=False)
        return {
            "ok": False,
            "id": job_id,
            "name": job["name"],
            "error": error_msg,
        }


def _run_watchdog(job: dict[str, Any]) -> str:
    """Run a script in watchdog mode. Empty stdout = silent. Non-zero exit = error."""
    script = job.get("script_path", "")
    if not script:
        raise ValueError("Watchdog job has no script_path")

    workdir = job.get("workdir", "") or None
    try:
        result = subprocess.run(
            [script],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=workdir,
            shell=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Script timed out after 300s: {script}")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"Script exited with code {result.returncode}: {stderr or '(no stderr)'}"
        )

    return result.stdout.strip()


async def _run_agent(job: dict[str, Any]) -> str:
    """Run a job in agent mode — execute the prompt via the LLM.

    This is a placeholder that returns the prompt info. In production,
    this would invoke the JEBAT agent pipeline with the configured
    model, skills, and delivery target.
    """
    prompt = job.get("prompt", "")
    model = job.get("model", "")
    skills = job.get("skills", [])
    deliver = job.get("deliver", "")

    # Build execution context
    context = {
        "prompt": prompt,
        "model": model or "(default)",
        "skills": skills,
        "deliver": deliver,
        "job_id": job["id"],
        "job_name": job["name"],
    }

    # NOTE: Actual LLM invocation would happen here via the JEBAT agent pipeline.
    # For now, return a structured acknowledgment so the system is testable.
    return (
        f"[Agent mode] Job '{job['name']}' executed.\n"
        f"Prompt: {prompt}\n"
        f"Model: {model or 'default'}\n"
        f"Skills: {', '.join(skills) if skills else 'none'}\n"
        f"Deliver: {deliver or 'stdout'}"
    )


def _record_run(job_id: str, output: str, success: bool = True) -> None:
    """Record a job execution in the database."""
    now = time.time()
    conn = _get_conn()
    try:
        conn.execute(
            """UPDATE cron_jobs
               SET last_run = ?, last_output = ?, run_count = run_count + 1,
                   updated_at = ?
               WHERE id = ?""",
            (now, output, now, job_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Utility: get_due_jobs ────────────────────────────────────────────────────

def get_due_jobs() -> list[dict[str, Any]]:
    """Return all enabled jobs that are currently due to run.

    Useful for REPL startup checks or external schedulers.
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM cron_jobs WHERE enabled = 1"
        ).fetchall()
    finally:
        conn.close()

    jobs = [_row_to_dict(r) for r in rows]
    return [j for j in jobs if is_due(j)]


# ── Utility: get_job ─────────────────────────────────────────────────────────

def get_job(job_id: str) -> dict[str, Any] | None:
    """Fetch a single job by ID."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM cron_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    job = _row_to_dict(row)
    # Enrich with human-readable timestamps
    job["status"] = "active" if job["enabled"] else "paused"
    if job.get("last_run"):
        job["last_run_iso"] = datetime.fromtimestamp(
            job["last_run"], tz=timezone.utc
        ).isoformat()
    else:
        job["last_run_iso"] = None
    try:
        parsed = parse_schedule(job["schedule"])
        nxt = next_run_time(parsed, job.get("last_run"))
        job["next_run"] = (
            datetime.fromtimestamp(nxt, tz=timezone.utc).isoformat()
            if nxt else None
        )
    except ValueError:
        job["next_run"] = None

    return job
