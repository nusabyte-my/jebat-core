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


def test_parse_pseudo_tool_call_shape():
    # Some models emit `tool_name(args: {...})` instead of the documented
    # `{"tool": ..., "args": {...}}` JSON. The JSON parser rejects that body,
    # so the call used to be dropped silently — the agent loop then saw no
    # tool calls, treated the text as the final answer and stopped after one
    # turn with no work done. Seen live with rootsys/glm-5.3 on 2026-10-25.
    xml_text = """
    <thought>Find the repo first.</thought>
    <tool_call>
    terminal(command, args: {"command": "pwd && ls -la"})
    </tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "terminal"
    assert calls[0]["args"]["command"] == "pwd && ls -la"


def test_parse_pseudo_tool_call_object_only():
    xml_text = """
    <tool_call>
    list_dir({"path": "."})
    </tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "list_dir"
    assert calls[0]["args"]["path"] == "."


def test_parse_pseudo_tool_call_positional_string():
    xml_text = """
    <tool_call>
    read_file("main.py")
    </tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "read_file"
    assert calls[0]["args"]["input"] == "main.py"


def test_parse_pseudo_tool_call_arg_key_shape():
    # rootsys/glm-5.3 also emits a malformed XML variant with an <arg_key>
    # tag and NO closing </arg_key>. Observed live 2026-10-25.
    xml_text = """
    <tool_call>terminal<arg_key>args": {"command": "pwd && ls -la"}</arg_value></tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "terminal"
    assert calls[0]["args"]["command"] == "pwd && ls -la"


def test_parse_pseudo_tool_call_arg_key_with_closing_tag():
    xml_text = """
    <tool_call>terminal<arg_key>command</arg_key><arg_value>ls</arg_value></tool_call>
    """
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "terminal"
    assert calls[0]["args"]["command"] == "ls"


def test_parse_pseudo_tool_call_bare_name():
    # A bare name is still a usable call — the tool reports its own
    # missing-argument error, which beats dropping the call entirely.
    xml_text = "<tool_call>list_dir</tool_call>"
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "list_dir"
    assert calls[0]["args"] == {}


def test_parse_pseudo_tool_call_python_dict_literal():
    xml_text = """<tool_call>shell_exec {'command': "ls"}</tool_call>"""
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "shell_exec"
    assert calls[0]["args"]["command"] == "ls"


def test_parse_pseudo_tool_call_args_string_shape():
    # A third rootsys shape: the name, then a JSON object on the next line
    # whose "args" value is a plain command STRING rather than a mapping.
    xml_text = '<tool_call>terminal\n{"args": "pwd; ls -la"}</arg_value></tool_call>'
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "terminal"
    assert calls[0]["args"]["input"] == "pwd; ls -la"


def test_parse_pseudo_tool_call_trailing_xml_after_object():
    # Stray XML close tags after the payload must not defeat the JSON read.
    xml_text = '<tool_call>terminal\n{"args": {"command": "pwd"}}</arg_value></tool_call>'
    calls = _parse_tool_calls(xml_text)
    assert len(calls) == 1
    assert calls[0]["tool"] == "terminal"
    assert calls[0]["args"]["command"] == "pwd"


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


def test_multiturn_react_loop(tmp_path):
    # register() persists to disk — isolate to tmp so the real
    # ~/.jebat/jebat-cli-providers.json is never polluted.
    registry = ProviderRegistry(path=str(tmp_path / "providers.json"))
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
