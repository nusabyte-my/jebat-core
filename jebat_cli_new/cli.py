"""argparse surface for the JEBAT CLI (omp-shaped).

Replaces hand-rolled sys.argv filtering with a real parser so one-shot
(`-p/--print`), machine output (`--mode json`), model roles, profiles and
tool/skill filtering are addressable as flags instead of subcommand words.

Bare `jebat`, `jebat repl`, `jebat code "<prompt>"`, `jebat chat ...` and
every existing subcommand keep working — `parse()` returns the same token
list `main()` already dispatches on in `args.tokens`, plus the new options.

Two switches deliberately use nargs="?" with const, because the legacy
surface treats bare `-c` / `-s` as "continue last session":
    -c / --continue            -> const=True,  -c <id> -> that session
    -s / --session [ID]        -> const=True,  -s <id> -> that session
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SUBCOMMANDS = (
    "repl", "code", "agent", "chat", "think", "provider", "model",
    "mcp", "config", "agentix", "learning", "workflow", "doctor",
    "status", "webui", "tool", "tools", "init",
)

MODES = ("text", "json", "rpc", "rpc-ui")

THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max", "auto")

# omp-shaped roles. `default` is the main agent model; the rest are overrides.
ROLE_NAMES = ("default", "smol", "slow", "plan", "vision", "task", "advisor")


# ── Config: roles + profiles ────────────────────────────────────────────────

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def roles_file() -> Path:
    return Path.home() / ".jebat" / "config.yaml"


def load_roles() -> Dict[str, str]:
    """Read model roles from ~/.jebat/config.yaml (key: `roles`)."""
    data = _load_yaml(roles_file())
    raw = data.get("roles") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if v}


def save_role(role: str, model: str) -> Path:
    """Persist one role into config.yaml without disturbing other keys."""
    path = roles_file()
    data = _load_yaml(path)
    roles = data.get("roles")
    if not isinstance(roles, dict):
        roles = {}
    roles[role] = model
    data["roles"] = roles
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML required to write roles") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.with_suffix(f".yaml.bak-roles").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def profile_home() -> Path:
    """Base dir for named profiles: ~/.jebat/profiles/<name>."""
    return Path.home() / ".jebat" / "profiles"


def apply_profile(name: str) -> None:
    """Point every JEBAT state path at an isolated profile dir.

    Sets HOME/USERPROFILE so modules that compute `Path.home() / ".jebat"`
    resolve inside the profile — no per-module changes needed.
    """
    root = profile_home() / name
    root.mkdir(parents=True, exist_ok=True)
    os.environ["JEBAT_PROFILE"] = name
    os.environ["USERPROFILE"] = str(root)
    os.environ["HOME"] = str(root)


def split_provider_model(spec: str) -> Tuple[Optional[str], str]:
    """`openai/gpt-5` -> ("openai", "gpt-5"); `gpt-5` -> (None, "gpt-5").

    Only splits on a slash whose left side names a provider — a registered
    config, a PROVIDER_KINDS entry, or a custom provider id. Namespaced model
    ids (openrouter's `anthropic/claude-sonnet-4`) therefore survive intact.
    """
    if "/" not in spec:
        return None, spec
    head, tail = spec.split("/", 1)
    return (head, tail) if head in known_provider_ids() else (None, spec)


def known_provider_ids() -> set:
    try:
        from jebat_cli_new.jebat import PROVIDER_KINDS, ProviderRegistry

        ids = {kind for kind, *_ in PROVIDER_KINDS}
        ids |= {name.lower().replace(" ", "-") for _, name, *_ in PROVIDER_KINDS}
        ids |= set(ProviderRegistry().configs)
        return ids
    except Exception:
        return set()


def ensure_provider(registry, provider_id: Optional[str], model: Optional[str]):
    """Register `provider_id` from PROVIDER_KINDS when it isn't configured yet.

    Lets `--provider groq` / `--model groq/llama-3.3-70b` work out of the box
    instead of failing with "no provider configured". Returns (provider, model).
    """
    if not provider_id:
        return provider_id, model
    if provider_id in registry.configs:
        return provider_id, model
    try:
        from jebat_cli_new.jebat import PROVIDER_KINDS, ProviderConfig
    except Exception:
        return provider_id, model
    for kind, name, api_base, default_model, _needs_key, _desc in PROVIDER_KINDS:
        if kind == provider_id or name.lower().replace(" ", "-") == provider_id.lower():
            registry.configs[kind] = ProviderConfig(
                id=kind, name=name, api_base=api_base,
                model=model or default_model, kind=kind,
            )
            return kind, model or default_model
    return provider_id, model


def resolve_role(role: Optional[str], cli_model: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """CLI --model wins; otherwise fall back to the persisted role."""
    if cli_model:
        return split_provider_model(cli_model)
    if role:
        spec = load_roles().get(role)
        if spec:
            return split_provider_model(spec)
    return None, None


# ── Filtering ───────────────────────────────────────────────────────────────

def filter_tools(names: Optional[Sequence[str]]) -> None:
    """Restrict the tool registry in place (omp's --tools / --no-tools)."""
    if names is None:
        return
    wanted = {n.strip() for n in names if n.strip()}
    from jebat_cli_new import tools as tools_mod

    def keep(definition: Dict[str, Any]) -> bool:
        return definition.get("name") in wanted

    tools_mod.TOOL_DEFINITIONS[:] = [d for d in tools_mod.TOOL_DEFINITIONS if keep(d)]
    for name in list(getattr(tools_mod, "HANDLERS", {})):
        if name not in wanted:
            tools_mod.HANDLERS.pop(name, None)


def filter_skills(patterns: Optional[Sequence[str]], disabled: bool) -> List[str]:
    """Return skill names to keep. Empty list means 'no filtering'."""
    if disabled:
        return []
    if not patterns:
        return []
    import fnmatch

    try:
        from jebat_cli_new.jebat import SkillManager

        available = [name for name, _ in SkillManager().list_skills()]
    except Exception:
        return []
    keep: List[str] = []
    for pattern in patterns:
        keep.extend(fnmatch.filter(available, pattern.strip()))
    return sorted(set(keep))


# ── Parser ──────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    from jebat_cli_new import __version__ as _cli_version

    p = argparse.ArgumentParser(
        prog="jebat",
        description="JEBAT — unified coding agent. One tool, all providers.",
        epilog=f"JEBAT v{_cli_version}",
        add_help=True,
    )
    p.add_argument("command", nargs="?", default=None,
                   help=f"Subcommand ({', '.join(SUBCOMMANDS)}) — omit for REPL")
    p.add_argument("prompt", nargs="*", help="Prompt words (bare prompt starts a REPL session)")

    p.add_argument("-p", "--print", dest="print_mode", action="store_true",
                   help="Non-interactive: run the prompt and exit")
    p.add_argument("--mode", choices=MODES, default="text",
                   help="Output mode (default: text)")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress banner, spinner and setup panels")

    p.add_argument("--provider", help="Override provider for this run")
    p.add_argument("--model", help="Override model for this run")
    for role in ROLE_NAMES:
        if role == "default":
            continue
        flag = "--plan-model" if role == "plan" else f"--{role}"
        p.add_argument(flag, dest=f"role_{role}",
                       help=f"Model for the '{role}' role")

    p.add_argument("--role", choices=ROLE_NAMES,
                   help="Use a named role's model for this run (see `roles` in config.yaml)")
    p.add_argument("--profile", help="Isolated profile for auth, sessions and caches")
    p.add_argument("--cwd", help="Working directory to start in")

    p.add_argument("-c", "--continue", dest="continue_last", nargs="?", const=True,
                   default=False, help="Continue the previous session")
    p.add_argument("-s", "--session", nargs="?", const=True, default=None,
                   help="Resume a session by id (picker when omitted)")

    p.add_argument("--thinking", choices=THINKING_LEVELS, help="Thinking level")
    p.add_argument("--no-tools", dest="no_tools", action="store_true",
                   help="Disable all built-in tools")
    p.add_argument("--tools", help="Comma-separated tool allowlist")
    p.add_argument("--skills", dest="skill_patterns",
                   help="Comma-separated skill globs (e.g. 'git-*,docker')")
    p.add_argument("--no-skills", dest="no_skills", action="store_true",
                   help="Disable skill discovery")
    p.add_argument("--no-session", dest="no_session", action="store_true",
                   help="Don't persist this session")

    p.add_argument("--yolo", action="store_true", help="Auto-approve tool calls")
    p.add_argument("--plan", action="store_true", help="Plan before executing")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    p.add_argument("--ghost", action="store_true", help="Silent execution")
    p.add_argument("--auto-commit", "-a", dest="auto_commit", action="store_true",
                   help="Git commit after file changes")

    p.add_argument("--banner", choices=("auto", "art", "plain", "none"),
                   default="auto",
                   help="Banner style: auto (by terminal), art, plain, or none")
    p.add_argument("--export", metavar="PATH",
                   help="Write the run as a markdown transcript to PATH and exit")
    p.add_argument("-e", "--extension", action="append", default=[],
                   help="Load an extension file or dir (repeatable)")
    p.add_argument("--no-extensions", dest="no_extensions", action="store_true",
                   help="Disable extension discovery")
    p.add_argument("--hook", action="append", default=[],
                   help="Load a hook/extension file (repeatable)")
    p.add_argument("--version", action="store_true", help="Print version and exit")
    p.add_argument("--set-role", metavar="ROLE=MODEL",
                   help="Persist a model role to config.yaml and exit")
    return p


def _reorder(tokens: Sequence[str]) -> List[str]:
    """Move a leading subcommand to the front when flags precede it.

    `jebat --yolo code "x"` -> `jebat code --yolo "x"` so argparse binds the
    subcommand instead of swallowing it as a prompt word.
    """
    out = list(tokens)
    for idx, token in enumerate(out):
        if token in SUBCOMMANDS:
            return [token] + out[:idx] + out[idx + 1:]
        if not token.startswith("-"):
            break
    return out


def parse(tokens: Sequence[str]) -> Tuple[Optional[argparse.Namespace], List[str]]:
    """Parse argv. Returns (namespace, residual tokens for `main`).

    residual is empty when the new surface fully handled the invocation.
    """
    parser = build_parser()
    reordered = _reorder(tokens)
    subcommand = reordered[0] if reordered and reordered[0] in SUBCOMMANDS else None
    if subcommand is not None:
        # A subcommand invocation owns everything after the word, including its
        # own flags (`mcp serve --transport stdio`, `agentix auto --name X`).
        # Leading flags the reorder scan stepped over stay global.
        body = reordered[1:]
        global_flags = 0
        while global_flags < len(body) and body[global_flags].startswith("-"):
            if body[global_flags] in ("-h", "--help"):
                break  # help belongs to the subcommand, not the global parser
            global_flags += 1
        ns = parser.parse_args([subcommand] + body[:global_flags])
        ns.extra_tokens = list(body[global_flags:])
    else:
        ns = parser.parse_args(reordered)
        ns.extra_tokens = []
    ns.handled = False

    # `command` is nargs="?" so a bare prompt lands there. Anything that is not
    # a real subcommand belongs to the prompt.
    if ns.command is not None and ns.command not in SUBCOMMANDS:
        ns.prompt = [ns.command] + list(ns.prompt or [])
        ns.command = None

    if ns.version:
        from jebat_cli_new import __version__

        print(f"jebat {__version__}")
        ns.handled = True
        return ns, []

    if ns.set_role:
        if "=" not in ns.set_role:
            parser.error("--set-role expects ROLE=MODEL")
        role, model = ns.set_role.split("=", 1)
        if role not in ROLE_NAMES:
            parser.error(f"unknown role '{role}' (choose from {', '.join(ROLE_NAMES)})")
        path = save_role(role, model)
        print(f"  role {role} = {model}  ({path})")
        ns.handled = True
        return ns, []

    # `-p` with no prompt words reads the prompt from stdin (omp's rule).
    # Bare `jebat` always starts the REPL, even with a pipe attached.
    if ns.print_mode and not ns.prompt and ns.command is None and not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            ns.prompt = [piped]

    if ns.profile:
        apply_profile(ns.profile)

    if ns.cwd:
        try:
            os.chdir(ns.cwd)
        except OSError as exc:
            parser.error(f"--cwd: {exc}")

    if ns.no_tools:
        filter_tools([])
    elif ns.tools:
        filter_tools(ns.tools.split(","))
    if not ns.no_extensions:
        from jebat_cli_new import extensions as _ext

        _ext.set_tool_allowlist([] if ns.no_tools else
                                (ns.tools.split(",") if ns.tools else None))

    ns.keep_skills = filter_skills(
        ns.skill_patterns.split(",") if ns.skill_patterns else None, ns.no_skills
    )

    # Extensions/hooks: load before anything can dispatch a slash command.
    ns.extension_summary = ""
    if not ns.no_extensions:
        from jebat_cli_new import extensions as ext

        ext.discover(list(ns.extension) + list(ns.hook))
        ns.extension_summary = ext.summary()

    provider, model = resolve_role(ns.role, ns.model)
    if ns.provider:
        provider = ns.provider
    ns.provider, ns.model = provider, model

    # Role overrides (--smol/--slow/--plan-model/--vision/--task/--advisor).
    ns.role_models = {}
    for role in ROLE_NAMES:
        if role == "default":
            continue
        value = getattr(ns, f"role_{role}", None)
        if value:
            ns.role_models[role] = value
    ns.quiet = bool(ns.quiet or ns.mode in ("json", "rpc", "rpc-ui"))
    if ns.quiet:
        # Keep stdout machine-clean: no ANSI, no spinner, no banner.
        from jebat_cli_new.theme import C

        for attr in [a for a in vars(C) if not a.startswith("_")]:
            if isinstance(getattr(C, attr), str):
                setattr(C, attr, "")

    return ns, _residual(ns)


def _residual(ns: argparse.Namespace) -> List[str]:
    """Rebuild the legacy token list for the subcommands `main` owns."""
    extras = list(getattr(ns, "extra_tokens", []) or [])
    cmd = ns.command
    rest = list(ns.prompt or [])
    if cmd is None:
        return []
    if cmd == "think":
        cmd = "chat"
    if cmd in ("provider", "model", "mcp", "config", "agentix", "learning",
               "workflow", "tool", "tools", "init", "doctor", "status", "webui"):
        return [cmd] + rest + extras
    if cmd in ("repl",):
        return []
    if cmd in ("code", "agent", "chat"):
        out = [cmd]
        if ns.yolo:
            out.append("--yolo")
        if ns.auto_commit:
            out.append("--auto-commit")
        if ns.plan:
            out.append("--plan")
        if ns.provider:
            out += ["--provider", ns.provider]
        if ns.model:
            out += ["--model", ns.model]
        return out + rest + extras
    return [cmd] + rest + extras


def one_shot_requested(ns: argparse.Namespace) -> bool:
    """True when this invocation should run once and exit (no REPL drop-in)."""
    if ns.print_mode or ns.mode == "json":
        return True
    return not sys.stdin.isatty()


def write_export(path: str, prompt: str, response: str,
                 provider: str = "", model: str = "", tools=None) -> "Path":
    """Write a one-shot run as a markdown transcript. Returns the written path."""
    from datetime import datetime
    from pathlib import Path as _Path

    out = _Path(path).expanduser()
    if out.is_dir():
        out = out / f"jebat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# JEBAT Run Export", "",
        f"- when: {stamp}",
        f"- provider: {provider or '-'}",
        f"- model: {model or '-'}",
    ]
    if tools:
        lines.append(f"- tools: {', '.join(tools)}")
    lines += ["", "## Prompt", "", prompt, "", "## JEBAT", "", response, ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def emit_json(payload: Dict[str, Any]) -> None:
    import json

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
