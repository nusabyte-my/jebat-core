"""
JEBAT — git integration for auto-commit after file operations.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional, List


def _run_git(args: List[str], cwd: Optional[str] = None, timeout: int = 30) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "git not found"
    except subprocess.TimeoutExpired:
        return -1, "", f"git timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def is_git_repo(path: str = ".") -> bool:
    """Check if path is inside a git repository."""
    code, _, _ = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0


def has_uncommitted_changes(path: str = ".") -> bool:
    """Check if there are uncommitted changes."""
    code, output, _ = _run_git(["status", "--porcelain"], cwd=path)
    return code == 0 and bool(output.strip())


def get_changed_files(path: str = ".") -> List[str]:
    """Get list of changed (untracked + modified) files."""
    code, output, _ = _run_git(["status", "--porcelain"], cwd=path)
    if code != 0:
        return []
    files = []
    for line in output.splitlines():
        if line.strip():
            # Status is first 2 chars, filename is after
            filename = line[3:].strip()
            if filename:
                files.append(filename)
    return files


def stage_files(files: List[str], path: str = ".") -> bool:
    """Stage specific files."""
    if not files:
        return True
    code, _, err = _run_git(["add"] + files, cwd=path)
    return code == 0


def stage_all(path: str = ".") -> bool:
    """Stage all changes."""
    code, _, _ = _run_git(["add", "-A"], cwd=path)
    return code == 0


def commit(message: str, path: str = ".") -> tuple[bool, str]:
    """Create a git commit. Returns (success, output)."""
    code, output, err = _run_git(["commit", "-m", message], cwd=path)
    if code == 0:
        return True, output
    return False, err or output


def auto_commit(message: str = "JEBAT: auto-save", path: str = ".") -> tuple[bool, str]:
    """Stage all changes and commit. Returns (success, output)."""
    if not is_git_repo(path):
        return False, "Not a git repository"
    if not has_uncommitted_changes(path):
        return True, "No changes to commit"
    if not stage_all(path):
        return False, "Failed to stage files"
    return commit(message, path)


def commit_if_changed(message: str, files: List[str], path: str = ".") -> tuple[bool, str]:
    """Stage specific files and commit only if there are changes."""
    if not is_git_repo(path):
        return False, "Not a git repository"
    if not files:
        return True, "No files to commit"
    if not stage_files(files, path):
        return False, "Failed to stage files"
    if not has_uncommitted_changes(path):
        return True, "No changes after staging"
    return commit(message, path)
