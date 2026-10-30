"""Keyboard-first command palette for the canonical JEBAT console.

The palette is deliberately independent from the agent runtime: it resolves a
command string, then the existing REPL dispatcher executes it. Non-interactive
terminals retain the numbered picker fallback.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaletteCommand:
    name: str
    description: str
    usage: str = ""

    @property
    def needs_argument(self) -> bool:
        return "<" in self.usage or self.usage.startswith("[")


ARGUMENTS = {
    "/advisor": "classify|verify|score <text> [options]",
    "/apikey": "<name>:<key>",
    "/brainstorm": "[mode:]<topic>",
    "/commit": "<message>",
    "/continue": "[session-id]",
    "/cost": "<model> <tokens>",
    "/delegate": "<agent>:<task>",
    "/diff": "[path]",
    "/export": "[output-path]",
    "/mem+": "<key> <value>",
    "/memory+": "<key> = <value>",
    "/mode": "<mode>",
    "/model": "[model-or-number]",
    "/ports": "[host]",
    "/provider": "[add|remove|test|provider-id]",
    "/recall": "[query]",
    "/scaffold": "<framework> [name]",
    "/scan": "[path]",
    "/search": "<query>",
    "/skill": "<name>",
    "/skin": "<skin>",
    "/swarm": "<task>",
    "/task": "<id>",
    "/tools": "[list|call <name> --args '{...}' [--yolo]]",
    "/tool": "[list|call <name> --args '{...}' [--yolo]]",
    "/validate": "<string>",
}


def fuzzy_match(query: str, text: str) -> bool:
    """Match ordered query characters, ignoring case and the leading slash."""
    query = query.lower().strip().lstrip("/")
    if not query:
        return True
    position = 0
    for char in text.lower():
        if position < len(query) and char == query[position]:
            position += 1
    return position == len(query)


def filter_commands(
    entries: Sequence[tuple[str, str]], query: str
) -> list[PaletteCommand]:
    """Return palette rows matching either a command or its description."""
    return [
        PaletteCommand(name, description, ARGUMENTS.get(name, ""))
        for name, description in entries
        if fuzzy_match(query, name) or fuzzy_match(query, description)
    ]


def interactive_palette(
    entries: Sequence[tuple[str, str]], initial: str = "/"
) -> str | None:
    """Select a command with filtering, arrows, Enter and Escape.

    Enter on a bare or partial command selects the highlighted row. Commands
    with arguments are completed in the same input rather than being executed
    prematurely. Returns the exact command line for the normal REPL dispatcher.
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style

    selected = 0
    bindings = KeyBindings()

    def rows(buffer_text: str) -> list[PaletteCommand]:
        query = buffer_text.split(maxsplit=1)[0] if buffer_text.startswith("/") else ""
        return filter_commands(entries, query)

    @bindings.add("up")
    @bindings.add("s-tab")
    def previous(event) -> None:
        nonlocal selected
        matches = rows(event.current_buffer.text)
        if matches:
            selected = (selected - 1) % len(matches)

    @bindings.add("down")
    @bindings.add("tab")
    def following(event) -> None:
        nonlocal selected
        matches = rows(event.current_buffer.text)
        if matches:
            selected = (selected + 1) % len(matches)

    @bindings.add("enter")
    def accept(event) -> None:
        nonlocal selected
        text = event.current_buffer.text.strip()
        matches = rows(event.current_buffer.text)
        if not matches:
            if " " in text:
                event.current_buffer.validate_and_handle()
            return
        exact = next((item for item in matches if item.name == text.split(maxsplit=1)[0]), None)
        chosen = exact or matches[min(selected, len(matches) - 1)]
        if exact and (" " in text or not chosen.needs_argument):
            event.current_buffer.validate_and_handle()
            return
        event.current_buffer.text = chosen.name + (" " if chosen.needs_argument else "")
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        selected = 0
        if not chosen.needs_argument:
            event.current_buffer.validate_and_handle()

    def toolbar() -> HTML:
        matches = rows(session.default_buffer.text)
        if not session.default_buffer.text.startswith("/"):
            return HTML("")
        lines = ["<b>↑↓ select · Enter choose · type filter · Esc cancel</b>"]
        if not matches:
            lines.append("<ansired>No matching command</ansired>")
        else:
            selected_row = min(selected, len(matches) - 1)
            for index, item in enumerate(matches[:12]):
                marker = "❯" if index == selected_row else " "
                style = "reverse" if index == selected_row else ""
                usage = f" {item.usage}" if item.usage else ""
                lines.append(
                    f"<style {style}>{marker} {item.name}{usage} — {item.description}</style>"
                )
        return HTML("\n".join(lines))

    style = Style.from_dict({"bottom-toolbar": "noreverse"})
    session: PromptSession = PromptSession(
        key_bindings=bindings,
        bottom_toolbar=toolbar,
        style=style,
        refresh_interval=0.1,
    )
    try:
        result = session.prompt("❯ ", default=initial).strip()
    except (EOFError, KeyboardInterrupt):
        return None
    return result or None


def choose_command(
    entries: Sequence[tuple[str, str]],
    *,
    interactive: bool = True,
    input_fn: Callable[[str], str] = input,
) -> tuple[str, str] | None:
    """Return `(command, arguments)` using the terminal-appropriate picker."""
    if interactive:
        command = interactive_palette(entries)
        if not command:
            return None
        parts = command.split(maxsplit=1)
        return parts[0], parts[1] if len(parts) > 1 else ""

    matches = filter_commands(entries, "")
    for index, item in enumerate(matches, 1):
        print(f"  {index:>2}. {item.name:<16} {item.description}")
    try:
        choice = input_fn("  Pick command (number or /name): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not choice:
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(matches):
        return matches[int(choice) - 1].name, ""
    selected = filter_commands(entries, choice)
    if choice.startswith("/") and selected:
        exact = next((item for item in selected if item.name == choice), selected[0])
        return exact.name, ""
    return None
