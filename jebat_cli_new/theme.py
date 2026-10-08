"""
JEBAT — Unified Theme and Visual Primitives.
Colors, boxes, cards, spinners, and stream formatting.
"""

from __future__ import annotations

import difflib
import json
import os
import random
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Rich backend (optional, graceful fallback) ──────────────────
try:
    from rich.console import Console as _RichConsole
    from rich.live import Live as _RichLive
    from rich.markdown import Markdown as _RichMarkdown
    from rich.text import Text as _RichText

    _RICH = True
except ImportError:  # pragma: no cover - rich is a declared dep; fallback only
    _RICH = False

_SHARED_RICH_CONSOLE = None


def get_rich_console():
    """Shared rich Console (width-honoring, terminal-aware)."""
    global _SHARED_RICH_CONSOLE
    if _RICH and _SHARED_RICH_CONSOLE is None:
        _SHARED_RICH_CONSOLE = _RichConsole()
    return _SHARED_RICH_CONSOLE


# ─── Color Enforcement & Detection ───────────────────────────────

USE_COLOR = os.environ.get("NO_COLOR") is None and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ─── ANSI Palette ────────────────────────────────────────────────

class C:
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    DIM         = "\033[2m"
    ITALIC      = "\033[3m"
    UNDERL      = "\033[4m"
    CYAN        = "\033[36m"
    MAGENTA     = "\033[35m"
    GREEN       = "\033[32m"
    YELLOW      = "\033[33m"
    RED         = "\033[31m"
    GRAY        = "\033[90m"
    WHITE       = "\033[97m"
    BLUE        = "\033[34m"
    BG_DARK     = "\033[48;5;235m"
    BG_CYAN     = "\033[48;5;30m"
    # Neon accents (256-color)
    NEON_CYAN   = "\033[38;5;51m"
    NEON_PURPLE = "\033[38;5;141m"
    NEON_AMBER  = "\033[38;5;214m"
    NEON_GREEN  = "\033[38;5;46m"
    NEON_PINK   = "\033[38;5;205m"
    # Surface colors
    SURFACE     = "\033[48;5;236m"
    SURFACE2    = "\033[48;5;234m"
    BORDER      = "\033[38;5;238m"
    TEXT_DIM    = "\033[38;5;245m"
    TEXT_MUTED  = "\033[38;5;240m"



# ─── Colour Gate ─────────────────────────────────────────────────

# Alias so callers can use either name.
_COLOR = USE_COLOR
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


# ─── Wrapping ────────────────────────────────────────────────────

def _wrap(text: str, width: int) -> List[str]:
    """Hard-wrap to `width` columns, breaking long tokens rather than overflowing."""
    out: List[str] = []
    for raw in str(text).split("\n"):
        if len(_clean(raw)) <= width:
            out.append(raw)
            continue
        line = ""
        for word in raw.split(" "):
            while len(word) > width:
                if line:
                    out.append(line)
                    line = ""
                out.append(word[:width])
                word = word[width:]
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line += " " + word
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


# ─── Wordmark + Banner ───────────────────────────────────────────

# JEBAT wordmark — ANSI Shadow. Six rows, 38 cols.
_WORDMARK = (
    "██╗ ███████╗██████╗  █████╗ ████████╗",
    "██║ ██╔════╝██╔══██╗██╔══██╗╚══██╔══╝",
    "██║ █████╗  ██████╔╝███████║   ██║   ",
    "██║ ██╔══╝  ██╔══██╗██╔══██║   ██║   ",
    "██║ ███████╗██████╔╝██║  ██║   ██║   ",
    "╚═╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ",
)

# Stealth-Dark Tactical: cyan at the top fading to purple at the base.
_MARK_TOP = (0, 255, 255)
_MARK_BOTTOM = (175, 135, 255)

# Widest row plus its two-space gutter.
WORDMARK_WIDTH = 40


def _lerp256(c1, c2, t):
    """Interpolate two RGB tuples into a 256-colour escape code."""
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return 16 + int(r / 255 * 5) * 36 + int(g / 255 * 5) * 6 + int(b / 255 * 5)


def _terminal_width(default: int = 80) -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default



def boot_animation(rows=None, steps: int = 6, delay: float = 0.04) -> None:
    """Sweep a highlight band across the wordmark once.

    No-op when colour is off or stdout is not a terminal, so piped and JSON
    output never sees cursor movement.
    """
    if not USE_COLOR or not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
        return
    rows = rows or _WORDMARK
    width = max(len(r) for r in rows)
    last = max(1, len(rows) - 1)
    esc, nl = chr(27), chr(10)
    try:
        for step in range(steps):
            head = int((width + 10) * step / steps)
            sys.stdout.write(esc + f"[{len(rows)}A")
            for r_i, row in enumerate(rows):
                base = _lerp256(_MARK_TOP, _MARK_BOTTOM, r_i / last)
                buf = []
                for i, ch in enumerate(row):
                    if ch == " ":
                        buf.append(ch)
                    elif head <= i < head + 10:
                        buf.append(esc + "[38;5;231m" + esc + "[1m" + ch)
                    else:
                        buf.append(esc + f"[38;5;{base}m" + ch)
                sys.stdout.write("  " + "".join(buf) + esc + "[0m" + nl)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(esc + f"[{len(rows)}A")
    except Exception:
        return


def banner(subtitle=None, version=None, style: str = "auto", animate: bool = False):
    """JEBAT banner — wordmark, tagline and optional live-state subtitle.

    style: "art" always, "plain" never, "auto" picks by terminal width and
    colour support. Piped output stays plain so logs stay readable.
    """
    art = style == "art" or (style == "auto" and USE_COLOR
                             and _terminal_width() >= WORDMARK_WIDTH)
    print()
    if art:
        if animate:
            boot_animation()
        last = len(_WORDMARK) - 1
        for i, row in enumerate(_WORDMARK):
            col = _lerp256(_MARK_TOP, _MARK_BOTTOM, i / last)
            print(f"  \033[38;5;{col}m\033[1m{row}\033[0m")
    else:
        print(f"  {C.NEON_CYAN}{C.BOLD}JEBAT{C.RESET}" if USE_COLOR else "  JEBAT")

    dim, reset = (C.DIM, C.RESET) if USE_COLOR else ("", "")
    rule = f"{C.BORDER}┄┄┄{C.RESET} " if USE_COLOR else "--- "
    tail = f"{C.NEON_PURPLE}⚔{C.RESET}  " if USE_COLOR else ""
    ver = f"  {dim}v{version}{reset}" if version else ""
    print()
    print(f"  {rule}{tail}{dim}unified coding agent{reset}{ver}")
    if subtitle:
        print(f"  {dim}{subtitle}{reset}")
    print()


def show_setup(provider_name, model, endpoint, status="Ready"):
    """Setup panel with provider info."""
    _double_box("Setup",
                f"Provider  {provider_name}\nModel     {model}\n"
                f"Endpoint  {endpoint}\n● {status} — type /help to begin")

# ─── Utility Functions ───────────────────────────────────────────

def cprint(*args, **kwargs):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not USE_COLOR:
        args = tuple(re.sub(r"\033\[[0-9;]*m", "", a) if isinstance(a, str) else a
                     for a in args)
    print(*args, **kwargs)


def _clean(s: str) -> str:
    """Strip ANSI escape codes for width calculation."""
    return re.sub(r'\033\[[0-9;]*m', '', s)


def _pad(s: str, width: int) -> str:
    """Pad string to width, accounting for ANSI codes."""
    clean_len = len(_clean(s))
    return s + " " * max(0, width - clean_len)


# ─── Gradient ────────────────────────────────────────────────────

def _gradient(text: str, c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> str:
    """Apply 256-color gradient across text."""
    def _to256(r, g, b):
        return 16 + int(r / 255 * 5) * 36 + int(g / 255 * 5) * 6 + int(b / 255 * 5)
    out = ""
    n = max(1, len(text) - 1)
    for i, ch in enumerate(text):
        if ch == " ":
            out += ch
            continue
        t = i / n
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        out += f"\033[38;5;{_to256(r, g, b)}m{ch}"
    out += "\033[0m"
    return out


# ─── Visual Primitives & Panels ──────────────────────────────────

PANEL_THEMES = {
    "default": (C.CYAN, C.DIM),        # cyan border
    "success": (C.GREEN, C.DIM),        # green border
    "warning": (C.YELLOW, C.DIM),       # yellow border
    "error":   (C.RED, C.DIM),          # red border
    "info":    (C.NEON_CYAN, C.DIM),    # neon cyan
    "special": (C.NEON_PURPLE, C.DIM),  # purple
    "accent":  (C.NEON_AMBER, C.DIM),   # amber
}


def box(title, text, width=72, theme="default"):
    """Box with colored border. Every line is exactly `width` columns."""
    border_color, _ = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    inner = w - 2
    label = f"── {_clean(title)} "
    print(f"{border_color}╭{label}" + "─" * max(0, inner - len(label)) + f"╮{C.RESET}")
    for line in text.split("\n"):
        pad = max(0, inner - 1 - len(_clean(line)))
        print(f"{border_color}│{C.RESET} {line}{' ' * pad}{border_color}│{C.RESET}")
    print(f"{border_color}╰" + "─" * inner + f"╯{C.RESET}")


def panel(title: str, text: str, width: int = 72, theme: str = "default"):
    """Alias for box with title."""
    box(title, text, width, theme)


def _double_box(title, text, width=72, theme="default"):
    """Double-bordered box. Every line is exactly `width` columns."""
    border_color, _ = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    inner = w - 2
    print(f"{border_color}╔{'═' * inner}╗{C.RESET}")
    label = f"  {_clean(title)}"
    print(f"{border_color}║{C.RESET}{label}{' ' * max(0, inner - len(label))}{border_color}║{C.RESET}")
    print(f"{border_color}╠{'═' * inner}╣{C.RESET}")
    for line in text.split("\n"):
        pad = max(0, inner - 1 - len(_clean(line)))
        print(f"{border_color}║{C.RESET} {line}{' ' * pad}{border_color}║{C.RESET}")
    print(f"{border_color}╚{'═' * inner}╝{C.RESET}")


def _info_panel(title, items, width=72, theme="info"):
    """Panel of key/value rows. Every line is exactly `width` columns."""
    border_color, _ = PANEL_THEMES.get(theme, PANEL_THEMES["default"])
    w = width
    inner = w - 2
    label = f"── {_clean(title)} "
    print(f"{border_color}╭{label}" + "─" * max(0, inner - len(label)) + f"╮{C.RESET}")
    for item_label, value in items:
        pad_label = max(1, 14 - len(str(item_label)))
        plain = f"  {item_label}{' ' * pad_label}{value}"
        pad = max(0, inner - len(plain))
        line = f"  {C.CYAN}{item_label}{C.RESET}{' ' * pad_label}{value}"
        print(f"{border_color}│{C.RESET}{line}{' ' * pad}{border_color}│{C.RESET}")
    print(f"{border_color}╰" + "─" * inner + f"╯{C.RESET}")


# ─── Formatting Helpers ──────────────────────────────────────────

def format_cost(usd: float) -> str:
    """Format cost in USD."""
    return f"${usd:.4f}" if usd > 0 else "$0.0000"


def _format_model_row(idx: int, model: Tuple[Any, ...], current_model: Optional[str] = None) -> str:
    """Format a model row for display."""
    mid, name, ctx, max_out, in_cost, out_cost, caps = model
    is_current = (mid == current_model)
    marker = f" {C.GREEN}●{C.RESET}" if is_current else " "
    # Context window display
    if ctx >= 1000000:
        ctx_str = f"{ctx//1000000}M"
    elif ctx >= 1000:
        ctx_str = f"{ctx//1000}K"
    else:
        ctx_str = str(ctx)
    # Cost display
    if in_cost == 0 and out_cost == 0:
        cost_str = f"{C.GREEN}FREE{C.RESET}"
    else:
        cost_str = f"${in_cost:.2f}/${out_cost:.2f}"
    # Capabilities
    cap_str = " ".join(f"{C.DIM}[{c}]{C.RESET}" for c in caps)
    return f"  {C.CYAN}{idx:2d}{C.RESET}{marker} {C.BOLD}{name:28s}{C.RESET} {C.DIM}{mid:35s}{C.RESET} ctx:{ctx_str:>6s} {cost_str:>20s} {cap_str}"


# ─── Status Line & Bottom Bar ────────────────────────────────────

def status_line(iters: int, tokens: int, latency_ms: float):
    """Format and print an execution status line."""
    cprint(f"{C.DIM}── {iters} iter · {tokens:,} tokens · {latency_ms}ms ──{C.RESET}")


def bottom_bar(
    provider: str,
    model: str,
    tokens: int = 0,
    iter_count: int = 0,
    tool_count: int = 0,
    elapsed_s: float = 0.0,
    cost_usd: float = 0.0,
):
    """Upgraded status bar with neon accents and visual hierarchy."""
    ctx_max = 200000
    pct = min(100, int(tokens / ctx_max * 100)) if tokens else 0
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)
    if pct > 80:
        bar_color = C.RED
    elif pct > 50:
        bar_color = C.YELLOW
    else:
        bar_color = C.NEON_GREEN

    h = int(elapsed_s // 3600)
    m = int((elapsed_s % 3600) // 60)
    s = int(elapsed_s % 60)
    time_str = f"{h}h {m:02d}m" if h > 0 else f"{m}m {s:02d}s"
    chain = f"{C.NEON_AMBER}⛓ {tool_count}{C.RESET}" if tool_count > 0 else f"{C.DIM}⛓ 0{C.RESET}"
    model_short = model.split(":")[0] if ":" in model else model
    cost_str = format_cost(cost_usd) if cost_usd >= 0 else ""

    # Top separator
    print(f"{C.BORDER}{'─' * 78}{C.RESET}")
    # Hints line
    cprint(f"  {C.TEXT_DIM}❯ type a message · {C.NEON_CYAN}/help{C.RESET} {C.TEXT_DIM}for commands · {C.NEON_PURPLE}/plan{C.RESET} {C.TEXT_DIM}toggle plan · {C.NEON_GREEN}/skills{C.RESET} {C.TEXT_DIM}browse · Ctrl+C cancel{C.RESET}")
    # Status line with colored sections
    status_parts = [
        f"{C.NEON_CYAN}{C.BOLD}{model_short}{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {C.TEXT_DIM}{tokens:,}/{ctx_max:,} tok{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {bar_color}[{bar}]{C.RESET} {C.TEXT_DIM}{pct}%{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {C.NEON_PURPLE}⚙ {tool_count}{C.RESET}",
        f"{C.TEXT_DIM}│{C.RESET} {chain}",
        f"{C.TEXT_DIM}│{C.RESET} {C.TEXT_DIM}⏱ {time_str}{C.RESET}",
    ]
    if cost_usd > 0:
        status_parts.append(f"{C.TEXT_DIM}│{C.RESET} {C.NEON_GREEN}{cost_str}{C.RESET}")
    cprint(f"  {' '.join(status_parts)}")
    # Bottom separator
    print(f"{C.BORDER}{'─' * 78}{C.RESET}")


# ─── Markdown Answer Renderer ────────────────────────────────────

def _print_answer(text: str):
    """Print answer with markdown-style formatting, no box."""
    if not text:
        return
    lines = text.split("\n")
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        # Code block toggle
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                cprint(f"  {C.DIM}{stripped}{C.RESET}")
            continue
        if in_code_block:
            cprint(f"  {C.DIM}{line}{C.RESET}")
            continue
        # Headers
        if stripped.startswith("### "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        elif stripped.startswith("## "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        elif stripped.startswith("# "):
            cprint(f"  {C.CYAN}{C.BOLD}{stripped}{C.RESET}")
        # Bold
        elif "**" in stripped:
            # Simple bold rendering
            clean = re.sub(r'\*\*(.+?)\*\*', rf"{C.BOLD}\1{C.RESET}", stripped)
            cprint(f"  {clean}")
        # Inline code
        elif "`" in stripped and not stripped.startswith("```"):
            clean = re.sub(r'`(.+?)`', rf"{C.CYAN}\1{C.RESET}", stripped)
            cprint(f"  {clean}")
        # List items
        elif re.match(r'^[-*]\s', stripped):
            cprint(f"  {C.GREEN}•{C.RESET} {stripped[2:]}")
        # Numbered lists
        elif re.match(r'^\d+\.\s', stripped):
            num = re.match(r'^(\d+\.)', stripped).group(1)
            cprint(f"  {C.GREEN}{num}{C.RESET} {stripped[len(num)+1:]}")
        else:
            cprint(f"  {line}")


# ─── Thinking Spinner ────────────────────────────────────────────

THINK_QUOTES = [
    "The best code is no code at all",
    "First, solve the problem. Then, write the code.",
    "Talk is cheap. Show me the code.",
    "Simplicity is the soul of efficiency.",
    "Any fool can write code that a computer can understand.",
    "Programs must be written for people to read.",
    "The only way to learn a new programming language is by writing programs.",
    "It works on my machine",
    "Have you tried turning it off and on again?",
    "There are only two hard things in CS: cache invalidation and naming things.",
    "It's not a bug, it's a feature.",
    "A good programmer looks both ways before crossing a one-way street.",
    "Deleted code is debugged code.",
    "Code is like humor. When you have to explain it, it's bad.",
    "Fix the cause, not the symptom.",
    "Optimism is an occupational hazard of programming.",
]

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class ThinkingSpinner:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._msg = ""
        self._start_time = 0.0

    def start(self, msg: str = "Thinking"):
        self._stop.clear()
        self._msg = msg
        self._start_time = time.time()
        if _RICH:
            self._live = _RichLive(
                "", console=get_rich_console(), refresh_per_second=8, transient=True
            )
            self._live.start()
            self._thread = threading.Thread(target=self._run_rich, daemon=True)
        else:
            self._thread = threading.Thread(target=self._run_fallback, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if _RICH and getattr(self, "_live", None) is not None:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
        else:
            sys.stderr.write("\r" + " " * 80 + "\r")
            sys.stderr.flush()

    def _frame_text(self) -> str:
        elapsed = time.time() - self._start_time
        pct = min(100, int(elapsed / 60 * 100))
        filled = pct // 5
        bar = "█" * filled + "░" * (20 - filled)
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        time_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
        max_quote = 40
        quote = _spinner_quote(elapsed)
        quote_display = quote[:max_quote] + "..." if len(quote) > max_quote else quote
        return f"⏳ {self._msg}... [{bar}] {pct}% {time_str}  {quote_display}"

    def _run_rich(self):
        from rich.text import Text as _Text

        while not self._stop.is_set():
            t = _Text()
            t.append(self._frame_text(), style="cyan")
            try:
                self._live.update(t)
            except Exception:
                pass
            time.sleep(0.15)

    def _run_fallback(self):
        i = 0
        last_quote = time.time()
        quote = random.choice(THINK_QUOTES)
        while not self._stop.is_set():
            now = time.time()
            elapsed = now - self._start_time
            pct = min(100, int(elapsed / 60 * 100))
            filled = pct // 5
            bar = "█" * filled + "░" * (20 - filled)
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            time_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
            if now - last_quote > 3:
                quote = random.choice(THINK_QUOTES)
                last_quote = now
            max_quote = 40
            quote_display = quote[:max_quote] + "..." if len(quote) > max_quote else quote
            text = f"\r  {C.CYAN}⏳{C.RESET} {self._msg}... {C.DIM}[{bar}] {pct}% {time_str}{C.RESET}  {C.DIM}{quote_display}{C.RESET}"
            sys.stdout.write(text)
            sys.stdout.flush()
            i += 1
            time.sleep(0.3)


_SPINNER_QUOTE_IDX = {"i": 0}


def _spinner_quote(elapsed: float) -> str:
    """Quote that rotates every ~3s without re-seeding random per frame."""
    idx = int(elapsed // 3)
    return THINK_QUOTES[idx % len(THINK_QUOTES)]


# ─── Streaming Markdown Renderer ─────────────────────────────────

class StreamingMarkdown:
    """Incremental markdown renderer for token-by-token streaming.

    rich backend: completed lines accumulate into a live-updating Markdown
    panel (true reflow, proper tables/code). Fallback: the original ANSI
    line renderer. Public API unchanged: start/feed/end.
    """

    def __init__(self, width: int = 78):
        self.width = width
        self._in_code = False
        self._buffer = ""
        self._started = False
        self._full_text = ""
        self._live = None
        self._console = get_rich_console() if _RICH else None

    def start(self):
        """Open the streaming response frame."""
        self._started = True
        if _RICH:
            from rich.markdown import Markdown as _Md

            self._live = _RichLive(
                _Md("", code_theme="monokai"),
                console=self._console,
                refresh_per_second=12,
                vertical_overflow="visible",
            )
            try:
                self._live.start()
            except Exception:
                self._live = None
            return
        border = C.BORDER
        print(f"\n{border}╭── {C.NEON_GREEN}{C.BOLD}Response{C.RESET}{border} {'─' * (self.width - 14)}╮{C.RESET}")

    def feed(self, token: str):
        """Feed a token into the renderer. Renders completed lines."""
        self._buffer += token
        if _RICH and self._live is not None:
            self._full_text += token
            try:
                from rich.markdown import Markdown as _Md

                self._live.update(_Md(self._full_text, code_theme="monokai"))
            except Exception:
                self._live = None  # degrade to line mode mid-stream
            return
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            self._render_line(line)

    def _render_line(self, line: str):
        """Render a single completed line with markdown formatting."""
        stripped = line.strip()
        border = C.BORDER
        prefix = f"{border}│{C.RESET} "

        if stripped.startswith('```'):
            self._in_code = not self._in_code
            if self._in_code:
                lang = stripped[3:].strip()
                sys.stdout.write(f"{prefix} {C.DIM}{'─' * 40} {lang}{C.RESET}\n")
            else:
                sys.stdout.write(f"{prefix} {C.DIM}{'─' * 40}{C.RESET}\n")
            return

        if self._in_code:
            sys.stdout.write(f"{prefix}  {C.DIM}{line}{C.RESET}\n")
            return

        # Headers
        if stripped.startswith('### '):
            sys.stdout.write(f"{prefix} {C.CYAN}{C.BOLD}{stripped}{C.RESET}\n")
        elif stripped.startswith('## '):
            sys.stdout.write(f"{prefix} {C.CYAN}{C.BOLD}{stripped}{C.RESET}\n")
        elif stripped.startswith('# '):
            sys.stdout.write(f"{prefix} {C.NEON_CYAN}{C.BOLD}{stripped}{C.RESET}\n")
        # Bold
        elif '**' in stripped:
            clean = re.sub(r'\*\*(.+?)\*\*', rf"{C.BOLD}\1{C.RESET}", stripped)
            sys.stdout.write(f"{prefix} {clean}\n")
        # Inline code
        elif '`' in stripped and not stripped.startswith('```'):
            clean = re.sub(r'`(.+?)`', rf"{C.CYAN}\1{C.RESET}", stripped)
            sys.stdout.write(f"{prefix} {clean}\n")
        # List items
        elif re.match(r'^[-*]\s', stripped):
            sys.stdout.write(f"{prefix} {C.GREEN}•{C.RESET} {stripped[2:]}\n")
        elif re.match(r'^\d+\.\s', stripped):
            num = re.match(r'^(\d+\.)', stripped).group(1)
            sys.stdout.write(f"{prefix} {C.GREEN}{num}{C.RESET} {stripped[len(num)+1:]}\n")
        else:
            sys.stdout.write(f"{prefix} {line}\n")
        sys.stdout.flush()

    def end(self, latency_ms: float = 0, tokens: int = 0, cost_usd: float = 0):
        """Close the streaming frame with stats."""
        if _RICH and self._live is not None:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
            stats = f"{tokens:,} tok · {latency_ms:.0f}ms"
            if cost_usd > 0:
                stats += f" · ${cost_usd:.4f}"
            print(f"  {C.DIM}{stats}{C.RESET}")
            self._buffer = ""
            return
        if self._buffer.strip():
            self._render_line(self._buffer)
            self._buffer = ""
        border = C.BORDER
        stats = f"{C.DIM}{tokens:,} tok · {latency_ms:.0f}ms"
        if cost_usd > 0:
            stats += f" · ${cost_usd:.4f}"
        stats += C.RESET
        print(f"{border}╰{'─' * (self.width - 2)}╯{C.RESET}")
        print(f"  {stats}")


# ─── Diff Renderer ───────────────────────────────────────────────

def render_diff(old_content: str, new_content: str, filename: str, width: int = 78) -> str:
    """Render a colored unified diff between old and new content."""
    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=''
    ))
    if not diff_lines:
        return f"  {C.DIM}No changes{C.RESET}"

    out = []
    border = C.BORDER
    out.append(f"{border}╭── {C.NEON_AMBER}{C.BOLD}Diff: {filename}{C.RESET}{border} {'─' * max(1, width - len(filename) - 12)}╮{C.RESET}")
    for line in diff_lines:
        line = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            out.append(f"{border}│{C.RESET} {C.BOLD}{line}{C.RESET}")
        elif line.startswith('@@'):
            out.append(f"{border}│{C.RESET} {C.CYAN}{line}{C.RESET}")
        elif line.startswith('+'):
            out.append(f"{border}│{C.RESET} {C.GREEN}{line}{C.RESET}")
        elif line.startswith('-'):
            out.append(f"{border}│{C.RESET} {C.RED}{line}{C.RESET}")
        else:
            out.append(f"{border}│{C.RESET} {C.DIM}{line}{C.RESET}")
    out.append(f"{border}╰{'─' * (width - 1)}╯{C.RESET}")
    return '\n'.join(out)


def prompt_diff_approval() -> bool:
    """Ask user to approve a diff. Returns True if approved."""
    try:
        choice = input(f"  {C.NEON_AMBER}Apply?{C.RESET} [{C.GREEN}a{C.RESET}]pply / [{C.RED}r{C.RESET}]eject: ").strip().lower()
        return choice in ('a', 'apply', 'y', 'yes', '')
    except (EOFError, KeyboardInterrupt):
        return False


# ─── Thought Card ────────────────────────────────────────────────

def thought_card(thought: str, elapsed_s: Optional[float] = None, collapsed: bool = True):
    """Render a thinking/reasoning block, collapsed by default."""
    if not thought or not thought.strip():
        return
    border = C.BORDER
    timing = f" ({elapsed_s:.1f}s)" if elapsed_s is not None else ""
    header = f"💭 Thinking{timing}"
    if collapsed:
        lines = thought.strip().splitlines()
        preview = lines[0][:60] + ('...' if len(lines[0]) > 60 or len(lines) > 1 else '')
        print(f"  {C.DIM}{header}: {preview}{C.RESET}")
    else:
        print(f"{border}╭── {C.YELLOW}{header}{C.RESET}{border} {'─' * 50}╮{C.RESET}")
        for line in thought.strip().splitlines():
            print(f"{border}│{C.RESET}  {C.ITALIC}{C.DIM}{line}{C.RESET}")
        print(f"{border}╰{'─' * 72}╯{C.RESET}")
