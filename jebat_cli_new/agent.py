"""
JEBAT — agent loop / runtime with OpenManus-style multi-step planning
and OpenClaude-style UX for coding tasks.
"""

from __future__ import annotations

import json, textwrap
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from jebat_cli_new.models import ProviderConfig, CompletionRequest, CompletionResponse
from jebat_cli_new.providers import ProviderRegistry
from jebat_cli_new.tools import TOOL_DEFINITIONS, execute_tool


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


# OpenManus-style system prompt
SYSTEM_PROMPT = textwrap.dedent("""
You are JEBAT, an advanced coding agent. You follow the OpenManus methodology:

1. ANALYZE: Understand the task thoroughly
2. PLAN: Break down into numbered steps
3. EXECUTE: Use tools to implement each step
4. VERIFY: Check your work
5. REPORT: Provide a final answer

You have access to these native tools:
- read_file(path, offset=1, limit=200) — Read a file
- write_file(path, content) — Write content to a file
- search_files(pattern, path=".", target="files", file_glob="", limit=50) — Search files
- terminal(command, timeout=120, workdir=None) — Execute shell command
- list_dir(path=".", pattern="*") — List directory contents

To use a tool, output a JSON tool call:
```json
{"tool": "tool_name", "args": {"param": "value"}}
```

After each tool call, you'll receive the result as TOOL_RESULT.
Use results to inform your next action.

When done, output: FINAL_ANSWER: <your answer>
""").strip()

# OpenClaude-style minimal prompt
MINIMAL_PROMPT = textwrap.dedent("""
You are JEBAT, a coding agent. Be direct and concise.

Tools: read_file, write_file, search_files, terminal, list_dir

To use a tool:
```json
{"tool": "tool_name", "args": {"param": "value"}}
```

After tool calls, you get TOOL_RESULT.
End with: FINAL_ANSWER: <answer>
""").strip()


def _parse_tool_calls(text: str) -> List[dict]:
    """Extract JSON tool calls from agent output."""
    calls = []
    in_json_block = False
    json_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        # Handle markdown code blocks
        if stripped.startswith("```json"):
            in_json_block = True
            json_lines = []
            continue
        elif stripped == "```" and in_json_block:
            in_json_block = False
            json_text = "\n".join(json_lines).strip()
            try:
                obj = json.loads(json_text)
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
            json_lines = []
            continue

        if in_json_block:
            json_lines.append(line)
            continue

        # Handle bare JSON lines
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                obj = json.loads(stripped)
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                continue

    return calls


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
                 auto_commit: bool = False, style: str = "jebat"):
        self.registry = registry
        self.default_provider = default_provider
        self.model = model
        self.messages: List[AgentMessage] = []
        self.max_iterations = 8
        self.yolo = yolo
        self.auto_commit = auto_commit
        self.style = style  # "jebat" or "openmanus"

    def _render_history(self, limit: int = 8) -> str:
        return "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in self.messages[-limit:]]
        )

    def _call_provider(self, prompt: str, provider: str, model: str,
                       temperature: float = 0.2, max_tokens: int = 4096) -> CompletionResponse:
        """Call the provider through the registry or fallback to ollama runner."""
        impl = self.registry.get(provider)
        if impl:
            req = CompletionRequest(provider=provider, model=model, prompt=prompt,
                                   temperature=temperature, max_tokens=max_tokens)
            try:
                return impl.complete(req)
            except Exception as exc:
                return CompletionResponse(text=f"[JEBAT provider error: {exc}]",
                                        model=model, provider=provider)
        # Fallback to ollama runner directly
        try:
            from jebat_cli_new.runner import ollama_complete
            text, latency_ms = ollama_complete(model=model, prompt=prompt,
                                              temperature=temperature, max_tokens=max_tokens)
            return CompletionResponse(text=text, model=model, provider=provider,
                                    latency_ms=latency_ms)
        except Exception as exc:
            return CompletionResponse(text=f"[JEBAT provider error: {exc}]",
                                    model=model, provider=provider)

    def step(self, prompt: str, provider: Optional[str] = None,
             model: Optional[str] = None, plan: bool = False) -> AgentStep:
        provider_name = provider or self.default_provider
        model_name = model or self.model

        # Select system prompt based on style
        sys_prompt = SYSTEM_PROMPT if self.style == "openmanus" else MINIMAL_PROMPT

        if plan:
            history = "\n".join([
                SYSTEM_PROMPT,  # Always use full prompt for planning
                self._render_history(),
                f"TASK: {prompt}",
                " Begin with numbered steps.",
            ])
        else:
            history = "\n".join([sys_prompt, self._render_history(), f"USER: {prompt}"])

        resp = self._call_provider(history, provider_name, model_name,
                                  temperature=0.2 if not plan else 0.4)
        text = resp.text

        # Parse tool calls from response
        tool_calls = _parse_tool_calls(text)
        tool_actions = []
        tool_results = []

        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            tool_args = tc.get("args", {})
            tool_actions.append(f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)[:120]})")
            result = execute_tool(tool_name, tool_args, yolo=self.yolo)
            tool_results.append(f"TOOL_RESULT[{tool_name}]: {result[:500]}")

        # If tool calls were made, feed results back for a second pass
        final_answer = None
        if tool_calls:
            observation = "\n".join(tool_results)
            follow_up = f"{history}\n\nASSISTANT: {text}\n\n{observation}\n\nNow provide your final answer: FINAL_ANSWER: "
            resp2 = self._call_provider(follow_up, provider_name, model_name)
            text = resp2.text

        if "FINAL_ANSWER:" in text:
            final_answer = text.split("FINAL_ANSWER:", 1)[1].strip()

        self.messages.append(AgentMessage(role="user", content=prompt))
        self.messages.append(AgentMessage(role="assistant", content=text,
                                         tool_calls=json.dumps(tool_actions) if tool_actions else None))

        return AgentStep(
            prompt=prompt,
            response=CompletionResponse(
                text=text or final_answer or "",
                model=model_name,
                provider=provider_name,
                tokens_used=resp.tokens_used,
                latency_ms=resp.latency_ms,
            ),
            tool_actions=tool_actions,
            plan=text if plan else None,
            observation=final_answer,
            steps=_extract_steps(text) if plan else [],
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
