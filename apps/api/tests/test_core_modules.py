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


if __name__ == "__main__":
    unittest.main()
