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


def _parse_tool_calls(text: str) -> List[dict]:
    """Extract tool calls from Hermes XML, markdown JSON, or raw JSON lines."""
    calls: List[dict] = []
    if not text:
        return calls

    # 1. Hermes <tool_call> tags
    xml_matches = re.findall(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL | re.IGNORECASE)
    for match in xml_matches:
        cleaned = match.strip()
        try:
            obj = json.loads(cleaned)
            normalized = _normalize_tool_call(obj)
            if normalized:
                calls.append(normalized)
        except json.JSONDecodeError:
            pass

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
                 verbose: bool = False):
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

        while iteration < self.max_iterations:
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
                # Model finished turn without further tool calls
                break

            tool_results = []
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

        # Synthesis pass if loop exhausted max_iterations without explicit FINAL_ANSWER
        if iteration >= self.max_iterations and not final_answer and all_tool_actions:
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
