#!/usr/bin/env python3
"""
JEBAT — unified coding-agent CLI.
One tool. All providers. Native tools. Plan + execute.
"""

from __future__ import annotations

import argparse, json, os, sys, textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


# ═══════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ProviderConfig:
    id: str
    name: str
    api_base: str
    model: str
    api_key: Optional[str] = None
    kind: str = "ollama"

@dataclass
class CompletionRequest:
    provider: str
    model: str
    prompt: str
    temperature: float = 0.2
    max_tokens: int = 4096

@dataclass
class CompletionResponse:
    text: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    latency_ms: int = 0

@dataclass
class AgentMessage:
    role: str
    content: str
    tool_calls: Optional[str] = None

@dataclass
class AgentStep:
    prompt: str
    response: CompletionResponse
    tool_actions: List[str] = field(default_factory=list)
    plan: Optional[str] = None
    observation: Optional[str] = None
    steps: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# PROVIDER REGISTRY
# ═══════════════════════════════════════════════════════════════════

_PROVIDER_FILE = os.path.expanduser("~/.jebat/jebat-cli-providers.json")


class ProviderRegistry:
    def __init__(self):
        self.configs: Dict[str, ProviderConfig] = {}
        self.providers: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(_PROVIDER_FILE):
            try:
                with open(_PROVIDER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, cfg in data.items():
                    c = ProviderConfig(**cfg)
                    self.configs[key] = c
                    self.providers[key] = _provider_factory(c)
            except Exception:
                pass

    def _save(self):
        os.makedirs(os.path.dirname(_PROVIDER_FILE), exist_ok=True)
        data = {}
        for key, cfg in self.configs.items():
            data[key] = {
                "id": cfg.id, "name": cfg.name, "api_base": cfg.api_base,
                "model": cfg.model, "api_key": cfg.api_key, "kind": cfg.kind,
            }
        with open(_PROVIDER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register(self, key: str, impl, cfg: Optional[ProviderConfig] = None):
        if cfg:
            self.configs[key] = cfg
        self.providers[key] = impl
        self._save()

    def get(self, key: str):
        return self.providers.get(key)


def _provider_factory(cfg: ProviderConfig):
    kind = cfg.kind.lower()
    if kind == "ollama":
        return OllamaProvider(cfg)
    elif kind == "openai":
        return OpenAIProvider(cfg)
    elif kind == "anthropic":
        return AnthropicProvider(cfg)
    elif kind == "gemini":
        return GeminiProvider(cfg)
    elif kind == "github":
        return GitHubProvider(cfg)
    return None


# ═══════════════════════════════════════════════════════════════════
# PROVIDERS (stdlib urllib, zero deps)
# ═══════════════════════════════════════════════════════════════════

import urllib.request, urllib.error


class OllamaProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self.base = cfg.api_base.rstrip("/")

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        import time
        t0 = time.time()
        url = f"{self.base}/api/chat"
        body = json.dumps({
            "model": req.model,
            "messages": [{"role": "user", "content": req.prompt}],
            "stream": False,
            "options": {"temperature": req.temperature, "num_predict": req.max_tokens},
        }).encode()
        r = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=120) as resp:
            data = json.loads(resp.read())
        latency = int((time.time() - t0) * 1000)
        text = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count", 0)
        return CompletionResponse(text=text, model=req.model, provider=req.provider,
                                  tokens_used=tokens, latency_ms=latency)


class OpenAIProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        import time
        t0 = time.time()
        url = f"{self.cfg.api_base}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"
        body = json.dumps({
            "model": req.model,
            "messages": [{"role": "user", "content": req.prompt}],
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }).encode()
        r = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(r, timeout=120) as resp:
            data = json.loads(resp.read())
        latency = int((time.time() - t0) * 1000)
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return CompletionResponse(text=text, model=req.model, provider=req.provider,
                                  tokens_used=tokens, latency_ms=latency)


class AnthropicProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        import time
        t0 = time.time()
        url = f"{self.cfg.api_base}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.cfg.api_key or "",
        }
        body = json.dumps({
            "model": req.model,
            "max_tokens": req.max_tokens,
            "messages": [{"role": "user", "content": req.prompt}],
        }).encode()
        r = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(r, timeout=120) as resp:
            data = json.loads(resp.read())
        latency = int((time.time() - t0) * 1000)
        text = data["content"][0]["text"]
        tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
        return CompletionResponse(text=text, model=req.model, provider=req.provider,
                                  tokens_used=tokens, latency_ms=latency)


class GeminiProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        # Gemini uses OpenAI-compatible endpoint
        provider = OpenAIProvider(ProviderConfig(
            id=self.cfg.id, name=self.cfg.name,
            api_base=self.cfg.api_base + f"/v1beta/openai?key={self.cfg.api_key}",
            model=self.cfg.model, api_key=self.cfg.api_key, kind="openai"))
        return provider.complete(req)


class GitHubProvider:
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        provider = OpenAIProvider(ProviderConfig(
            id=self.cfg.id, name=self.cfg.name,
            api_base=self.cfg.api_base, model=self.cfg.model,
            api_key=self.cfg.api_key, kind="openai"))
        return provider.complete(req)


# ═══════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════

DANGEROUS_CMDS = ["rm -rf", "rm -r /", "del /s", "format", "mkfs", "> /dev/"]
DANGEROUS_FILES = ["/etc/passwd", "/etc/shadow", "~/.ssh/"]


def is_dangerous(cmd: str) -> bool:
    return any(d in cmd.lower() for d in DANGEROUS_CMDS)


def is_dangerous_file(path: str) -> bool:
    return any(d in path.lower() for d in DANGEROUS_FILES)


def execute_tool(name: str, args: Dict[str, Any], yolo: bool = False) -> str:
    try:
        if name == "read_file":
            path = args.get("path", "")
            offset = max(1, args.get("offset", 1))
            limit = args.get("limit", 200)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            out = []
            for i, line in enumerate(lines[offset-1:offset+limit-1], start=offset):
                out.append(f"{i:6d} | {line.rstrip()}")
            return "\n".join(out)

        elif name == "write_file":
            path = args.get("path") or args.get("filename") or ""
            content = args.get("content", "")
            if not yolo and is_dangerous_file(path):
                return f"BLOCKED: dangerous file {path}"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written {len(content)} bytes to {path}"

        elif name == "terminal":
            cmd = args.get("command", "")
            timeout = args.get("timeout", 120)
            workdir = args.get("workdir", None)
            if not yolo and is_dangerous(cmd):
                return f"BLOCKED: dangerous command"
            import subprocess
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=workdir, encoding="utf-8", errors="replace",
            )
            output = result.stdout + result.stderr
            if len(output) > 2000:
                output = output[:2000] + "... (truncated)"
            return output or "(no output)"

        elif name == "search_files":
            pattern = args.get("pattern", "")
            path = args.get("path", ".")
            limit = args.get("limit", 50)
            import fnmatch
            matches = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(f.lower(), pattern.lower()):
                        matches.append(os.path.join(root, f))
                        if len(matches) >= limit:
                            return "\n".join(matches)
            return "\n".join(matches) if matches else "No matches"

        elif name == "list_dir":
            path = args.get("path", ".")
            pattern = args.get("pattern", "*")
            import fnmatch
            entries = []
            try:
                for entry in sorted(os.listdir(path)):
                    if fnmatch.fnmatch(entry, pattern):
                        full = os.path.join(path, entry)
                        size = os.path.getsize(full) if os.path.isfile(full) else 0
                        kind = "file" if os.path.isfile(full) else "dir"
                        entries.append(f"{kind:4s} {size:8d} {entry}")
            except Exception as e:
                return f"Error: {e}"
            return "\n".join(entries) if entries else "(empty)"

        return f"Unknown tool: {name}"

    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════
# GIT AUTO-COMMIT
# ═══════════════════════════════════════════════════════════════════

def git_auto_commit(message: str, path: str = ".") -> tuple[bool, str]:
    import subprocess
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=path)
        if not r.stdout.strip():
            return False, "No changes"
        subprocess.run(["git", "add", "-A"], capture_output=True, cwd=path)
        r = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, cwd=path)
        return True, r.stdout.strip().split("\n")[0] if r.stdout else "Committed"
    except Exception as e:
        return False, str(e)


def git_has_changes(path: str = ".") -> bool:
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=path)
    return bool(r.stdout.strip())


# ═══════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = textwrap.dedent("""
You are JEBAT, a unified coding agent. Be direct and precise.

## Tools
- read_file(path, offset=1, limit=200)
- write_file(path, content)
- search_files(pattern, path=".", target="files", limit=50)
- terminal(command, timeout=120, workdir=None)
- list_dir(path=".", pattern="*")

## Tool Format
```json
{"tool": "tool_name", "args": {"param": "value"}}
```

## Rules
1. Use tools when needed. Don't ask permission.
2. After tool calls, you get TOOL_RESULT.
3. When done, output: FINAL_ANSWER: <answer>
4. Be concise. No filler.
""").strip()


def _parse_tool_calls(text: str) -> List[dict]:
    calls = []
    in_block = False
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```json"):
            in_block = True
            lines = []
            continue
        if s == "```" and in_block:
            in_block = False
            try:
                obj = json.loads("\n".join(lines))
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
            lines = []
            continue
        if in_block:
            lines.append(line)
            continue
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
    return calls


def _extract_steps(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines()
            if l.strip() and l.strip()[0].isdigit() and "." in l.strip()[:4]]


class Agent:
    def __init__(self, registry: ProviderRegistry, provider: str = "ollama",
                 model: str = "qwen2.5-coder:7b", yolo: bool = False,
                 auto_commit: bool = False):
        self.registry = registry
        self.provider = provider
        self.model = model
        self.messages: List[AgentMessage] = []
        self.yolo = yolo
        self.auto_commit = auto_commit
        self.max_iterations = 8

    def _history(self, limit: int = 8) -> str:
        return "\n".join(f"{m.role.upper()}: {m.content}" for m in self.messages[-limit:])

    def _call(self, prompt: str, temp: float = 0.2, max_tokens: int = 4096) -> CompletionResponse:
        impl = self.registry.get(self.provider)
        if impl:
            try:
                return impl.complete(CompletionRequest(
                    provider=self.provider, model=self.model,
                    prompt=prompt, temperature=temp, max_tokens=max_tokens))
            except Exception as e:
                return CompletionResponse(text=f"[error: {e}]", model=self.model, provider=self.provider)
        return CompletionResponse(text="[no provider]", model=self.model, provider=self.provider)

    def step(self, prompt: str, plan: bool = False) -> AgentStep:
        if plan:
            history = "\n".join([SYSTEM_PROMPT, self._history(),
                                f"TASK: {prompt}", "Begin with numbered steps."])
        else:
            history = "\n".join([SYSTEM_PROMPT, self._history(), f"USER: {prompt}"])

        resp = self._call(history, temp=0.2 if not plan else 0.4)
        text = resp.text

        # Parse and execute tool calls
        tool_calls = _parse_tool_calls(text)
        tool_actions = []
        tool_results = []
        for tc in tool_calls:
            name = tc.get("tool", "")
            args = tc.get("args", {})
            tool_actions.append(f"{name}({json.dumps(args, ensure_ascii=False)[:120]})")
            result = execute_tool(name, args, yolo=self.yolo)
            tool_results.append(f"TOOL_RESULT[{name}]: {result[:500]}")

        # Feed results back
        final_answer = None
        if tool_calls:
            obs = "\n".join(tool_results)
            follow_up = f"""{SYSTEM_PROMPT}

Previous conversation:
{self._history()}

User request: {prompt}

Your tool call:
{text}

Tool result:
{obs}

Now provide your final answer as: FINAL_ANSWER: <answer>"""
            resp2 = self._call(follow_up)
            text = resp2.text

        if "FINAL_ANSWER:" in text:
            final_answer = text.split("FINAL_ANSWER:", 1)[1].strip()

        self.messages.append(AgentMessage(role="user", content=prompt))
        self.messages.append(AgentMessage(role="assistant", content=text,
                                         tool_calls=json.dumps(tool_actions) if tool_actions else None))

        return AgentStep(
            prompt=prompt,
            response=CompletionResponse(text=text or final_answer or "",
                                       model=self.model, provider=self.provider,
                                       tokens_used=resp.tokens_used, latency_ms=resp.latency_ms),
            tool_actions=tool_actions,
            plan=text if plan else None,
            observation=final_answer,
            steps=_extract_steps(text) if plan else [],
        )

    def plan_and_execute(self, prompt: str) -> AgentStep:
        """Two-phase: plan first, then execute."""
        print("  ⟳ Planning...")
        plan_step = self.step(prompt, plan=True)
        print("  ✓ Plan ready\n")
        print(plan_step.plan or "No plan")
        print()
        return self.step(f"Follow this plan:\n{plan_step.plan}\n\nTASK: {prompt}")

    def chat(self, prompt: str) -> str:
        """Simple chat, no tools."""
        out = self.step(prompt)
        return out.response.text


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def _default_api_base(kind: str) -> str:
    return {"ollama": "http://127.0.0.1:11434", "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
            "github": "https://models.github.ai/inference"}.get(kind, "")

def _default_model(kind: str) -> str:
    return {"ollama": "qwen2.5-coder:7b", "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-20250514", "gemini": "gemini-2.5-pro",
            "github": "openai/gpt-4o-mini"}.get(kind, "")


def cmd_code(args, registry: ProviderRegistry):
    provider = args.provider or "ollama"
    model = args.model or "qwen2.5-coder:7b"

    print()
    print("  JEBAT  ⚔️  unified coding agent")
    print(f"  provider: {provider}  model: {model}")
    print()

    agent = Agent(registry, provider=provider, model=model,
                  yolo=getattr(args, "yolo", False),
                  auto_commit=getattr(args, "auto_commit", False))

    # One-shot mode
    if args.prompt:
        if getattr(args, "plan", False):
            out = agent.plan_and_execute(args.prompt)
        else:
            out = agent.step(args.prompt)
        print(f"\n  {out.response.text}\n")

        # Auto-commit
        if getattr(args, "auto_commit", False) and out.tool_actions and git_has_changes():
            ok, msg = git_auto_commit(f"JEBAT: {args.prompt[:80]}")
            if ok:
                print(f"  ℹ {msg}")
        return

    # Interactive mode
    print("  /help, /plan, /provider, /model, /clear, /exit")
    print()
    while True:
        try:
            prompt = input(f"  [{provider}:{model}] ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not prompt:
            continue
        if prompt.lower() in {"/exit", "/quit", "/q"}:
            print("  Exiting.")
            break
        if prompt.lower() in {"/clear", "/reset"}:
            agent.messages.clear()
            print("  Session cleared.")
            continue
        if prompt.lower() == "/help":
            print("  Commands:")
            print("    /help         Show this help")
            print("    /plan         Plan-then-execute mode")
            print("    /provider X   Switch provider")
            print("    /model X      Switch model")
            print("    /clear        Clear conversation")
            print("    /exit         Exit session")
            continue
        if prompt.lower() == "/plan":
            task = input("  Task: ").strip()
            if task:
                out = agent.plan_and_execute(task)
                print(f"\n  {out.response.text}\n")
            continue
        if prompt.lower().startswith("/provider "):
            provider = prompt.split(None, 1)[1].strip()
            agent.provider = provider
            print(f"  provider: {provider}")
            continue
        if prompt.lower().startswith("/model "):
            model = prompt.split(None, 1)[1].strip()
            agent.model = model
            print(f"  model: {model}")
            continue

        out = agent.step(prompt)
        print(f"\n  {out.response.text}\n")


def cmd_chat(args, registry: ProviderRegistry):
    """Chat mode — no tools, just conversation."""
    provider = args.provider or "ollama"
    model = args.model or "qwen2.5-coder:7b"

    print()
    print("  JEBAT  ⚔️  chat mode")
    print(f"  provider: {provider}  model: {model}")
    print()

    agent = Agent(registry, provider=provider, model=model)

    if args.prompt:
        print(f"\n  {agent.chat(args.prompt)}\n")
        return

    print("  Type your message. /exit to quit.")
    print()
    while True:
        try:
            prompt = input(f"  [{provider}:{model}] ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not prompt:
            continue
        if prompt.lower() in {"/exit", "/quit", "/q"}:
            break
        print(f"\n  {agent.chat(prompt)}\n")


def cmd_provider(args, registry: ProviderRegistry):
    if args.action == "list":
        if not registry.configs:
            print("  No providers. Add: jebat provider add <kind> --id <id>")
        else:
            print("  Providers:")
            for key, cfg in registry.configs.items():
                print(f"    {key} ({cfg.kind}, model={cfg.model})")
        return

    if args.action == "use":
        target = args.provider
        if target not in registry.configs:
            print(f"  Unknown: {target}")
            print(f"  Available: {', '.join(registry.configs.keys())}")
            sys.exit(1)
        cfg = registry.configs[target]
        print(f"  Using: {target} ({cfg.model})")
        return

    if args.action == "add":
        kind = (args.provider or "").strip().lower()
        if kind not in {"ollama", "openai", "anthropic", "gemini", "github"}:
            print("  Kinds: ollama|openai|anthropic|gemini|github")
            return
        pid = getattr(args, "provider_id", None) or kind
        config = ProviderConfig(
            id=pid, name=kind.capitalize(),
            api_base=getattr(args, "api_base", None) or _default_api_base(kind),
            model=getattr(args, "model", None) or _default_model(kind),
            api_key=getattr(args, "api_key", None), kind=kind)
        impl = _provider_factory(config)
        registry.register(pid, impl, cfg=config)
        print(f"  Added: {pid} ({kind})")
        return

    print("  Usage: jebat provider list|use|add")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="jebat", description="JEBAT — unified coding-agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  jebat code \"Fix the bug in auth.py\"\n"
               "  jebat code --yolo --auto-commit \"Refactor login\"\n"
               "  jebat chat \"What is Python?\"\n"
               "  jebat provider add openai --id work --api-key sk-...\n"
               "  jebat repl\n")

    sub = parser.add_subparsers(dest="command")

    code = sub.add_parser("code", help="Coding agent with tools")
    code.add_argument("prompt", nargs="?")
    code.add_argument("--provider", default="ollama")
    code.add_argument("--model", default="qwen2.5-coder:7b")
    code.add_argument("--yolo", action="store_true")
    code.add_argument("--auto-commit", "-a", action="store_true")
    code.add_argument("--plan", action="store_true")
    code.add_argument("--project-path", dest="project_path")

    chat = sub.add_parser("chat", help="Chat (no tools)")
    chat.add_argument("prompt", nargs="?")
    chat.add_argument("--provider", default="ollama")
    chat.add_argument("--model", default="qwen2.5-coder:7b")

    prov = sub.add_parser("provider", help="Provider management")
    prov_sub = prov.add_subparsers(dest="action")
    prov_sub.add_parser("list")
    use_p = prov_sub.add_parser("use")
    use_p.add_argument("provider")
    add_p = prov_sub.add_parser("add")
    add_p.add_argument("provider", help="Kind: ollama|openai|anthropic|gemini|github")
    add_p.add_argument("--id", dest="provider_id")
    add_p.add_argument("--api-base", dest="api_base")
    add_p.add_argument("--model")
    add_p.add_argument("--api-key", dest="api_key")

    repl = sub.add_parser("repl", help="Interactive REPL")
    repl.add_argument("--provider", default="ollama")
    repl.add_argument("--model", default="qwen2.5-coder:7b")

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    registry = ProviderRegistry()

    if args.command == "code":
        cmd_code(args, registry)
    elif args.command == "chat":
        cmd_chat(args, registry)
    elif args.command == "provider":
        cmd_provider(args, registry)
    elif args.command == "repl":
        # repl is just code without a prompt
        args.prompt = None
        cmd_code(args, registry)
    else:
        # Default: interactive mode
        args.prompt = None
        args.provider = "ollama"
        args.model = "qwen2.5-coder:7b"
        args.yolo = False
        args.auto_commit = False
        args.plan = False
        args.project_path = None
        cmd_code(args, registry)


if __name__ == "__main__":
    main()
