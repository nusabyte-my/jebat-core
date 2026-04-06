#!/usr/bin/env python3
"""
JEBAT CLI ⚔️
Installs JEBAT context into your IDE or project.

Commands:
  jebat install           Interactive wizard
  jebat install --ide <name> --target <path>
  jebat detect            Show detected IDEs on this machine
  jebat prompt            Print universal system prompt to stdout

Usage:
  python jebat.py install
  python jebat.py install --ide cursor --target ./myproject
  python jebat.py install --ide all --target ./myproject
  python jebat.py detect
  python jebat.py prompt
"""

import sys
import argparse
from pathlib import Path

# Force UTF-8 on Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent))

from detect import detect_all, IDEInfo
from installer import install_to_project, install_global, read_universal_prompt
import ui


SUPPORTED_IDES = ["cursor", "vscode", "zed", "trae", "antigravity"]


# ─────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────

def cmd_detect():
    ui.header("JEBAT ⚔️  — IDE Detection")
    ides = detect_all()
    found = 0
    for key, info in ides.items():
        if info.detected:
            ui.ok(f"{ui.C.BOLD}{info.name}{ui.C.RESET}  {ui.C.DIM}{info.install_path or 'in PATH'}{ui.C.RESET}")
            found += 1
        else:
            ui.info(f"{ui.C.DIM}{info.name} — not detected{ui.C.RESET}")
    ui.divider()
    print(f"\n  Found {ui.C.BOLD}{found}{ui.C.RESET} IDE(s).\n")


def cmd_prompt():
    print(read_universal_prompt())


def cmd_install_direct(ide_keys: list[str], target: Path, scope: str):
    ides = detect_all()
    ui.header(f"JEBAT ⚔️  — Installing ({scope})")

    for key in ide_keys:
        if key not in ides:
            ui.err(f"Unknown IDE: {key}")
            continue
        info = ides[key]
        _do_install(info, target, scope)

    ui.divider()
    print(f"\n  {ui.C.GREEN}{ui.C.BOLD}Done. JEBAT ⚔️ armed.{ui.C.RESET}\n")


def cmd_install_wizard():
    ui.header("JEBAT ⚔️  — Installer Wizard")

    ides = detect_all()
    detected = [(k, v) for k, v in ides.items() if v.detected]
    undetected = [(k, v) for k, v in ides.items() if not v.detected]

    # Build options list — detected first, then rest
    options = []
    for k, v in detected:
        options.append((k, f"{ui.C.BOLD}{v.name}{ui.C.RESET} {ui.C.GREEN}(detected){ui.C.RESET}"))
    for k, v in undetected:
        options.append((k, f"{v.name} {ui.C.DIM}(not detected){ui.C.RESET}"))

    selected_keys = ui.choose(
        "Which IDE(s) to install for?",
        options,
        allow_multi=True,
    )

    if not selected_keys:
        ui.warn("Nothing selected. Exiting.")
        return

    # Scope
    scope_options = [
        ("project", "Project  — install into a specific project directory"),
        ("global",  "Global   — install into IDE's global config (where supported)"),
    ]
    scope_sel = ui.choose("Install scope?", scope_options)
    scope = scope_sel[0] if scope_sel else "project"

    target = Path.cwd()
    if scope == "project":
        raw = ui.ask("Target project path", default=str(Path.cwd()))
        target = Path(raw).expanduser().resolve()
        if not target.is_dir():
            ui.err(f"Directory not found: {target}")
            sys.exit(1)

    ui.divider()
    ui.label("Installing...")

    for key in selected_keys:
        _do_install(ides[key], target, scope)

    ui.divider()
    print(f"\n  {ui.C.GREEN}{ui.C.BOLD}Done. JEBAT ⚔️ armed.{ui.C.RESET}\n")

    # Post-install hints
    for key in selected_keys:
        info = ides[key]
        if info.global_note:
            ui.info(f"{info.name}: {info.global_note}")
    print()


def _do_install(info: IDEInfo, target: Path, scope: str):
    try:
        if scope == "global":
            result = install_global(info)
            if result is None:
                ui.warn(f"{info.name}: global install not supported — falling back to project.")
                result = install_to_project(info, target)
        else:
            result = install_to_project(info, target)

        for path in result:
            ui.ok(f"{ui.C.BOLD}{info.name}{ui.C.RESET} → {ui.C.DIM}{path}{ui.C.RESET}")

    except FileNotFoundError as e:
        ui.err(f"{info.name}: {e}")
    except Exception as e:
        ui.err(f"{info.name}: unexpected error — {e}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="jebat",
        description="JEBAT ⚔️  — Install JEBAT context into your IDE or project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python jebat.py install                          interactive wizard
  python jebat.py install --ide cursor             wizard for Cursor only
  python jebat.py install --ide all --target ./x   install all to ./x
  python jebat.py install --ide vscode --global    global VS Code install
  python jebat.py detect                           show detected IDEs
  python jebat.py prompt                           print universal prompt
        """,
    )

    sub = parser.add_subparsers(dest="command")

    # install
    p_install = sub.add_parser("install", help="Install JEBAT context")
    p_install.add_argument(
        "--ide",
        choices=SUPPORTED_IDES + ["all"],
        help="Target IDE (omit for interactive wizard)",
    )
    p_install.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        metavar="PATH",
        help="Target project directory (default: current directory)",
    )
    p_install.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Install to IDE's global config instead of a project",
    )

    # detect
    sub.add_parser("detect", help="Show detected IDEs on this machine")

    # prompt
    sub.add_parser("prompt", help="Print universal system prompt to stdout")

    args = parser.parse_args()

    if args.command == "detect":
        cmd_detect()

    elif args.command == "prompt":
        cmd_prompt()

    elif args.command == "install":
        scope = "global" if args.global_install else "project"
        if args.ide:
            keys = SUPPORTED_IDES if args.ide == "all" else [args.ide]
            cmd_install_direct(keys, args.target, scope)
        else:
            cmd_install_wizard()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
