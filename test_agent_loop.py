"""Unit tests for jebat.core.agent_loop — pure logic functions.

Covers:
- ReAct text pattern extraction (_extract_react_tool_calls)
- API-level tool call extraction (_extract_api_tool_calls)
- Tool result formatting (_format_tool_result_for_llm)
- Conversation history compaction (_compact_conversation_history)
- Safety mode approval logic (_should_approve_tool)
- Tool system prompt appendix (_build_tool_system_prompt_appendix)
- Dataclass construction (ToolCallStep, AgentResult)
- Project context section building (_build_project_context_section)
"""

from __future__ import annotations

import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import fields

# Import the module under test
# Note: pyproject.toml sets pythonpath=["jebat-core"] so jebat.core.agent_loop
# resolves to jebat-core/jebat/core/agent_loop.py (the full package)
from jebat.core.agent_loop import (
    _extract_react_tool_calls,
    _extract_api_tool_calls,
    _format_tool_result_for_llm,
    _compact_conversation_history,
    _should_approve_tool,
    _build_tool_system_prompt_appendix,
    _build_project_context_section,
    ToolCallStep,
    AgentResult,
    SafetyMode,
    MAX_ITERATIONS,
    DEFAULT_MAX_CONTEXT_TOKENS,
)


# ═══════════════════════════════════════════════════════════════════════
# ReAct Pattern Extraction
# ═══════════════════════════════════════════════════════════════════════


class TestExtractReactToolCalls:
    """Tests for _extract_react_tool_calls (ReAct text pattern parsing)."""

    def test_single_json_action(self):
        text = 'Action: terminal\nAction Input: {"command": "ls -la"}'
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "terminal"
        assert calls[0][1] == {"command": "ls -la"}

    def test_multiple_actions(self):
        text = (
            'Action: terminal\nAction Input: {"command": "pwd"}\n'
            "Observation: /home/user\n"
            'Action: write_file\nAction Input: {"path": "out.txt", "content": "hello"}'
        )
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 2
        assert calls[0][0] == "terminal"
        assert calls[1][0] == "write_file"
        assert calls[1][1]["path"] == "out.txt"

    def test_string_param_double_quotes(self):
        text = 'Action: web_search\nAction Input: "python async patterns"'
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "web_search"
        assert calls[0][1] == {"query": "python async patterns"}

    def test_string_param_single_quotes(self):
        text = "Action: web_search\nAction Input: 'rust vs go'"
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][1] == {"query": "rust vs go"}

    def test_array_param(self):
        text = 'Action: memory_recall\nAction Input: ["topic_a", "topic_b"]'
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][1] == {"items": ["topic_a", "topic_b"]}

    def test_no_actions_returns_empty(self):
        calls = _extract_react_tool_calls("Just a plain text response.")
        assert calls == []

    def test_case_insensitive(self):
        text = 'action: Terminal\naction input: {"command": "echo hi"}'
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "Terminal"

    def test_malformed_json_fallback(self):
        text = 'Action: terminal\nAction Input: {broken json}}'
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert "raw_input" in calls[0][1]

    def test_action_with_whitespace(self):
        text = 'Action:  file_read  \nAction Input:  {"path": "/etc/hosts"}  '
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        assert calls[0][0] == "file_read"
        assert calls[0][1]["path"] == "/etc/hosts"

    def test_thought_and_observation_not_matched(self):
        text = (
            "Thought: I should check the file.\n"
            'Action: terminal\nAction Input: {"command": "cat file.txt"}\n'
            "Observation: file contents here"
        )
        calls = _extract_react_tool_calls(text)
        assert len(calls) == 1
        # Only the Action line should be matched, not Thought or Observation


# ═══════════════════════════════════════════════════════════════════════
# API-Level Tool Call Extraction
# ═══════════════════════════════════════════════════════════════════════


class TestExtractApiToolCalls:
    """Tests for _extract_api_tool_calls (OpenAI/Anthropic structured tool_calls)."""

    def test_openai_style(self):
        data = {
            "tool_calls": [
                {
                    "name": "terminal",
                    "arguments": '{"command": "ls"}',
                }
            ]
        }
        calls = _extract_api_tool_calls(data)
        assert len(calls) == 1
        assert calls[0] == ("terminal", {"command": "ls"})

    def test_openai_function_style(self):
        data = {
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": '{"path": "a.txt", "content": "hi"}',
                    }
                }
            ]
        }
        calls = _extract_api_tool_calls(data)
        assert len(calls) == 1
        assert calls[0][0] == "write_file"
        assert calls[0][1]["path"] == "a.txt"

    def test_arguments_as_dict(self):
        data = {"tool_calls": [{"name": "terminal", "arguments": {"command": "pwd"}}]}
        calls = _extract_api_tool_calls(data)
        assert len(calls) == 1
        assert calls[0][1] == {"command": "pwd"}

    def test_empty_tool_calls(self):
        data = {"tool_calls": []}
        calls = _extract_api_tool_calls(data)
        assert calls == []

    def test_no_tool_calls_key(self):
        data = {"choices": [{"message": {"content": "Hello!"}}]}
        calls = _extract_api_tool_calls(data)
        assert calls == []

    def test_non_dict_input(self):
        calls = _extract_api_tool_calls("not a dict")
        assert calls == []

    def test_none_input(self):
        calls = _extract_api_tool_calls(None)
        assert calls == []

    def test_malformed_json_arguments(self):
        data = {"tool_calls": [{"name": "terminal", "arguments": "{bad json}"}]}
        calls = _extract_api_tool_calls(data)
        assert len(calls) == 1
        assert "raw_arguments" in calls[0][1]

    def test_empty_name_skipped(self):
        data = {"tool_calls": [{"name": "", "arguments": "{}"}]}
        calls = _extract_api_tool_calls(data)
        assert calls == []

    def test_multiple_calls(self):
        data = {
            "tool_calls": [
                {"name": "file_read", "arguments": '{"path": "a.py"}'},
                {"name": "terminal", "arguments": '{"command": "python a.py"}'},
            ]
        }
        calls = _extract_api_tool_calls(data)
        assert len(calls) == 2
        assert calls[0][0] == "file_read"
        assert calls[1][0] == "terminal"


# ═══════════════════════════════════════════════════════════════════════
# Tool Result Formatting
# ═══════════════════════════════════════════════════════════════════════


class TestFormatToolResultForLlm:
    """Tests for _format_tool_result_for_llm."""

    def test_error_result(self):
        result = _format_tool_result_for_llm("terminal", None, "Permission denied")
        assert "error: Permission denied" in result
        assert "terminal" in result

    def test_dict_result(self):
        result = _format_tool_result_for_llm("file_read", {"content": "hello"}, None)
        assert "file_read result:" in result
        assert "hello" in result

    def test_string_result(self):
        result = _format_tool_result_for_llm("terminal", "output text", None)
        assert "terminal result: output text" in result

    def test_large_dict_truncated(self):
        big_dict = {"data": "x" * 5000}
        result = _format_tool_result_for_llm("test_tool", big_dict, None)
        assert "truncated" in result

    def test_large_string_truncated(self):
        big_str = "x" * 5000
        result = _format_tool_result_for_llm("test_tool", big_str, None)
        # String results are sliced to 4000 chars, but the prefix is also added
        assert "test_tool result:" in result

    def test_non_serializable_dict_value(self):
        result = _format_tool_result_for_llm("test_tool", {"obj": object()}, None)
        assert "test_tool result:" in result

    def test_none_result_no_error(self):
        result = _format_tool_result_for_llm("test_tool", None, None)
        assert "test_tool result: None" in result


# ═══════════════════════════════════════════════════════════════════════
# Conversation History Compaction
# ═══════════════════════════════════════════════════════════════════════


class TestCompactConversationHistory:
    """Tests for _compact_conversation_history (semantic chunking)."""

    def _make_messages(self, count: int) -> list[dict[str, str]]:
        msgs = []
        for i in range(count):
            role = "user" if i % 2 == 0 else "assistant"
            msgs.append({"role": role, "content": f"Message {i}: {'x' * 200}"})
        return msgs

    @patch("jebat.llm.token_usage.estimate_tokens", return_value=100)
    def test_short_history_unchanged(self, mock_tokens):
        msgs = [{"role": "user", "content": "hi"}]
        result = _compact_conversation_history(msgs, max_tokens=10000)
        assert result == msgs

    @patch("jebat.llm.token_usage.estimate_tokens", return_value=100)
    def test_empty_list(self, mock_tokens):
        result = _compact_conversation_history([], max_tokens=10000)
        assert result == []

    @patch("jebat.llm.token_usage.estimate_tokens", return_value=1000)
    def test_over_budget_gets_compacted(self, mock_tokens):
        # 15 messages × 1000 tokens = 15000 total, budget 5000
        msgs = self._make_messages(15)
        result = _compact_conversation_history(msgs, max_tokens=5000)
        # Should have fewer messages than original
        assert len(result) < len(msgs)
        # First message should always be preserved
        assert result[0] == msgs[0]

    @patch("jebat.llm.token_usage.estimate_tokens", return_value=100)
    def test_under_budget_preserves_all(self, mock_tokens):
        msgs = self._make_messages(5)
        result = _compact_conversation_history(msgs, max_tokens=10000)
        assert len(result) == len(msgs)


# ═══════════════════════════════════════════════════════════════════════
# Safety Mode Approval
# ═══════════════════════════════════════════════════════════════════════


class TestShouldApproveTool:
    """Tests for _should_approve_tool (safety mode + guardrail logic)."""

    def test_dangerous_mode_approves_everything(self):
        assert _should_approve_tool("rm_rf", {"path": "/"}, SafetyMode.DANGEROUS) is True

    def test_confirm_mode_approves_everything(self):
        assert _should_approve_tool("write_file", {"path": "a.txt"}, SafetyMode.CONFIRM) is True

    def test_auto_mode_auto_tier_approved(self):
        with patch("jebat.core.agent_loop.classify_tool_call", return_value="auto"):
            assert _should_approve_tool("file_read", {"path": "a.txt"}, SafetyMode.AUTO) is True

    def test_auto_mode_confirm_tier_no_interactive(self):
        with patch("jebat.core.agent_loop.classify_tool_call", return_value="confirm"):
            assert _should_approve_tool("terminal", {"command": "ls"}, SafetyMode.AUTO) is False

    def test_auto_mode_confirm_tier_with_interactive_approves(self):
        with patch("jebat.core.agent_loop.classify_tool_call", return_value="confirm"):
            confirm = MagicMock(return_value=True)
            assert _should_approve_tool("terminal", {"command": "ls"}, SafetyMode.AUTO, confirm) is True
            confirm.assert_called_once()

    def test_auto_mode_confirm_tier_with_interactive_rejects(self):
        with patch("jebat.core.agent_loop.classify_tool_call", return_value="confirm"):
            confirm = MagicMock(return_value=False)
            assert _should_approve_tool("terminal", {"command": "ls"}, SafetyMode.AUTO, confirm) is False

    def test_auto_mode_dangerous_tier_no_interactive(self):
        with patch("jebat.core.agent_loop.classify_tool_call", return_value="dangerous"):
            assert _should_approve_tool("rm_rf", {"path": "/"}, SafetyMode.AUTO) is False


# ═══════════════════════════════════════════════════════════════════════
# Tool System Prompt Appendix
# ═══════════════════════════════════════════════════════════════════════


class TestBuildToolSystemPromptAppendix:
    """Tests for _build_tool_system_prompt_appendix."""

    def test_empty_registry_returns_empty(self):
        with patch("jebat.core.agent_loop.TOOL_REGISTRY", {}):
            result = _build_tool_system_prompt_appendix()
            assert result == ""

    def test_nonempty_registry_returns_descriptions(self):
        mock_tool = MagicMock()
        mock_tool.description = "A test tool"
        mock_tool.schema = {"properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}
        with patch("jebat.core.agent_loop.TOOL_REGISTRY", {"test_tool": mock_tool}):
            result = _build_tool_system_prompt_appendix()
            assert "test_tool" in result
            assert "A test tool" in result
            assert "cmd" in result


# ═══════════════════════════════════════════════════════════════════════
# Dataclass Construction
# ═══════════════════════════════════════════════════════════════════════


class TestToolCallStepDataclass:
    """Tests for ToolCallStep dataclass."""

    def test_construction_defaults(self):
        step = ToolCallStep(tool_name="test", params={}, result=None)
        assert step.tool_name == "test"
        assert step.params == {}
        assert step.result is None
        assert step.duration_ms == 0
        assert step.safety_tier == "auto"
        assert step.approved is True
        assert step.error is None

    def test_construction_all_fields(self):
        step = ToolCallStep(
            tool_name="terminal",
            params={"command": "ls"},
            result="file.txt",
            duration_ms=150,
            safety_tier="confirm",
            approved=True,
            error=None,
        )
        assert step.duration_ms == 150
        assert step.safety_tier == "confirm"

    def test_with_error(self):
        step = ToolCallStep(
            tool_name="bad_tool",
            params={},
            result=None,
            error="Tool not found",
        )
        assert step.error == "Tool not found"


class TestAgentResultDataclass:
    """Tests for AgentResult dataclass."""

    def test_construction_defaults(self):
        result = AgentResult(final_response="Hello!")
        assert result.final_response == "Hello!"
        assert result.tool_calls_made == []
        assert result.iterations_used == 0
        assert result.tokens_used == {}
        assert result.provider_used == ""
        assert result.error is None

    def test_construction_all_fields(self):
        result = AgentResult(
            final_response="Done",
            tool_calls_made=[],
            iterations_used=3,
            tokens_used={"prompt": 100, "completion": 50},
            provider_used="openai",
            error="timeout",
            session_id="abc123",
        )
        assert result.iterations_used == 3
        assert result.error == "timeout"
        assert result.session_id == "abc123"


class TestSafetyMode:
    """Tests for SafetyMode constants."""

    def test_constants(self):
        assert SafetyMode.AUTO == "auto"
        assert SafetyMode.CONFIRM == "confirm"
        assert SafetyMode.DANGEROUS == "dangerous"


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_max_iterations(self):
        assert MAX_ITERATIONS == 10
        assert isinstance(MAX_ITERATIONS, int)

    def test_default_max_context_tokens(self):
        assert DEFAULT_MAX_CONTEXT_TOKENS == 80_000


# ═══════════════════════════════════════════════════════════════════════
# Project Context Section
# ═══════════════════════════════════════════════════════════════════════




class TestRetryWithBackoff:
    """Tests for _retry_with_backoff (async retry with exponential backoff)."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        from jebat.core.agent_loop import _retry_with_backoff
        async def _ok(): return "ok"
        mock_fn = MagicMock(side_effect=_ok)
        result = await _retry_with_backoff(mock_fn, max_retries=3)
        assert result == "ok"
        assert mock_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_transient_error_retries_then_succeeds(self):
        from jebat.core.agent_loop import _retry_with_backoff
        mock_fn = MagicMock(side_effect=[TimeoutError("timeout"), "ok"])
        mock_fn.__name__ = "mock_fn"
        with patch("jebat.core.agent_loop.asyncio.sleep", new_callable=AsyncMock):
            result = await _retry_with_backoff(mock_fn, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert mock_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_auth_error_raises_immediately(self):
        from jebat.core.agent_loop import _retry_with_backoff
        mock_fn = MagicMock(side_effect=Exception("invalid api key"))
        mock_fn.__name__ = "mock_fn"
        with pytest.raises(Exception, match="invalid api key"):
            await _retry_with_backoff(mock_fn, max_retries=3)
        assert mock_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit_retries(self):
        from jebat.core.agent_loop import _retry_with_backoff
        mock_fn = MagicMock(side_effect=[Exception("429 too many requests"), "ok"])
        mock_fn.__name__ = "mock_fn"
        with patch("jebat.core.agent_loop.asyncio.sleep", new_callable=AsyncMock):
            result = await _retry_with_backoff(mock_fn, max_retries=3, base_delay=0.01)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_max_retries_exhausted_raises(self):
        from jebat.core.agent_loop import _retry_with_backoff
        mock_fn = MagicMock(side_effect=TimeoutError("timeout"))
        mock_fn.__name__ = "mock_fn"
        with patch("jebat.core.agent_loop.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TimeoutError):
                await _retry_with_backoff(mock_fn, max_retries=2, base_delay=0.01)
        assert mock_fn.call_count == 3

class TestBuildProjectContextSection:
    """Tests for _build_project_context_section."""

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_empty_directory_returns_empty(self, mock_git, tmp_path):
        result = _build_project_context_section(str(tmp_path))
        assert result == ""

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_agents_md_found(self, mock_git, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# Agents\nDo stuff.", encoding="utf-8")
        result = _build_project_context_section(str(tmp_path))
        assert "AGENTS.md" in result
        assert "Do stuff." in result

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_marker_files_detected(self, mock_git, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
        (tmp_path / "package.json").write_text('{"name": "test"}', encoding="utf-8")
        result = _build_project_context_section(str(tmp_path))
        assert "pyproject.toml" in result
        assert "package.json" in result

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_large_file_truncated(self, mock_git, tmp_path):
        big_content = "x" * 10000
        (tmp_path / "MEMORY.md").write_text(big_content, encoding="utf-8")
        result = _build_project_context_section(str(tmp_path))
        assert "truncated" in result

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_multiple_context_files(self, mock_git, tmp_path):
        (tmp_path / "AGENTS.md").write_text("agents", encoding="utf-8")
        (tmp_path / "MEMORY.md").write_text("memory", encoding="utf-8")
        (tmp_path / "DESIGN.md").write_text("design", encoding="utf-8")
        result = _build_project_context_section(str(tmp_path))
        assert "AGENTS.md" in result
        assert "MEMORY.md" in result
        assert "DESIGN.md" in result

    @patch("jebat.core.agent_loop._get_git_context", return_value=None)
    def test_project_root_in_output(self, mock_git, tmp_path):
        (tmp_path / "README.md").write_text("# readme", encoding="utf-8")
        result = _build_project_context_section(str(tmp_path))
        assert str(tmp_path) in result
