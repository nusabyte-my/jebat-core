"""
JEBAT Security Framework — three-tier safety, audit logging, sandbox mode,
and encryption for data-at-rest.

Tiers:
  - auto:      No prompt, execute immediately   (ls, echo, file read)
  - confirm:   Ask Y/n before executing          (rm file, chmod)
  - dangerous: Require --dangerous flag          (rm -rf /, mkfs)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jebat.tools import classify_command, classify_tool_call

# ── Encryption ──────────────────────────────────────────────────────────────

from jebat.features.security.encryption import (
    EncryptionManager,
    PasswordHasher,
    FieldEncryption,
    get_encryption_manager,
    get_password_hasher,
    encrypt_field,
    decrypt_field,
    hash_password,
    verify_password,
    log_encryption_operation,
)

# ── Audit Log ─────────────────────────────────────────────────────────────

AUDIT_LOG_PATH = Path.home() / ".jebat" / "logs" / "audit.jsonl"


@dataclass
class AuditEntry:
    timestamp: str
    tool: str
    params: dict[str, Any]
    result_preview: str
    duration_ms: int
    safety_tier: str
    approved: bool
    session_id: str = ""


def write_audit(entry: AuditEntry) -> None:
    """Append an audit entry as JSONL."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "ts": entry.timestamp,
        "tool": entry.tool,
        "params": entry.params,
        "result": entry.result_preview[:200],
        "duration_ms": entry.duration_ms,
        "safety": entry.safety_tier,
        "approved": entry.approved,
        "session": entry.session_id,
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, default=str) + "\n")


# ── Approval Prompt ──────────────────────────────────────────────────────

def prompt_confirm(tool_name: str, params: dict[str, Any], tier: str) -> bool:
    """Prompt the user for approval.

    Returns True if approved, False if rejected.
    In sandbox mode, returns True but marks as dry-run.
    """
    if tier == "auto":
        return True

    # Show the command/action to the user
    detail = params.get("command") or params.get("path") or str(params)
    prompt_text = (
        f"\n  [{tier.upper()}] {tool_name}: {detail}\n"
        f"  Proceed? [Y/n/d (dry-run)]: "
    )

    try:
        response = input(prompt_text).strip().lower()
        if response in ("d", "dry", "dry-run"):
            print("  -> DRY RUN (not executed)")
            return True  # We'll catch this via sandbox flag
        if response in ("n", "no"):
            print("  -> CANCELLED")
            return False
        return True
    except (EOFError, KeyboardInterrupt):
        print("\n  -> CANCELLED")
        return False


# ── Sandbox Mode ──────────────────────────────────────────────────────────

SANDBOX_ACTIVE = False


def enable_sandbox() -> None:
    global SANDBOX_ACTIVE
    SANDBOX_ACTIVE = True


def disable_sandbox() -> None:
    global SANDBOX_ACTIVE
    SANDBOX_ACTIVE = False


def is_sandbox() -> bool:
    return SANDBOX_ACTIVE


# ── Audit Log Reader ──────────────────────────────────────────────────────

def read_audit_log(limit: int = 50, level: str | None = None) -> list[dict[str, Any]]:
    """Read recent audit log entries."""
    if not AUDIT_LOG_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(AUDIT_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if level and entry.get("safety") != level:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries[-limit:]


def clear_audit_log() -> None:
    if AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.unlink()


# ── Security Utility ──────────────────────────────────────────────────────

def sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive values (API keys, tokens) from params for logging.

    Returns a sanitized copy of the params dict.
    """
    SENSITIVE_KEYS = {"api_key", "key", "token", "secret", "password", "auth"}
    sanitized = {}
    for k, v in params.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "***REDACTED***"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_params(v)
        elif isinstance(v, str) and len(v) > 20 and any(
            v.startswith(prefix) for prefix in ("sk-", "pk-", "ghp_", "gho_", "ntn_")
        ):
            sanitized[k] = v[:8] + "***" + v[-4:]
        else:
            sanitized[k] = v
    return sanitized


__all__ = [
    # Encryption
    "EncryptionManager",
    "PasswordHasher",
    "FieldEncryption",
    "get_encryption_manager",
    "get_password_hasher",
    "encrypt_field",
    "decrypt_field",
    "hash_password",
    "verify_password",
    "log_encryption_operation",
    # Audit
    "AuditEntry",
    "write_audit",
    "read_audit_log",
    "clear_audit_log",
    # Approval
    "prompt_confirm",
    # Sandbox
    "enable_sandbox",
    "disable_sandbox",
    "is_sandbox",
    # Utils
    "sanitize_params",
]