#!/usr/bin/env python3
"""
JEBAT Adapter Installer
Installs JEBAT adapter files into any project for supported IDEs and clients.

Usage:
    python install.py --ide cursor --target /path/to/your/project
    python install.py --ide vscode --target /path/to/your/project
    python install.py --ide zed    --target /path/to/your/project
    python install.py --ide all    --target /path/to/your/project
    python install.py --print                  # Print universal prompt to stdout
    python validate.py                         # Validate adapter drift locally
"""

import argparse
import shutil
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ADAPTERS_DIR = SCRIPT_DIR

IDE_CONFIGS = {
    "cursor": {
        "src": ADAPTERS_DIR / "cursor" / ".cursorrules",
        "dest": ".cursorrules",
        "note": "Cursor will auto-load .cursorrules from project root. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
    "vscode": {
        "src": ADAPTERS_DIR / "vscode" / "copilot-instructions.md",
        "dest": ".github/copilot-instructions.md",
        "note": "GitHub Copilot reads .github/copilot-instructions.md automatically. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
    "zed": {
        "src": ADAPTERS_DIR / "zed" / "system-prompt.md",
        "dest": ".zed/jebat-system-prompt.md",
        "note": "Paste the contents into Zed -> Settings -> assistant system_prompt. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
    "trae": {
        "src": ADAPTERS_DIR / "generic" / "JEBAT.md",
        "dest": ".trae/jebat-context.md",
        "note": "Paste the SYSTEM PROMPT block into Trae's custom instructions field. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
    "antigravity": {
        "src": ADAPTERS_DIR / "generic" / "JEBAT.md",
        "dest": ".antigravity/jebat-context.md",
        "note": "Paste the SYSTEM PROMPT block into your Antigravity AI context. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
    "generic": {
        "src": ADAPTERS_DIR / "generic" / "JEBAT.md",
        "dest": "JEBAT-CONTEXT.md",
        "note": "Paste the SYSTEM PROMPT block into your LLM interface's system prompt. This adapter follows the shared JEBAT core, routing, templates, and checklists.",
    },
}


def install(ide: str, target: Path):
    if ide == "all":
        for name in IDE_CONFIGS:
            install(name, target)
        return

    if ide not in IDE_CONFIGS:
        print(f"Unknown IDE: {ide}. Choose from: {', '.join(IDE_CONFIGS.keys())}, all")
        sys.exit(1)

    cfg = IDE_CONFIGS[ide]
    dest_path = target / cfg["dest"]
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cfg["src"], dest_path)
    print(f"[{ide}] Installed → {dest_path}")
    print(f"       {cfg['note']}")
    print()


def print_universal():
    prompt_file = ADAPTERS_DIR / "jebat-universal-prompt.md"
    print(prompt_file.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Install shared-core JEBAT adapters for your IDE or client")
    parser.add_argument("--ide", choices=list(IDE_CONFIGS.keys()) + ["all"],
                        help="Target IDE")
    parser.add_argument("--target", type=Path, default=Path.cwd(),
                        help="Target project directory (default: current directory)")
    parser.add_argument("--print", action="store_true",
                        help="Print universal system prompt to stdout")
    args = parser.parse_args()

    if args.print:
        print_universal()
        return

    if not args.ide:
        parser.print_help()
        sys.exit(1)

    if not args.target.is_dir():
        print(f"Target directory not found: {args.target}")
        sys.exit(1)

    install(args.ide, args.target)
    print("Done. JEBAT ⚔️ is now armed in this project.")


if __name__ == "__main__":
    main()
