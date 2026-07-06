"""JEBAT Git Integration — PendekarGit (Code Warrior).

Git tools for commit, diff, blame, log, apply, branch management.
Essential for any coding CLI agent — table stakes alongside Hermes/Claude Code/Codex.
"""

import json
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jebat.tools import register_tool, ToolDef

# ─── Git Tool Definitions ───

GIT_TOOLS: list[ToolDef] = []

# 1. git_commit — commit staged changes with auto-generated or user message
GIT_TOOLS.append(ToolDef(
    name="git_commit",
    description="Commit staged changes to git. Auto-generates message from diff if none provided.",
    schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message. If omitted, auto-generated from staged diff."},
            "allow_empty": {"type": "boolean", "description": "Allow empty commits (default false).", "default": False},
            "amend": {"type": "boolean", "description": "Amend the previous commit (default false).", "default": False},
        },
        "required": [],
    },
    safety_tier="confirm",
))

# 2. git_diff — show diff of staged, unstaged, or specific commits
GIT_TOOLS.append(ToolDef(
    name="git_diff",
    description="Show git diff — staged, unstaged, or between commits.",
    schema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "What to diff: 'staged', 'unstaged', 'HEAD', or a commit SHA.", "default": "unstaged"},
            "file": {"type": "string", "description": "Optional file path to restrict diff to."},
            "stat": {"type": "boolean", "description": "Show stat summary instead of full diff (default false).", "default": False},
        },
        "required": [],
    },
    safety_tier="auto",
))

# 3. git_log — show commit history
GIT_TOOLS.append(ToolDef(
    name="git_log",
    description="Show git commit log with author, date, message.",
    schema={
        "type": "object",
        "properties": {
            "count": {"type": "integer", "description": "Number of commits to show (default 10).", "default": 10},
            "author": {"type": "string", "description": "Filter by author name/email."},
            "since": {"type": "string", "description": "Show commits since date (e.g. '2 weeks ago')."},
            "file": {"type": "string", "description": "Show only commits touching this file."},
            "oneline": {"type": "boolean", "description": "One-line per commit (default true).", "default": True},
        },
        "required": [],
    },
    safety_tier="auto",
))

# 4. git_blame — show who wrote each line of a file
GIT_TOOLS.append(ToolDef(
    name="git_blame",
    description="Show git blame — who wrote each line of a file, when, and which commit.",
    schema={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "File path to blame."},
            "range": {"type": "string", "description": "Line range (e.g. '10,20')."},
        },
        "required": ["file"],
    },
    safety_tier="auto",
))

# 5. git_status — show working tree status
GIT_TOOLS.append(ToolDef(
    name="git_status",
    description="Show git working tree status — staged, unstaged, untracked files.",
    schema={
        "type": "object",
        "properties": {
            "short": {"type": "boolean", "description": "Short format (default true).", "default": True},
        },
        "required": [],
    },
    safety_tier="auto",
))

# 6. git_branch — list, create, or switch branches
GIT_TOOLS.append(ToolDef(
    name="git_branch",
    description="List, create, or switch git branches.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Action: 'list', 'create', 'switch', 'delete'.", "default": "list"},
            "name": {"type": "string", "description": "Branch name (for create/switch/delete)."},
            "remote": {"type": "boolean", "description": "Include remote branches in list (default false).", "default": False},
        },
        "required": [],
    },
    safety_tier="confirm",
))

# 7. git_apply — apply a patch or stash
GIT_TOOLS.append(ToolDef(
    name="git_apply",
    description="Apply a patch file or git stash to the working tree.",
    schema={
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Patch file path or 'stash' to apply latest stash."},
            "check": {"type": "boolean", "description": "Check if patch applies cleanly without actually applying (default false).", "default": False},
        },
        "required": ["source"],
    },
    safety_tier="confirm",
))

# 8. git_stash — stash or pop working changes
GIT_TOOLS.append(ToolDef(
    name="git_stash",
    description="Stash, pop, or list git stashes.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Action: 'push', 'pop', 'list', 'drop'.", "default": "push"},
            "message": {"type": "string", "description": "Stash message (for push)."},
            "index": {"type": "integer", "description": "Stash index (for pop/drop, default 0 = latest).", "default": 0},
        },
        "required": [],
    },
    safety_tier="auto",
))

# Register all git tools
for tool_def in GIT_TOOLS:
    register_tool(tool_def)


# ─── Tool Implementations ───

def _run_git(cmd: list[str], cwd: str | None = None, timeout: int = 30) -> dict[str, Any]:
    """Run a git command and return structured result."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or os.getcwd(),
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "git command timed out", "success": False}
    except FileNotFoundError:
        return {"exit_code": -1, "stdout": "", "stderr": "git not found — is git installed?", "success": False}


def _auto_message_from_diff() -> str:
    """Generate commit message from staged diff stats."""
    r = _run_git(["diff", "--cached", "--stat"])
    if not r["success"] or not r["stdout"]:
        return "chore: auto-commit"
    
    lines = r["stdout"].split("\n")
    # Extract file names and changes
    files = []
    for line in lines[:-1]:  # skip summary line
        parts = line.strip().split("|")
        if len(parts) >= 2:
            fname = parts[0].strip()
            changes = parts[1].strip()
            files.append(f"{fname} ({changes})")
    
    if len(files) <= 3:
        return f"chore: update {', '.join(files)}"
    else:
        return f"chore: update {len(files)} files"


def git_commit(**kwargs) -> dict[str, Any]:
    """Commit staged changes."""
    message = kwargs.get("message") or _auto_message_from_diff()
    allow_empty = kwargs.get("allow_empty", False)
    amend = kwargs.get("amend", False)
    
    cmd = ["commit", "-m", message]
    if allow_empty:
        cmd.append("--allow-empty")
    if amend:
        cmd.append("--amend")
    
    r = _run_git(cmd)
    if r["success"]:
        # Get the commit SHA
        sha_r = _run_git(["rev-parse", "HEAD"])
        sha = sha_r["stdout"][:7] if sha_r["success"] else "unknown"
        r["commit_sha"] = sha
        r["message"] = message
    return r


def git_diff(**kwargs) -> dict[str, Any]:
    """Show git diff."""
    target = kwargs.get("target", "unstaged")
    file_path = kwargs.get("file")
    stat = kwargs.get("stat", False)
    
    cmd = ["diff"]
    if target == "staged":
        cmd.append("--cached")
    elif target != "unstaged":
        cmd.extend([target])  # commit SHA
    
    if stat:
        cmd.append("--stat")
    
    if file_path:
        cmd.append(file_path)
    
    r = _run_git(cmd, timeout=60)
    if r["success"]:
        # Truncate very long diffs
        if len(r["stdout"]) > 5000 and not stat:
            r["stdout"] = r["stdout"][:5000] + "\n... (truncated, use stat=true for summary)"
        r["diff_lines"] = len(r["stdout"].split("\n"))
    return r


def git_log(**kwargs) -> dict[str, Any]:
    """Show git log."""
    count = kwargs.get("count", 10)
    author = kwargs.get("author")
    since = kwargs.get("since")
    file_path = kwargs.get("file")
    oneline = kwargs.get("oneline", True)
    
    cmd = ["log"]
    if oneline:
        cmd.append("--oneline")
    cmd.append(f"-{count}")
    
    if author:
        cmd.extend(["--author", author])
    if since:
        cmd.extend(["--since", since])
    if file_path:
        cmd.extend(["--", file_path])
    
    r = _run_git(cmd)
    if r["success"] and not oneline:
        # Parse structured log
        commits = []
        for block in r["stdout"].split("\n\n"):
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                sha_match = re.match(r"commit ([a-f0-9]+)", lines[0])
                author_match = re.match(r"Author: (.+)", lines[1])
                date_match = re.match(r"Date: (.+)", lines[2])
                msg = "\n".join(lines[3:]).strip()
                commits.append({
                    "sha": sha_match.group(1)[:7] if sha_match else "?",
                    "author": author_match.group(1) if author_match else "?",
                    "date": date_match.group(1) if date_match else "?",
                    "message": msg,
                })
        r["commits"] = commits
    return r


def git_blame(**kwargs) -> dict[str, Any]:
    """Show git blame."""
    file_path = kwargs.get("file")
    range_spec = kwargs.get("range")
    
    cmd = ["blame", file_path]
    if range_spec:
        cmd.extend(["-L", range_spec])
    
    r = _run_git(cmd, timeout=30)
    if r["success"]:
        # Parse blame into structured data
        lines = []
        for line in r["stdout"].split("\n"):
            # Format: sha (author date line) code
            match = re.match(r"^([a-f0-9]+)\s+\((.+?\s+\d{4}-\d{2}-\d{2}\s+\d+)\)\s+(.*)$", line)
            if match:
                sha = match.group(1)[:7]
                meta = match.group(2).strip()
                code = match.group(3)
                lines.append({"sha": sha, "meta": meta, "code": code})
        r["blame_lines"] = lines
        # Truncate if too many
        if len(r["stdout"]) > 5000:
            r["stdout"] = r["stdout"][:5000] + "\n... (truncated)"
    return r


def git_status(**kwargs) -> dict[str, Any]:
    """Show git status."""
    short = kwargs.get("short", True)
    
    cmd = ["status"]
    if short:
        cmd.append("--short")
        cmd.append("--branch")
    
    r = _run_git(cmd)
    if r["success"] and short:
        # Parse short status
        files = []
        for line in r["stdout"].split("\n"):
            if line.startswith("##"):
                r["branch"] = line[3:]
            elif len(line) >= 3:
                status = line[:2]
                fname = line[3:]
                files.append({"status": status, "file": fname})
        r["files"] = files
    return r


def git_branch(**kwargs) -> dict[str, Any]:
    """Manage git branches."""
    action = kwargs.get("action", "list")
    name = kwargs.get("name")
    remote = kwargs.get("remote", False)
    
    if action == "list":
        cmd = ["branch"]
        if remote:
            cmd.append("-r")
        cmd.append("--list")
        r = _run_git(cmd)
        if r["success"]:
            branches = [b.strip().lstrip("* ") for b in r["stdout"].split("\n") if b.strip()]
            r["branches"] = branches
        return r
    elif action == "create" and name:
        r = _run_git(["checkout", "-b", name])
        r["action"] = "created_and_switched"
        r["branch"] = name
        return r
    elif action == "switch" and name:
        r = _run_git(["checkout", name])
        r["action"] = "switched"
        r["branch"] = name
        return r
    elif action == "delete" and name:
        r = _run_git(["branch", "-d", name])
        r["action"] = "deleted"
        r["branch"] = name
        return r
    else:
        return {"success": False, "stderr": f"Invalid action '{action}' or missing branch name"}


def git_apply(**kwargs) -> dict[str, Any]:
    """Apply a patch or stash."""
    source = kwargs.get("source")
    check = kwargs.get("check", False)
    
    if source == "stash":
        cmd = ["stash", "pop"]
        r = _run_git(cmd)
        return r
    
    # Apply a patch file
    cmd = ["apply"]
    if check:
        cmd.append("--check")
    cmd.append(source)
    
    r = _run_git(cmd)
    return r


def git_stash(**kwargs) -> dict[str, Any]:
    """Manage git stashes."""
    action = kwargs.get("action", "push")
    message = kwargs.get("message")
    index = kwargs.get("index", 0)
    
    if action == "push":
        cmd = ["stash", "push"]
        if message:
            cmd.extend(["-m", message])
        r = _run_git(cmd)
        return r
    elif action == "pop":
        cmd = ["stash", "pop"]
        if index > 0:
            cmd.append(f"stash@{index}")
        r = _run_git(cmd)
        return r
    elif action == "list":
        r = _run_git(["stash", "list"])
        if r["success"]:
            stashes = []
            for line in r["stdout"].split("\n"):
                if line.strip():
                    stashes.append(line.strip())
            r["stashes"] = stashes
        return r
    elif action == "drop":
        cmd = ["stash", "drop", f"stash@{index}"]
        r = _run_git(cmd)
        return r
    else:
        return {"success": False, "stderr": f"Invalid stash action: {action}"}


# ─── Module Register ────────────────────────────────────────────────────

# Wire tool handlers to ToolDefs and register in global TOOL_REGISTRY
import asyncio
from jebat.tools import register_tool

_HANDLER_MAP = {
    "git_commit": git_commit,
    "git_diff": git_diff,
    "git_log": git_log,
    "git_blame": git_blame,
    "git_status": git_status,
    "git_branch": git_branch,
    "git_apply": git_apply,
    "git_stash": git_stash,
}

def _make_async(fn):
    """Wrap a sync function into an async one for ToolDef.handler compatibility."""
    async def wrapper(**kwargs):
        return fn(**kwargs)
    return wrapper

for tool_def in GIT_TOOLS:
    handler = _HANDLER_MAP.get(tool_def.name)
    if handler:
        async_handler = _make_async(handler)
        tool_def.handler = async_handler
        register_tool(
            tool_def.name,
            handler=async_handler,
            schema=tool_def.schema,
            safety_tier=tool_def.safety_tier,
            timeout=tool_def.timeout,
            description=tool_def.description,
        )

print(f"[PendekarGit] 8 git tools registered: commit, diff, log, blame, status, branch, apply, stash")