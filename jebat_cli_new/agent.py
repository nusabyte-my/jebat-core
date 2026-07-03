"""
JEBAT — agent loop / runtime with OpenManus-style multi-step planning
and native tool execution for coding tasks.
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


PLAN_PROMPT = textwrap.dedent("""
You are JEBAT, a coding agent. Reason stepwise.
Format your plan as numbered steps:
1. ...
2. ...
Then output the final answer as: FINAL_ANSWER: <...>.
""").strip()

TOOLS_SPEC = """You have access to these native tools:

1. read_file(path, offset=1, limit=200) — Read a file, returns content with line numbers.
2. write_file(path, content) — Write content to a file, creates dirs if needed.
3. search_files(pattern, path=".", target="files", file_glob="", limit=50) — Search by glob or grep.
4. terminal(command, timeout=120, workdir=None) — Execute a shell command.
5. list_dir(path=".", pattern="*") — List directory contents.

To use a tool, output a JSON tool call on its own line:
```json
{"tool": "read_file", "args": {"path": "file.py"}}
```

You may issue multiple tool calls. After each tool call, you will receive the result
as a TOOL_RESULT message. Use tool results to inform your next action.

When you are done, output your final answer as: FINAL_ANSWER: <your answer>
"""


def _parse_tool_calls(text: str) -> List[dict]:
    """Extract JSON tool calls from agent output."""
    calls = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("```json") and line.endswith("```"):
            try:
                obj = json.loads(line[7:-3].strip())
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                continue
        elif line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                continue
    return calls


class AgentLoop:
    def __init__(self, registry: ProviderRegistry, default_provider: str = "ollama", model: str = "qwen2.5-coder:7b", yolo: bool = False, auto_commit: bool = False):
        self.registry = registry
        self.default_provider = default_provider
        self.model = model
        self.messages: List[AgentMessage] = []
        self.max_iterations = 8
        self.yolo = yolo
        self.auto_commit = auto_commit

    def _render_history(self, limit: int = 8) -> str:
        return "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in self.messages[-limit:]]
        )

    def _call_provider(self, prompt: str, provider: str, model: str, temperature: float = 0.2, max_tokens: int = 4096) -> CompletionResponse:
        """Call the provider through the registry or fallback to ollama runner."""
        impl = self.registry.get(provider)
        if impl:
            req = CompletionRequest(provider=provider, model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
            try:
                return impl.complete(req)
            except Exception as exc:
                return CompletionResponse(text=f"[JEBAT provider error: {exc}]", model=model, provider=provider)
        # Fallback to ollama runner directly
        try:
            from jebat_cli_new.runner import ollama_complete
            text, latency_ms = ollama_complete(model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
            return CompletionResponse(text=text, model=model, provider=provider, latency_ms=latency_ms)
        except Exception as exc:
            return CompletionResponse(text=f"[JEBAT provider error: {exc}]", model=model, provider=provider)

    def step(self, prompt: str, provider: Optional[str] = None, model: Optional[str] = None, plan: bool = False) -> AgentStep:
        provider_name = provider or self.default_provider
        model_name = model or self.model

        if plan:
            history = "\n".join([
                PLAN_PROMPT,
                TOOLS_SPEC,
                self._render_history(),
                f"TASK: {prompt}",
                " Begin with numbered steps.",
            ])
        else:
            history = "\n".join([self._render_history(), TOOLS_SPEC, f"USER: {prompt}"])

        resp = self._call_provider(history, provider_name, model_name, temperature=0.2 if not plan else 0.4)
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
        self.messages.append(AgentMessage(role="assistant", content=text, tool_calls=json.dumps(tool_actions) if tool_actions else None))

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
        )

    def run_plan_then_answer(self, prompt: str, provider: Optional[str] = None, model: Optional[str] = None):
        plan_step = self.step(prompt, provider=provider, model=model, plan=True)
        print("[plan]\n" + (plan_step.plan or "No plan") + "\n")
        answer_step = self.step(f"Follow this plan:\n{plan_step.plan}\nTASK: {prompt}", provider=provider, model=model, plan=False)
        return answer_step

    def interactive(self, provider: Optional[str] = None, model: Optional[str] = None, mode: str = "auto"):
        provider_name = provider or self.default_provider
        model_name = model or self.model
        print(f"JEBAT code :: provider={provider_name} model={model_name} mode={mode}")
        print("Type /help for commands, Ctrl+C or /exit to quit\n")
        while True:
            try:
                prompt = input(">> ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if not prompt:
                continue
            if prompt.lower() in {"/exit", "/quit", "/q"}:
                break
            if prompt.lower() in {"/clear", "/reset"}:
                self.messages.clear()
                print("Session cleared")
                continue
            if prompt.lower() == "/plan":
                out = self.run_plan_then_answer("", provider=provider_name, model=model_name)
                print(out.response.text + "\n")
                continue
            if prompt.lower() == "/help":
                print("Commands: /help /exit /clear /plan /provider <id> /model <name>")
                continue
            if prompt.lower().startswith("/provider "):
                provider_name = prompt.split(None, 1)[1].strip()
                print(f"Switched to provider: {provider_name}")
                continue
            if prompt.lower().startswith("/model "):
                model_name = prompt.split(None, 1)[1].strip()
                print(f"Switched to model: {model_name}")
                continue

            out = self.step(prompt, provider=provider_name, model=model_name, plan=(mode == "plan"))
            print(out.response.text + "\n")
