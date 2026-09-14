from __future__ import annotations

from jebat_cli_new.agent import _extract_thought, _parse_tool_calls, _truncate_observation, AgentLoop
from jebat_cli_new.models import CompletionResponse
from jebat_cli_new.providers import ProviderRegistry
from jebat_cli_new.tools import execute_tool


def test_parse_hermes_tool_calls():
    # Hermes XML tag format
    xml_text = """
    <thought>I should inspect the repository structure first.</thought>
    <tool_call>
    {"tool": "list_dir", "args": {"path": "."}}
    </tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "list_dir"
    assert calls[0]["args"]["path"] == "."


def test_parse_openai_hermes_style_keys():
    # OpenAI/Hermes style: name and arguments
    raw_text = """
    <tool_call>
    {"name": "read_file", "arguments": "{\\"path\\": \\"main.py\\", \\"limit\\": 10}"}
    </tool_call>
    """
    calls = _parse_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "read_file"
    assert calls[0]["args"]["path"] == "main.py"
    assert calls[0]["args"]["limit"] == 10


def test_extract_thought():
    text = "<thought>Thinking carefully about the problem</thought> Done."
    assert _extract_thought(text) == "Thinking carefully about the problem"


def test_observation_folding():
    short = "Hello world"
    assert _truncate_observation(short, max_chars=50) == "Hello world"

    long_text = "A" * 5000
    folded = _truncate_observation(long_text, max_chars=100)
    assert "characters omitted for context budget" in folded
    assert len(folded) < 300


def test_atomic_tool_validation_error():
    # Calling read_file without required 'path' parameter
    result = execute_tool("read_file", {"limit": 10}, yolo=True)
    assert "[TOOL_SCHEMA_ERROR for read_file]" in result
    assert "path" in result


class MockProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.index = 0

    def complete(self, req):
        if self.index < len(self.responses):
            text = self.responses[self.index]
            self.index += 1
        else:
            text = "FINAL_ANSWER: Done."
        return CompletionResponse(text=text, model="mock", provider="mock", tokens_used=10, latency_ms=1)


def test_multiturn_react_loop():
    registry = ProviderRegistry()
    responses = [
        '<thought>Listing dir</thought><tool_call>{"tool": "list_dir", "args": {"path": "."}}</tool_call>',
        '<thought>Reading file</thought><tool_call>{"tool": "read_file", "args": {"path": "pyproject.toml", "limit": 2}}</tool_call>',
        'FINAL_ANSWER: Found dependencies in pyproject.toml',
    ]
    mock = MockProvider(responses)
    registry.register("mock", mock)

    loop = AgentLoop(registry=registry, default_provider="mock", model="mock", yolo=True)
    step = loop.step("Analyze pyproject")

    # Verify both tool calls were recorded
    assert len(step.tool_actions) == 2
    assert "list_dir" in step.tool_actions[0]
    assert "read_file" in step.tool_actions[1]
    assert step.response.text == "Found dependencies in pyproject.toml"
