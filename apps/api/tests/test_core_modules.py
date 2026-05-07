"""
Tests for JEBAT core modules — import health, basic instantiation, and config.

These tests verify that the refactored import system works and core
classes can be instantiated without external services.
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class TestImportHealth(unittest.TestCase):
    """Verify all core packages import without errors."""

    def test_import_core_memory(self):
        from apps.api.core.memory import MemoryManager, MemoryLayer, Memory
        self.assertIsNotNone(MemoryManager)
        self.assertIsNotNone(MemoryLayer)
        self.assertIsNotNone(Memory)

    def test_import_core_agents(self):
        from apps.api.core.agents import AgentFactory, AgentOrchestrator
        self.assertIsNotNone(AgentFactory)
        self.assertIsNotNone(AgentOrchestrator)

    def test_import_core_cache(self):
        from apps.api.core.cache import CacheManager, SmartCache
        self.assertIsNotNone(CacheManager)
        self.assertIsNotNone(SmartCache)

    def test_import_core_decision(self):
        from apps.api.core.decision import DecisionEngine
        self.assertIsNotNone(DecisionEngine)

    def test_import_features_ultra_think(self):
        from apps.api.features.ultra_think import UltraThink, ThinkingMode, create_ultra_think
        self.assertIsNotNone(UltraThink)
        self.assertIsNotNone(ThinkingMode)
        self.assertIsNotNone(create_ultra_think)

    def test_import_features_ultra_loop(self):
        from apps.api.features.ultra_loop import UltraLoop, create_ultra_loop
        self.assertIsNotNone(UltraLoop)
        self.assertIsNotNone(create_ultra_loop)

    def test_import_llm(self):
        from apps.api.llm import load_llm_config
        self.assertIsNotNone(load_llm_config)

    def test_import_monitoring(self):
        from apps.api.monitoring import MetricsCollector, DashboardAPI
        self.assertIsNotNone(MetricsCollector)
        self.assertIsNotNone(DashboardAPI)

    def test_import_orchestration(self):
        from apps.api.orchestration import WorkflowEngine
        self.assertIsNotNone(WorkflowEngine)

    def test_import_analytics(self):
        from apps.api.analytics import AnalyticsEngine
        self.assertIsNotNone(AnalyticsEngine)

    def test_import_mcp(self):
        from apps.api.mcp import Skill, SkillRegistry
        self.assertIsNotNone(Skill)
        self.assertIsNotNone(SkillRegistry)

    def test_import_integrations_channels(self):
        from apps.api.integrations.channels import ChannelManager
        self.assertIsNotNone(ChannelManager)

    def test_import_database_safe(self):
        """Database package should import even without sqlalchemy/asyncpg."""
        import apps.api.database as db
        # Should not crash — gracefully degrades
        self.assertIsNotNone(db)

    def test_import_root_package(self):
        import apps.api as jebat
        self.assertEqual(jebat.__version__, "2.0.0")


class TestConfig(unittest.TestCase):
    """Test the configuration system."""

    def test_settings_defaults(self):
        from apps.api.config import settings
        self.assertEqual(settings.version, "2.0.0")
        self.assertIsInstance(settings.api.port, int)
        self.assertIsInstance(settings.webui.port, int)

    def test_settings_env_override(self):
        with mock.patch.dict(os.environ, {"JEBAT_API_PORT": "9999"}):
            from apps.api.config import Settings
            s = Settings()
            self.assertEqual(s.api.port, 9999)

    def test_llm_config_defaults(self):
        from apps.api.llm.config import load_llm_config
        config = load_llm_config()
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.model, "llama3.2")
        self.assertIsInstance(config.temperature, float)
        self.assertIsInstance(config.max_tokens, int)

    def test_llm_config_env_override(self):
        with mock.patch.dict(os.environ, {
            "JEBAT_LLM_PROVIDER": "openai",
            "JEBAT_LLM_MODEL": "gpt-4o",
        }):
            from apps.api.llm.config import load_llm_config
            config = load_llm_config()
            self.assertEqual(config.provider, "openai")
            self.assertEqual(config.model, "gpt-4o")


class TestCoreInstantiation(unittest.TestCase):
    """Test that core classes can be instantiated."""

    def test_memory_manager(self):
        from apps.api.core.memory import MemoryManager
        mm = MemoryManager()
        self.assertIsNotNone(mm)

    def test_agent_factory(self):
        from apps.api.core.agents import AgentFactory
        af = AgentFactory()
        self.assertIsNotNone(af)

    def test_cache_manager(self):
        from apps.api.core.cache import CacheManager
        cm = CacheManager()
        self.assertIsNotNone(cm)

    def test_decision_engine(self):
        from apps.api.core.decision import DecisionEngine
        de = DecisionEngine()
        self.assertIsNotNone(de)

    def test_metrics_collector(self):
        from apps.api.monitoring import MetricsCollector
        mc = MetricsCollector()
        self.assertIsNotNone(mc)

    def test_analytics_engine(self):
        from apps.api.analytics import AnalyticsEngine
        ae = AnalyticsEngine()
        self.assertIsNotNone(ae)


class TestUltraThink(unittest.IsolatedAsyncioTestCase):
    """Test Ultra-Think basic functionality."""

    async def test_create_ultra_think(self):
        from apps.api.features.ultra_think import create_ultra_think, ThinkingMode
        thinker = await create_ultra_think(config={"max_thoughts": 5})
        self.assertIsNotNone(thinker)

    async def test_thinking_modes(self):
        from apps.api.features.ultra_think import ThinkingMode
        modes = [m.value for m in ThinkingMode]
        self.assertIn("fast", modes)
        self.assertIn("deliberate", modes)
        self.assertIn("deep", modes)


class TestUltraLoop(unittest.IsolatedAsyncioTestCase):
    """Test Ultra-Loop basic functionality."""

    async def test_create_ultra_loop(self):
        from apps.api.features.ultra_loop import create_ultra_loop
        loop = await create_ultra_loop(
            config={"cycle_interval": 1.0, "max_cycles": 0},
            enable_db_persistence=False,
        )
        self.assertIsNotNone(loop)

    async def test_loop_phases(self):
        from apps.api.features.ultra_loop import LoopPhase
        phases = [p.value for p in LoopPhase]
        self.assertIn("perception", phases)
        self.assertIn("cognition", phases)


class TestDatabaseSafety(unittest.IsolatedAsyncioTestCase):
    """Test database layer degrades gracefully."""

    async def test_health_check_without_deps(self):
        from apps.api.database import check_database_health
        result = await check_database_health()
        self.assertIn("healthy", result)
        self.assertIn("error", result)


class TestWebSkills(unittest.IsolatedAsyncioTestCase):
    """Test webfetch/websearch skills."""

    def test_web_skills_import(self):
        from apps.api.skills import WebFetchSkill, WebSearchSkill
        self.assertEqual(WebFetchSkill.name, "web_fetch")
        self.assertEqual(WebSearchSkill.name, "web_search")

    async def test_web_fetch_rejects_invalid_scheme(self):
        from apps.api.skills import WebFetchSkill
        skill = WebFetchSkill()
        result = await skill.execute(url="file:///etc/passwd")
        self.assertFalse(result.success)
        self.assertIn("Invalid URL scheme", result.error)

    async def test_web_fetch_rejects_missing_host(self):
        from apps.api.skills import WebFetchSkill
        skill = WebFetchSkill()
        result = await skill.execute(url="https://")
        self.assertFalse(result.success)
        self.assertIn("no host", result.error)

    async def test_web_search_rejects_empty_query(self):
        from apps.api.skills import WebSearchSkill
        skill = WebSearchSkill()
        result = await skill.execute(query="")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Empty query")




class TestChatHistory(unittest.TestCase):
    """Test chat history persistence."""

    def test_chat_history_append_and_load(self):
        import tempfile
        from pathlib import Path
        from apps.api.llm.history import ChatHistoryStore

        with tempfile.TemporaryDirectory() as td:
            history_path = Path(td) / "chat_history.jsonl"
            store = ChatHistoryStore(history_path)

            store.append("session-a", "user", "hello")
            store.append("session-a", "assistant", "hi there")
            store.append("session-b", "user", "other session")

            rows = store.load("session-a", limit=10)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].role, "user")
            self.assertEqual(rows[0].content, "hello")
            self.assertEqual(rows[1].role, "assistant")
            self.assertEqual(rows[1].content, "hi there")

    def test_chat_history_limit(self):
        import tempfile
        from pathlib import Path
        from apps.api.llm.history import ChatHistoryStore

        with tempfile.TemporaryDirectory() as td:
            history_path = Path(td) / "chat_history.jsonl"
            store = ChatHistoryStore(history_path)

            for i in range(6):
                store.append("session-limit", "user", f"msg-{i}")

            rows = store.load("session-limit", limit=3)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].content, "msg-3")
            self.assertEqual(rows[1].content, "msg-4")
            self.assertEqual(rows[2].content, "msg-5")


class TestMCPServer(unittest.TestCase):
    """Test MCP server import safety."""

    def test_mcp_server_imports_without_deps(self):
        """MCP server module should import even without mcp/jebat_dev."""
        import apps.api.mcp.server as mcp_server
        self.assertIsNotNone(mcp_server.JEBATMCPServer)

    def test_mcp_skill_registry_import(self):
        from apps.api.mcp import Skill, SkillRegistry
        self.assertIsNotNone(Skill)
        self.assertIsNotNone(SkillRegistry)

    def test_services_package_imports_without_fastapi(self):
        """Services package should import lazily without fastapi."""
        import apps.api.services as svc
        self.assertIsNotNone(svc)

    def test_protocol_server_registers_web_tools(self):
        from apps.api.services.mcp import MCPProtocolServer
        srv = MCPProtocolServer()
        self.assertIn("web.search", srv.tools)
        self.assertIn("web.fetch", srv.tools)
        status = srv.get_status()
        self.assertIn("web.search", status["tools"])
        self.assertIn("web.fetch", status["tools"])


class TestNativeToolSupport(unittest.TestCase):
    """Test native tool-calling provider support."""

    def test_supports_native_tools(self):
        from apps.api.llm.providers import supports_native_tools
        self.assertTrue(supports_native_tools("openrouter"))
        self.assertTrue(supports_native_tools("ollama"))
        self.assertTrue(supports_native_tools("anthropic"))
        self.assertFalse(supports_native_tools("openai"))
        self.assertFalse(supports_native_tools("google"))
        self.assertFalse(supports_native_tools("local"))

    def test_openai_schema_has_function_type(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        schema = reg.to_openai_schema()
        for entry in schema:
            self.assertEqual(entry["type"], "function")
            self.assertIn("name", entry["function"])

    def test_anthropic_schema_has_input_schema(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        schema = reg.to_anthropic_schema()
        for entry in schema:
            self.assertIn("input_schema", entry)
            self.assertNotIn("type", entry)  # Anthropic doesn't wrap in {type: function}

    def test_native_tool_providers_constant(self):
        from apps.api.llm.providers import NATIVE_TOOL_PROVIDERS
        self.assertIsInstance(NATIVE_TOOL_PROVIDERS, frozenset)
        self.assertIn("ollama", NATIVE_TOOL_PROVIDERS)


class TestToolCalling(unittest.IsolatedAsyncioTestCase):
    """Test LLM tool-calling mechanism."""

    def test_tool_registry_import(self):
        from apps.api.llm.tools import ToolRegistry, ToolDefinition
        self.assertIsNotNone(ToolRegistry)
        self.assertIsNotNone(ToolDefinition)

    def test_register_defaults(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        names = [t.name for t in reg.list_tools()]
        self.assertIn("web_search", names)
        self.assertIn("web_fetch", names)

    def test_openai_schema_shape(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        schema = reg.to_openai_schema()
        self.assertIsInstance(schema, list)
        self.assertTrue(len(schema) >= 2)
        for entry in schema:
            self.assertEqual(entry["type"], "function")
            self.assertIn("function", entry)
            func = entry["function"]
            self.assertIn("name", func)
            self.assertIn("description", func)
            self.assertIn("parameters", func)

    def test_anthropic_schema_shape(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        schema = reg.to_anthropic_schema()
        self.assertIsInstance(schema, list)
        self.assertTrue(len(schema) >= 2)
        for entry in schema:
            self.assertIn("name", entry)
            self.assertIn("description", entry)
            self.assertIn("input_schema", entry)

    def test_ollama_schema_matches_openai(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        self.assertEqual(reg.to_ollama_schema(), reg.to_openai_schema())

    def test_prompt_block_contains_tools(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        reg.register_defaults()
        block = reg.prompt_block()
        self.assertIn("web_search", block)
        self.assertIn("web_fetch", block)
        self.assertIn('"tool"', block)

    def test_prompt_block_empty_registry(self):
        from apps.api.llm.tools import ToolRegistry
        reg = ToolRegistry()
        self.assertEqual(reg.prompt_block(), "")

    def test_parse_tool_call_valid(self):
        from apps.api.llm.tools import parse_tool_call
        result = parse_tool_call('{"tool": "web_search", "arguments": {"query": "hello"}}')
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "web_search")
        self.assertEqual(args["query"], "hello")

    def test_parse_tool_call_with_markdown(self):
        from apps.api.llm.tools import parse_tool_call
        text = '```json\n{"tool": "web_fetch", "arguments": {"url": "https://example.com"}}\n```'
        result = parse_tool_call(text)
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "web_fetch")
        self.assertEqual(args["url"], "https://example.com")

    def test_parse_tool_call_plain_text(self):
        from apps.api.llm.tools import parse_tool_call
        result = parse_tool_call("I don't need any tools for this question.")
        self.assertIsNone(result)

    def test_parse_tool_call_invalid_json(self):
        from apps.api.llm.tools import parse_tool_call
        result = parse_tool_call('{"tool": "web_search", "arguments": {broken}')
        self.assertIsNone(result)

    async def test_execute_unknown_tool(self):
        from apps.api.llm.tools import ToolRegistry, execute_tool_call
        reg = ToolRegistry()
        result = await execute_tool_call(reg, "nonexistent_tool", {"x": 1})
        self.assertEqual(result.tool_name, "nonexistent_tool")
        self.assertIn("Unknown tool", result.error)
        self.assertEqual(result.result, "")

    async def test_execute_tool_handler_error(self):
        from apps.api.llm.tools import ToolRegistry, ToolDefinition, execute_tool_call

        async def bad_handler(**kwargs):
            raise ValueError("intentional test error")

        reg = ToolRegistry()
        reg.register(ToolDefinition(
            name="bad_tool",
            description="A tool that always fails",
            parameters={"type": "object", "properties": {}},
            handler=bad_handler,
        ))
        result = await execute_tool_call(reg, "bad_tool", {})
        self.assertIn("intentional test error", result.error)
        self.assertEqual(result.result, "")

    async def test_execute_tool_success(self):
        from apps.api.llm.tools import ToolRegistry, ToolDefinition, execute_tool_call

        async def echo_handler(**kwargs):
            return f"echo: {kwargs.get('msg', '')}"

        reg = ToolRegistry()
        reg.register(ToolDefinition(
            name="echo",
            description="Echoes input",
            parameters={"type": "object", "properties": {"msg": {"type": "string"}}},
            handler=echo_handler,
        ))
        result = await execute_tool_call(reg, "echo", {"msg": "hello"})
        self.assertEqual(result.result, "echo: hello")
        self.assertEqual(result.error, "")


if __name__ == "__main__":
    unittest.main()
