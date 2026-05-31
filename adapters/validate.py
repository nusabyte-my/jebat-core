#!/usr/bin/env python3
"""
Validate that adapter files still reference the shared JEBAT operating model.

This is a lightweight drift check, not a semantic parser.
"""

from pathlib import Path


ROOT = Path(__file__).parent

FILES = {
    "universal": ROOT / "jebat-universal-prompt.md",
    "generic": ROOT / "generic" / "JEBAT.md",
    "cursor": ROOT / "cursor" / ".cursorrules",
    "vscode": ROOT / "vscode" / "copilot-instructions.md",
    "zed": ROOT / "zed" / "system-prompt.md",
}

REQUIRED_PATTERNS = [
    "Panglima",
    "vault/playbooks/dispatch-matrix.md",
    "vault/checklists/",
    "vault/templates/",
    "jebat-gateway.json",
]


def main() -> int:
    failures: list[str] = []

    for label, path in FILES.items():
        if not path.exists():
            failures.append(f"[{label}] missing file: {path}")
            continue

        text = path.read_text(encoding="utf-8")
        for pattern in REQUIRED_PATTERNS:
            if pattern not in text:
                failures.append(f"[{label}] missing pattern: {pattern}")

    if failures:
        print("Adapter validation failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Adapter validation passed.")
    print("Checked files:")
    for label, path in FILES.items():
        print(f"- {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
