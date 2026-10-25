"""
JEBAT — agent loop / runtime with OpenManus-style multi-step planning
and OpenClaude-style UX for coding tasks.
"""

from __future__ import annotations

import json, re, textwrap, time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from jebat_cli_new.models import ProviderConfig, CompletionRequest, CompletionResponse
from jebat_cli_new.providers import ProviderRegistry
from jebat_cli_new.tools import TOOL_DEFINITIONS, execute_tool
from jebat_cli_new.ux import TerminalUX
from jebat.llm.token_usage import budget_input, usage_from_texts


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


# OpenManus + Hermes hybrid system prompt
SYSTEM_PROMPT = textwrap.dedent("""
You are JEBAT, an advanced autonomous coding agent powered by OpenManus, Hermes, and Atomic Agent doctrines.

Methodology:
1. ANALYZE & SCRATCHPAD: Use <thought> tags to reason deliberately before acting.
2. PLAN: Break problems down into atomic verifiable steps.
3. EXECUTE: Use tools iteratively. You can execute multiple tool calls in succession.
4. VERIFY: Inspect tool outputs before claiming success.
5. REPORT: Deliver a concise, grounded final answer.

Available Tools:
- read_file(path, offset=1, limit=200) — Read lines from a file
- write_file(path, content) — Create or overwrite a file
- search_files(pattern, path=".", target="files", file_glob="", limit=50) — Search files or content
- terminal(command, timeout=120, workdir=None) — Execute shell command
- list_dir(path=".", pattern="*") — List directory entries

To call a tool, use Hermes format:
<thought>
Explain your reasoning and next planned action.
</thought>
<tool_call>
{"tool": "tool_name", "args": {"param": "value"}}
</tool_call>

Or standard JSON block:
```json
{"tool": "tool_name", "args": {"param": "value"}}
```

After each step, you receive tool outputs wrapped in <tool_response>.
Use the observations to inform subsequent steps until the goal is fully accomplished.

When finished, output: FINAL_ANSWER: <your complete answer>
""").strip()

# Minimal prompt for fast local runs
MINIMAL_PROMPT = textwrap.dedent("""
You are JEBAT, a direct and sovereign coding agent.

Tools: read_file, write_file, search_files, terminal, list_dir

Tool call format:
<thought>reasoning</thought>
<tool_call>
{"tool": "tool_name", "args": {"param": "value"}}
</tool_call>

After tools execute, you receive <tool_response>. Continue iterating until done.
End with: FINAL_ANSWER: <answer>
""").strip()


def _truncate_observation(text: str, max_chars: int = 4000) -> str:
    """Fold large tool observations using head + tail retention."""
    if not text or len(text) <= max_chars:
        return text or ""
    half = max_chars // 2
    omitted = len(text) - max_chars
    return (
        f"{text[:half]}\n\n"
        f"[... {omitted:,} characters omitted for context budget ...]\n\n"
        f"{text[-half:]}"
    )


def _normalize_tool_call(obj: Any) -> Optional[Dict[str, Any]]:
    """Normalize tool call dictionary to standard {tool, args} schema."""
    if not isinstance(obj, dict):
        return None
    
    tool_name = obj.get("tool") or obj.get("name")
    if not tool_name or not isinstance(tool_name, str):
        return None
        
    args = obj.get("args") if "args" in obj else obj.get("arguments", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"raw": args}
    elif not isinstance(args, dict):
        args = {}
        
    return {"tool": tool_name.strip(), "args": args}


def _unquote(value: str) -> str:
    """Strip surrounding quotes, a trailing `}`, and trailing emoji/decorations.

    A mangled value can arrive as `"pwd && ls -la"}🏁` — quoted, with a
    leftover closing brace and a trailing emoji. Take the quoted span when
    there is one, then drop a trailing brace.
    """
    v = value.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] != '"':
        # Quoted span that runs into trailing junk: close it at the last
        # quote inside the string.
        end = v.rfind('"')
        if end > 0:
            v = v[1:end]
    elif len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    v = v.rstrip()
    if v.endswith("}"):
        v = v[:-1].rstrip()
    return v


def _strip_trailing_brace(value: str) -> str:
    v = value.rstrip()
    if v.endswith("}"):
        v = v[:-1].rstrip()
    return v


def _coerce_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    start = text.find("{")
    if start < 0:
        return None
    candidate = text[start:]
    # json.loads rejects trailing data, and a model may leave a stray
    # `</arg_value>` (or any other text) after the closing brace. Take the
    # BALANCED object only.
    depth = 0
    end = -1
    in_str = False
    escape = False
    for i, ch in enumerate(candidate):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end > 0:
        candidate = candidate[:end]
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        import ast
        parsed = ast.literal_eval(candidate)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, SyntaxError):
        pass
    return _repair_json_quotes(candidate)


def _repair_json_quotes(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON whose string values contain UNESCAPED inner quotes.

    A model asked to emit a shell command inside a JSON argument often
    writes the inner quotes raw:

        {"tool": "terminal", "args": {"command": "grep -n "ValidationPipe" file"}}

    which is invalid JSON. Recover it by re-quoting the inner quotes: walk
    the string, and inside a value, escape any quote that is not the value's
    own terminator (the one followed by a structural character).
    """
    out: List[str] = []
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            continue
        if ch == '"':
            if not in_string:
                in_string = True
                out.append(ch)
                continue
            # Inside a string: this quote ends the value only if the next
            # non-space character is a structural one.
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            nxt = text[j] if j < len(text) else ""
            if nxt in (",", "}", "]", ":"):
                in_string = False
                out.append(ch)
            else:
                out.append('\\"')
            continue
        out.append(ch)
        if not in_string and ch in "{[":
            pass
    candidate = "".join(out)
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _strip_token_noise(text: str) -> str:
    """Remove stray non-ASCII glyphs the model sometimes emits mid-token.

    Observed with rootsys/glm-5.3: `list_dir 之争path="..."` — a pair of
    CJK characters injected where a quote or colon should be. They carry no
    meaning for a tool call, so drop them.
    """
    return "".join(ch for ch in text if ord(ch) < 128 or ch in "\u2018\u2019\u201c\u201d")


def _parse_name_key_pairs(text: str) -> Optional[Dict[str, Any]]:
    """Parse the `name key="value" key2="value2"` shape.

    Some models emit the arguments as a bare sequence of `key="value"`
    pairs after the tool name, with no braces:
        list_dir path="." pattern="*.ts"
    """
    pairs: Dict[str, Any] = {}
    for m in re.finditer(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(".*?"|\'.*?\'|\{.*?\}|\[[^\]]*\]|[-0-9.]+|[A-Za-z_][A-Za-z0-9_]*)',
        text, flags=re.DOTALL,
    ):
        key, raw = m.group(1), m.group(2)
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            pairs[key] = raw[1:-1]
        else:
            try:
                pairs[key] = json.loads(raw)
            except json.JSONDecodeError:
                pairs[key] = raw
    return pairs or None


def _parse_arg_key_pairs(block: str) -> Dict[str, Any]:
    """Extract every `"key": value` pair from an `<arg_key>` block.

    The block can hold SEVERAL keys, e.g.

        command": "find main.ts", "args": {}

    which is a mangled JSON object missing its opening brace. Rebuild it as
    a real object and parse it.
    """
    text = block.strip()
    if not text:
        return {}
    # Close the dangling brace if the block ends with one.
    candidate = text
    if candidate.count("{") > candidate.count("}"):
        candidate += "}"
    # Prepend the missing opening brace when the block starts mid-object.
    if candidate.lstrip().startswith('"') and "{" not in candidate.split(":")[0]:
        candidate = "{" + candidate
    parsed = _coerce_json(candidate)
    if parsed:
        return parsed
    # Fall back to a regex sweep for "key": value pairs.
    out: Dict[str, Any] = {}
    # The FIRST key may be missing its opening quote (the model wrote
    # `command": "..."` rather than `"command": "..."`), so match the key
    # with an optional leading quote.
    for m in re.finditer(r'"?([A-Za-z_][A-Za-z0-9_]*)"?\s*:\s*(".*?"|\{.*?\}|\[[^\]]*\]|[-0-9.]+|[A-Za-z_][A-Za-z0-9_]*)',
                         text, flags=re.DOTALL):
        key, raw = m.group(1), m.group(2)
        if raw.startswith('"') and raw.endswith('"'):
            out[key] = raw[1:-1]
        else:
            try:
                out[key] = json.loads(raw)
            except json.JSONDecodeError:
                out[key] = raw
    return out


def _split_key_value(value: str) -> tuple:
    """Split a mangled `key: payload` / `key": payload` string.

    Models emit the key and the payload in one blob when the XML is
    broken, e.g. `args": "pwd && ls -la"}`. Returns (key, payload) with the
    key normalised (quotes and a trailing colon removed); the key is None
    when the value carries no key prefix.
    """
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[\"']?\s*:\s*(.*)$", value, flags=re.DOTALL)
    if not m:
        return None, value
    return m.group(1), m.group(2)


def _parse_pseudo_tool_call(body: str) -> Optional[Dict[str, Any]]:
    # Strip stray XML close/open tags the model may leave inside the body
    # (e.g. a trailing `</arg_value>` with no matching open).
    text = re.sub(
        r"</?(?!arg_key\b|arg_value\b)[A-Za-z_][A-Za-z0-9_]*>", " ", body
    ).strip()
    text = _strip_token_noise(text)
    if not text or text.startswith("{"):
        return None

    # ── Shape A: tool_name<arg_key>KEY</arg_key><arg_value>VALUE</arg_value>
    ka = re.search(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*<arg_key>\s*(.*?)\s*</arg_key>\s*"
        r"(?:<arg_value>)?\s*(.*?)\s*(?:</arg_value>)?\s*$",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    if ka:
        name = ka.group(1)
        key = ka.group(2).strip().rstrip(":").strip("'\"")
        value = ka.group(3).strip()
        args: Dict[str, Any] = {}
        if key:
            parsed = _coerce_json(value)
            if parsed is not None:
                args = parsed
            else:
                args = {key: _unquote(_strip_trailing_brace(value))}
        elif value:
            vkey, vpayload = _split_key_value(value)
            parsed = _coerce_json(vpayload)
            if parsed is not None:
                args = parsed
            else:
                pairs = _parse_arg_key_pairs(vpayload)
                args = pairs if pairs else {"input": _unquote(_strip_trailing_brace(vpayload))}
        return {"tool": name, "args": args}

    # ── Shape B: tool_name<arg_key>KEY<arg_value>VALUE</arg_value>
    kb = re.search(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*<arg_key>\s*(.*?)\s*(?:<arg_value>)?\s*"
        r"(.*?)\s*(?:</arg_value>)?\s*$",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    if kb:
        name = kb.group(1)
        key = kb.group(2).strip().rstrip(":").strip("'\"")
        value = kb.group(3).strip()
        args = {}
        if key:
            parsed = _coerce_json(value)
            if parsed is not None:
                args = parsed
            else:
                args = {key: _unquote(_strip_trailing_brace(value))}
        elif value:
            # The block may hold SEVERAL `"key": value` pairs, e.g.
            # `command": "find main.ts", "args": {}` — a mangled JSON object
            # missing its opening brace. Parse the WHOLE value as pairs
            # first; only fall back to a single key/payload split.
            pairs = _parse_arg_key_pairs(value)
            if len(pairs) > 1 or (pairs and "args" not in pairs):
                # A nested "args" key alongside real parameters is noise —
                # the tool wants the parameters at the top level.
                # A nested "args" key alongside real parameters is noise —
                # the tool wants the parameters at the top level.
                if isinstance(pairs.get("args"), dict):
                    args = {k: v for k, v in pairs.items() if k != "args"}
                else:
                    args = pairs
            else:
                vkey, vpayload = _split_key_value(value)
                parsed = _coerce_json(vpayload)
                if parsed is not None:
                    args = parsed
                elif vkey and vkey != "args":
                    args = {vkey: _unquote(_strip_trailing_brace(vpayload))}
                else:
                    args = {"input": _unquote(_strip_trailing_brace(vpayload))}
        return {"tool": name, "args": args}

    # ── Shape C: tool_name(args: {..}) / tool_name({..}) / tool_name("v")
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$", text, flags=re.DOTALL)
    if m:
        name, inner = m.group(1), m.group(2).strip()
        if not name:
            return None
        am = re.search(r"args\s*:\s*(\{.*\})\s*$", inner, flags=re.DOTALL)
        args = {}
        if am:
            parsed = _coerce_json(am.group(1))
            args = parsed if parsed is not None else {}
        else:
            parsed = _coerce_json(inner)
            if parsed is not None:
                args = parsed
            elif inner:
                try:
                    args = {"input": json.loads(inner)}
                except json.JSONDecodeError:
                    args = {"input": _unquote(inner)}
        return {"tool": name, "args": args}

    # ── Shape E2: tool_name key="value" key2="value2"
    m1 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(.*)$", text, flags=re.DOTALL)
    if m1:
        pairs = _parse_name_key_pairs(m1.group(2))
        if pairs:
            return {"tool": m1.group(1), "args": pairs}

    # ── Shape E: tool_name followed by a JSON object (possibly on the next
    # line), e.g. `terminal\n{"args": "pwd; ls -la"}`. The object's "args"
    # value may itself be a JSON STRING holding the real payload.
    m3 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(\{.*)?$", text, flags=re.DOTALL)
    if m3:
        name = m3.group(1)
        rest = (m3.group(2) or "").strip()
        if not rest:
            # A bare name is still a usable call — the tool reports its own
            # missing-argument error, which beats dropping the call entirely.
            return {"tool": name, "args": {}}
        if rest:
            parsed = _coerce_json(rest)
            if parsed is not None:
                # {"args": "pwd; ls -la"} — the args value is a command
                # string, not a mapping. Unwrap it into the payload.
                inner = parsed.get("args")
                if isinstance(inner, str):
                    nested = _coerce_json(inner)
                    if nested is not None:
                        return {"tool": name, "args": nested}
                    return {"tool": name, "args": {"input": inner}}
                if isinstance(inner, dict):
                    return {"tool": name, "args": inner}
                return {"tool": name, "args": parsed}
        return None

    return None


def _looks_like_tool_call(text: str) -> bool:
    """Heuristic: does the text intend to be a tool call?

    True when it contains a tool-call marker or a recognisable
    `tool_name(...)` / `tool_name key="value"` shape, even if the parser
    could not decode the arguments.
    """
    if not text:
        return False
    if "tool_call" in text or "arg_key" in text or "arg_value" in text:
        return True
    return bool(re.search(r"\b(read_file|write_file|search_files|terminal|list_dir)\b", text))


def _parse_tool_calls(text: str) -> List[dict]:
    """Extract tool calls from Hermes XML, markdown JSON, or raw JSON lines."""
    calls: List[dict] = []
    if not text:
        return calls

    # 1. Hermes <tool_call> tags
    xml_matches = re.findall(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL | re.IGNORECASE)
    # A body that starts with `{` is a JSON tool call. The non-greedy regex
    # stops at the FIRST `</`, which truncates a command containing `</` (e.g.
    # `--include=*.ts` is fine, but a path or regex can contain it). When
    # the body opens with `{`, take the BALANCED object from the ORIGINAL
    # text instead of the regex capture.
    for m in re.finditer(r"<tool_call>\s*(\{)", text, flags=re.IGNORECASE):
        start = m.start(1)
        parsed = _coerce_json(text[start:])
        if parsed:
            normalized = _normalize_tool_call(parsed)
            if normalized:
                calls.append(normalized)
    if calls:
        return calls
    for match in xml_matches:
        cleaned = match.strip()
        try:
            obj = json.loads(cleaned)
            normalized = _normalize_tool_call(obj)
            if normalized:
                calls.append(normalized)
        except json.JSONDecodeError:
            # Not JSON — the model may have used the `tool_name(args: {...})`
            # pseudo-call shape. Parse it rather than dropping the call.
            pseudo = _parse_pseudo_tool_call(cleaned)
            if pseudo:
                calls.append(pseudo)

    if calls:
        return calls

    # 2. Markdown code blocks
    in_json_block = False
    json_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```json"):
            in_json_block = True
            json_lines = []
            continue
        elif stripped == "```" and in_json_block:
            in_json_block = False
            json_text = "\n".join(json_lines).strip()
            try:
                obj = json.loads(json_text)
                normalized = _normalize_tool_call(obj)
                if normalized:
                    calls.append(normalized)
            except json.JSONDecodeError:
                pass
            json_lines = []
            continue

        if in_json_block:
            json_lines.append(line)
            continue

        # 3. Bare JSON lines
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                obj = json.loads(stripped)
                normalized = _normalize_tool_call(obj)
                if normalized:
                    calls.append(normalized)
            except json.JSONDecodeError:
                continue

    return calls


def _extract_thought(text: str) -> Optional[str]:
    """Extract Hermes/DeepSeek scratchpad thought if present."""
    match = re.search(r"<thought>(.*?)</thought>", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_steps(text: str) -> List[str]:
    """Extract numbered steps from plan text."""
    steps = []
    for line in text.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line[:4]:
            steps.append(line)
    return steps

class AgentLoop:
    def __init__(self, registry: ProviderRegistry, default_provider: str = "ollama",
                  model: str = "qwen2.5-coder:7b", yolo: bool = False,
                 auto_commit: bool = False, style: str = "jebat", context_window: int = 16384,
                 verbose: bool = False, system_prompt_extra: str = "",
                 budget_tokens: Optional[int] = None, deadline: Optional[float] = None):
        self.registry = registry
        self.default_provider = default_provider
        self.model = model
        self.messages: List[AgentMessage] = []
        self.max_iterations = 8
        self.yolo = yolo
        self.auto_commit = auto_commit
        self.style = style  # "jebat" or "openmanus"
        self.context_window = context_window
        self.verbose = verbose
        self.system_prompt_extra = system_prompt_extra
        self.budget_tokens = budget_tokens
        self.deadline = deadline

    def _render_history(self, limit: int = 8) -> str:
        return "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in self.messages[-limit:]]
        )

    def _call_provider(self, prompt: str, provider: str, model: str,
                        temperature: float = 0.2, max_tokens: int = 4096) -> CompletionResponse:
        """Call the provider through the registry or fallback to ollama runner."""
        bounded = budget_input(
            prompt,
            context_window=self.context_window,
            max_output_tokens=max_tokens,
            model=model,
            provider=provider,
        )
        impl = self.registry.get(provider)
        if impl:
            req = CompletionRequest(provider=provider, model=model, prompt=bounded.prompt,
                                    temperature=temperature, max_tokens=max_tokens)
            try:
                response = impl.complete(req)
                reported_tokens = getattr(response, "tokens_used", 0)
                usage = usage_from_texts(
                    bounded.prompt,
                    response.text,
                    model=model,
                    provider=provider,
                    raw_usage={"total_tokens": reported_tokens} if reported_tokens else None,
                )
                return CompletionResponse(
                    text=response.text,
                    model=response.model,
                    provider=response.provider,
                    tokens_used=usage.total_tokens,
                    latency_ms=response.latency_ms,
                )
            except Exception as exc:
                return CompletionResponse(text=f"[JEBAT provider error: {exc}]",
                                        model=model, provider=provider)
        # Fallback to ollama runner directly
        try:
            from jebat_cli_new.runner import ollama_complete
            text, latency_ms = ollama_complete(model=model, prompt=bounded.prompt,
                                               temperature=temperature, max_tokens=max_tokens)
            usage = usage_from_texts(bounded.prompt, text, model=model, provider=provider)
            return CompletionResponse(text=text, model=model, provider=provider,
                                     tokens_used=usage.total_tokens, latency_ms=latency_ms)
        except Exception as exc:
            return CompletionResponse(text=f"[JEBAT provider error: {exc}]",
                                    model=model, provider=provider)

    def step(self, prompt: str, provider: Optional[str] = None,
              model: Optional[str] = None, plan: bool = False) -> AgentStep:
        provider_name = provider or self.default_provider
        model_name = model or self.model

        # Select system prompt based on style
        sys_prompt = SYSTEM_PROMPT if self.style == "openmanus" else MINIMAL_PROMPT
        if self.system_prompt_extra:
            sys_prompt += "\n\n" + self.system_prompt_extra
        from jebat_cli_new.tool_bridge import shared_tool_prompt
        sys_prompt += shared_tool_prompt()

        if plan:
            history = "\n".join([
                SYSTEM_PROMPT,  # Always use full prompt for planning
                self._render_history(),
                f"TASK: {prompt}",
                " Begin with numbered steps.",
            ])
        else:
            history = "\n".join([sys_prompt, self._render_history(), f"USER: {prompt}"])

        iteration = 0
        all_tool_actions: List[str] = []
        total_tokens = 0
        last_text = ""
        final_answer: Optional[str] = None
        working_conversation = history
        last_latency = 0.0

        # Optional incremental progress reporter (set by the MCP server for
        # long-running tools). Never active in plain CLI runs.
        from jebat_cli_new.progress import PROGRESS_REPORTER, report as _report_progress

        _reporter = PROGRESS_REPORTER.get()
        _notify_progress = (
            (lambda frac, msg: _report_progress(min(max(frac, 0.0), 1.0), msg)))
        max_iters = max(self.max_iterations, 1)

        def _step_progress(stage: str, frac: float) -> None:
            _notify_progress(frac, f"iteration {iteration + 1}/{max_iters}: {stage}")

        budget_exhausted = False
        while iteration < self.max_iterations:
            # Hard budget gates (agentix): cumulative tokens and wall clock.
            if self.budget_tokens is not None and total_tokens >= self.budget_tokens:
                budget_exhausted = True
                break
            if self.deadline is not None and time.time() >= self.deadline:
                budget_exhausted = True
                break
            _step_progress("reasoning", iteration / max_iters)
            resp = self._call_provider(
                working_conversation,
                provider_name,
                model_name,
                temperature=0.2 if not plan else 0.4,
            )
            total_tokens += resp.tokens_used
            last_text = resp.text
            last_latency = resp.latency_ms

            if "FINAL_ANSWER:" in last_text:
                final_answer = last_text.split("FINAL_ANSWER:", 1)[1].strip()
                break

            thought = _extract_thought(last_text)
            if thought and self.verbose:
                TerminalUX.thought_card(thought)

            tool_calls = _parse_tool_calls(last_text)
            if not tool_calls:
                # The model may have produced a tool call in a shape the
                # parser does not recognise. Do NOT silently end the run:
                # ask the model to restate the call in the documented form.
                # Dropping it here ends the task with the raw text as the
                # "final answer" — a half-finished audit.
                if _looks_like_tool_call(last_text) and iteration + 1 < self.max_iterations:
                    working_conversation = (
                        f"{working_conversation}\n\n"
                        f"ASSISTANT:\n{last_text}\n\n"
                        "Your tool call was not understood. Restate it as exactly one "
                        "of these, with no extra text:\n"
                        '<tool_call>\n{"tool": "tool_name", "args": {"param": "value"}}\n</tool_call>\n'
                        "or output FINAL_ANSWER: <your complete answer>"
                    )
                    iteration += 1
                    continue
                # Model finished turn without further tool calls
                break

            tool_results = []
            _step_progress("acting", (iteration + 0.5) / max_iters)
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                tool_args = tc.get("args", {})
                action_desc = f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)[:120]})"
                all_tool_actions.append(action_desc)

                t_start = time.time()
                raw_result = execute_tool(tool_name, tool_args, yolo=self.yolo)
                lat_ms = (time.time() - t_start) * 1000
                is_err = raw_result.startswith("[TOOL_SCHEMA_ERROR") or "Error" in raw_result[:20]

                # ── Autonomous AGI Reflexion Gate ──
                try:
                    from jebat.core.agi_core import AGICognitiveEngine
                    engine = AGICognitiveEngine()
                    reflexion = engine.reflexion_gate(tool_name, tool_args, raw_result)
                    if not reflexion.passed:
                        is_err = True
                        raw_result = (
                            f"{raw_result}\n\n"
                            f"{reflexion.actionable_feedback}"
                        )
                except Exception:
                    pass
                if self.verbose:
                    TerminalUX.tool_card(tool_name, tool_args, raw_result, latency_ms=lat_ms, is_error=is_err)

                folded_result = _truncate_observation(raw_result, max_chars=4000)
                tool_results.append(
                    f'<tool_response name="{tool_name}">\n{folded_result}\n</tool_response>'
                )
            observations = "\n\n".join(tool_results)
            working_conversation = (
                f"{working_conversation}\n\n"
                f"ASSISTANT:\n{last_text}\n\n"
                f"OBSERVATION:\n{observations}\n\n"
                "Continue with your next step using <thought> and <tool_call>, or output FINAL_ANSWER:"
            )
            iteration += 1

        # A turn that ended without a FINAL_ANSWER and without any tool
        # call leaves `last_text` holding raw model prose (often a
        # half-written tool call). Synthesise an answer from what was done
        # rather than returning that prose as if it were the conclusion.
        if (not final_answer and not all_tool_actions and last_text.strip()
                # A provider error is not an unfinished task — it is a
                # failure. Let it propagate so the caller reports it.
                and not last_text.startswith("[JEBAT provider error:")):
            wrap_prompt = (
                f"{working_conversation}\n\n"
                "You did not complete the task. Provide your FINAL_ANSWER now, "
                "citing only what you verified, and state explicitly what you could "
                "not check."
            )
            wrap_resp = self._call_provider(wrap_prompt, provider_name, model_name, temperature=0.2)
            total_tokens += wrap_resp.tokens_used
            last_text = wrap_resp.text
            if "FINAL_ANSWER:" in last_text:
                final_answer = last_text.split("FINAL_ANSWER:", 1)[1].strip()
            else:
                final_answer = last_text

        # Synthesis pass if loop exhausted max_iterations without explicit FINAL_ANSWER
        if (iteration >= self.max_iterations or budget_exhausted) and not final_answer and all_tool_actions:
            wrap_prompt = (
                f"{working_conversation}\n\n"
                "You have reached the maximum step limit. Summarize your findings and provide your FINAL_ANSWER:"
            )
            wrap_resp = self._call_provider(wrap_prompt, provider_name, model_name, temperature=0.2)
            total_tokens += wrap_resp.tokens_used
            last_text = wrap_resp.text
            if "FINAL_ANSWER:" in last_text:
                final_answer = last_text.split("FINAL_ANSWER:", 1)[1].strip()
            else:
                final_answer = last_text

        self.messages.append(AgentMessage(role="user", content=prompt))
        self.messages.append(
            AgentMessage(
                role="assistant",
                content=last_text,
                tool_calls=json.dumps(all_tool_actions) if all_tool_actions else None,
            )
        )

        # ── Epistemic Consolidation ──
        try:
            import asyncio
            from jebat.core.agi_core import AGICognitiveEngine
            asyncio.run(AGICognitiveEngine().consolidate_learning(prompt, final_answer or last_text, all_tool_actions))
        except Exception:
            pass

        return AgentStep(
            prompt=prompt,
            response=CompletionResponse(
                text=final_answer or last_text or "",
                model=model_name,
                provider=provider_name,
                tokens_used=total_tokens,
                latency_ms=last_latency,
            ),
            tool_actions=all_tool_actions,
            plan=last_text if plan else None,
            observation=final_answer,
            steps=_extract_steps(last_text) if plan else [],
        )

    def run_plan_then_answer(self, prompt: str, provider: Optional[str] = None,
                            model: Optional[str] = None):
        """OpenManus-style: plan first, then execute."""
        print("  ⟳ Planning...")
        plan_step = self.step(prompt, provider=provider, model=model, plan=True)
        print("  ✓ Plan ready\n")
        print(plan_step.plan or "No plan")
        print()
        answer_step = self.step(f"Follow this plan:\n{plan_step.plan}\nTASK: {prompt}",
                               provider=provider, model=model, plan=False)
        return answer_step

    def interactive(self, provider: Optional[str] = None, model: Optional[str] = None,
                   mode: str = "auto", style: str = "jebat"):
        """OpenClaude-style interactive REPL."""
        provider_name = provider or self.default_provider
        model_name = model or self.model
        self.style = style

        print()
        print("  JEBAT  ⚔️  unified coding agent")
        print(f"  provider: {provider_name}  model: {model_name}")
        print(f"  style: {self.style}  mode: {mode}")
        print()
        print("  /help, /plan, /provider, /model, /clear, /exit")
        print()

        while True:
            try:
                prompt = input(f"  [{provider_name}:{model_name}] ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not prompt:
                continue

            if prompt.lower() in {"/exit", "/quit", "/q"}:
                print("  Exiting.")
                break

            if prompt.lower() in {"/clear", "/reset"}:
                self.messages.clear()
                print("  Session cleared.")
                continue

            if prompt.lower() == "/help":
                print("  Commands:")
                print("    /help     Show this help")
                print("    /plan     Plan-then-answer mode")
                print("    /provider Switch provider")
                print("    /model    Switch model")
                print("    /clear    Clear conversation")
                print("    /exit     Exit session")
                continue

            if prompt.lower() == "/plan":
                task = input("  Task: ").strip()
                if task:
                    out = self.run_plan_then_answer(task, provider=provider_name, model=model_name)
                    print(f"\n  {out.response.text}\n")
                continue

            if prompt.lower().startswith("/provider "):
                provider_name = prompt.split(None, 1)[1].strip()
                print(f"  provider: {provider_name}")
                continue

            if prompt.lower().startswith("/model "):
                model_name = prompt.split(None, 1)[1].strip()
                print(f"  model: {model_name}")
                continue

            out = self.step(prompt, provider=provider_name, model=model_name,
                           plan=(mode == "plan"))
            print(f"\n  {out.response.text}\n")
