"""
Terminal UI helpers — ANSI colors, prompts, spinners.
No external dependencies.
"""

import sys
import os

# Disable color if not a TTY or NO_COLOR is set
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


class C:
    RESET  = "\033[0m"  if USE_COLOR else ""
    BOLD   = "\033[1m"  if USE_COLOR else ""
    DIM    = "\033[2m"  if USE_COLOR else ""
    RED    = "\033[91m" if USE_COLOR else ""
    GREEN  = "\033[92m" if USE_COLOR else ""
    YELLOW = "\033[93m" if USE_COLOR else ""
    CYAN   = "\033[96m" if USE_COLOR else ""
    WHITE  = "\033[97m" if USE_COLOR else ""


def header(text: str):
    print(f"\n{C.BOLD}{C.CYAN}{text}{C.RESET}")
    print(f"{C.DIM}{'─' * len(text)}{C.RESET}")


def ok(text: str):
    print(f"  {C.GREEN}✓{C.RESET}  {text}")


def warn(text: str):
    print(f"  {C.YELLOW}!{C.RESET}  {text}")


def err(text: str):
    print(f"  {C.RED}✗{C.RESET}  {text}", file=sys.stderr)


def info(text: str):
    print(f"  {C.DIM}·{C.RESET}  {text}")


def label(text: str):
    print(f"\n{C.BOLD}{text}{C.RESET}")


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {C.CYAN}?{C.RESET}  {prompt}{hint}: ").strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def ask_yn(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        val = input(f"  {C.CYAN}?{C.RESET}  {prompt} [{hint}]: ").strip().lower()
        if not val:
            return default
        return val in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def choose(prompt: str, options: list[tuple[str, str]], allow_multi: bool = False) -> list[str]:
    """
    Present a numbered menu. Returns list of selected keys.
    options: [(key, label), ...]
    """
    print(f"\n  {C.BOLD}{prompt}{C.RESET}")
    for i, (key, label_text) in enumerate(options, 1):
        print(f"    {C.CYAN}{i}{C.RESET}) {label_text}")
    if allow_multi:
        print(f"    {C.CYAN}a{C.RESET}) All")

    hint = "number(s) e.g. 1 3" if allow_multi else "number"
    try:
        raw = input(f"\n  {C.CYAN}?{C.RESET}  Choose ({hint}): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

    if allow_multi and raw == "a":
        return [k for k, _ in options]

    selected = []
    for part in raw.replace(",", " ").split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(options):
                selected.append(options[idx][0])
        except ValueError:
            pass
    return selected


def divider():
    print(f"\n{C.DIM}{'─' * 50}{C.RESET}")
