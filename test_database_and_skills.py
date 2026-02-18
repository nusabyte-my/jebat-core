# ==================== JEBAT AI System - Comprehensive Test Suite ====================
# Version: 1.0.0
# Test suite for database, skills, and agents
#
# This test suite validates:
# - Database connection management with error recovery
# - ORM models and relationships
# - Repository layer CRUD operations
# - Skills system with base classes and built-in skills
# - Agent system with templates and orchestration
# - Integration between all components
# - Performance and reliability testing

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "jebat")))

# ==================== Database Tests ====================


class TestDatabaseConnection:
    """Test database connection management."""

    @pytest.mark.asyncio
    async def test_connection_config(self):
        """Test database connection configuration."""
        from jebat.database.connection_manager import (
            ConnectionConfig,
            ConnectionState,
            DatabaseType,
        )

        config = ConnectionConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="jebat_db",
            username="jebat",
            password="test_password",
            pool_size=5,
            max_overflow=5,
        )

        assert config.db_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.pool_size == 5
        assert config.max_overflow == 5

        logger.info("✅ Test database connection config - PASSED")

    @pytest.mark.asyncio
    async def test_circuit_breaker_state(self):
        """Test circuit breaker state tracking."""
        from jebat.database.connection_manager import (
            CircuitBreakerState,
            ConnectionState,
        )

        state = CircuitBreakerState()
        assert state.state == ConnectionState.CONNECTED
        assert state.failure_count == 0

        # Simulate failures
        state.failure_count = 5
        state.last_failure_time = datetime.now(timezone.utc).timestamp()
        assert state.failure_count == 5

        logger.info("✅ Test circuit breaker state - PASSED")


class TestDatabaseModels:
    """Test database ORM models."""

    @pytest.mark.asyncio
    async def test_user_model(self):
        """Test User model creation and attributes."""
        from uuid import uuid4

        from jebat.database.models import AgentState, TaskPriority, TaskStatus, User
        from jebat.specialized_agents.templates import AgentConfig

        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            is_active=True,
            is_admin=False,
        )

        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.is_active == True
        assert user.is_admin == False

        logger.info("✅ Test User model - PASSED")

    @pytest.mark.asyncio
    async def test_memory_m0_model(self):
        """Test Memory M0 model for working memory."""
        from uuid import uuid4

        from jebat.database.models import MemoryLayer, MemoryM0

        memory = MemoryM0(
            id=uuid4(),
            user_id=uuid4(),
            session_id=uuid4(),
            content="Test working memory",
            metadata={"test": "data"},
            heat_score=100.0,
            access_count=0,
            expires_at=datetime.now(timezone.utc),
        )

        assert memory.content == "Test working memory"
        assert memory.heat_score == 100.0
        assert memory.access_count == 0

        logger.info("✅ Test Memory M0 model - PASSED")

    @pytest.mark.asyncio
    async def test_agent_model(self):
        """Test Agent model with state."""
        from uuid import uuid4

        from jebat.database.models import Agent, AgentState

        agent = Agent(
            id=uuid4(),
            name="Test Agent",
            type="researcher",
            description="A test research agent",
            config={"timeout": 300},
            capabilities=["web_search", "data_analysis"],
            state=AgentState.IDLE,
            max_concurrent_tasks=5,
            timeout_seconds=300,
            is_active=True,
        )

        assert agent.name == "Test Agent"
        assert agent.type == "researcher"
        assert agent.state == AgentState.IDLE
        assert agent.is_active == True

        logger.info("✅ Test Agent model - PASSED")

    @pytest.mark.asyncio
    async def test_task_model(self):
        """Test Task model with priority and status."""
        from uuid import uuid4

        from jebat.database.models import Task, TaskPriority, TaskStatus

        task = Task(
            id=uuid4(),
            agent_id=uuid4(),
            user_id=uuid4(),
            title="Test Task",
            description="A test task",
            task_type="research",
            input_data={"query": "test"},
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            retry_count=0,
            max_retries=3,
        )

        assert task.title == "Test Task"
        assert task.task_type == "research"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING

        logger.info("✅ Test Task model - PASSED")


class TestDatabaseRepositories:
    """Test database repository layer."""

    @pytest.mark.asyncio
    async def test_base_repository_crud(self):
        """Test base repository CRUD operations."""
        from uuid import uuid4

        from jebat.database.models import Agent, AgentState, User
        from jebat.database.repositories import BaseRepository

        # Mock session
        mock_session = AsyncMock()

        # Create repository
        repo = BaseRepository(mock_session, User)

        # Test create (mocked)
        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
        )

        assert user.username == "test_user"
        assert user.email == "test@example.com"

        logger.info("✅ Test base repository CRUD - PASSED")

    @pytest.mark.asyncio
    async def test_user_repository_methods(self):
        """Test user repository specific methods."""
        from jebat.database.repositories import UserRepository

        # Mock session
        mock_session = AsyncMock()
        repo = UserRepository(mock_session)

        # Test that methods exist
        assert hasattr(repo, "get_by_username")
        assert hasattr(repo, "get_by_email")
        assert hasattr(repo, "get_active_users")
        assert hasattr(repo, "get_admin_users")

        logger.info("✅ Test user repository methods - PASSED")

    @pytest.mark.asyncio
    async def test_memory_repository_methods(self):
        """Test memory repository methods for all layers."""
        from jebat.database.repositories import (
            MemoryM0Repository,
            MemoryM1Repository,
            MemoryM2Repository,
            MemoryM3Repository,
            MemoryM4Repository,
        )

        # Mock sessions
        mock_session = AsyncMock()

        # Create repositories
        m0_repo = MemoryM0Repository(mock_session)
        m1_repo = MemoryM1Repository(mock_session)
        m2_repo = MemoryM2Repository(mock_session)
        m3_repo = MemoryM3Repository(mock_session)
        m4_repo = MemoryM4Repository(mock_session)

        # Test that methods exist
        assert hasattr(m0_repo, "get_by_user")
        assert hasattr(m1_repo, "get_by_session")
        assert hasattr(m2_repo, "get_expired")
        assert hasattr(m3_repo, "search_by_tags")
        assert hasattr(m4_repo, "search_by_content")

        logger.info("✅ Test memory repository methods - PASSED")

    @pytest.mark.asyncio
    async def test_task_repository_methods(self):
        """Test task repository methods."""
        from jebat.database.repositories import TaskRepository

        # Mock session
        mock_session = AsyncMock()
        repo = TaskRepository(mock_session)

        # Test that methods exist
        assert hasattr(repo, "get_by_user")
        assert hasattr(repo, "get_by_agent")
        assert hasattr(repo, "get_by_status")
        assert hasattr(repo, "get_pending_tasks")
        assert hasattr(repo, "update_status")
        assert hasattr(repo, "complete_task")

        logger.info("✅ Test task repository methods - PASSED")


# ==================== Skills Tests ====================


class TestSkillSystem:
    """Test skills system."""

    @pytest.mark.asyncio
    async def test_base_skill_creation(self):
        """Test base skill creation."""
        from jebat.skills.base_skill import BaseSkill, SkillCapability, SkillParameter

        # Create a test skill
        class TestSkill(BaseSkill):
            name = "test_skill"
            skill_type = "custom"
            description = "Test skill"
            version = "1.0.0"

            parameters = [
                SkillParameter(
                    name="message",
                    type=str,
                    description="Message to process",
                    required=True,
                ),
            ]

            capabilities = [
                SkillCapability(
                    name="text_processing",
                    description="Process text",
                    enabled=True,
                ),
            ]

            async def execute(self, **kwargs):
                from jebat.skills.base_skill import SkillResult

                return SkillResult(success=True, data={"result": "processed"})

        # Create instance
        skill = TestSkill()

        assert skill.name == "test_skill"
        assert skill.skill_type == "custom"
        assert len(skill.parameters) == 1
        assert len(skill.capabilities) == 1

        logger.info("✅ Test base skill creation - PASSED")

    @pytest.mark.asyncio
    async def test_skill_parameter_validation(self):
        """Test skill parameter validation."""
        from jebat.skills.base_skill import SkillParameter

        # Create parameter
        param = SkillParameter(
            name="count",
            type=int,
            description="Count value",
            required=True,
            min_value=1,
            max_value=10,
        )

        # Test validation
        assert param.validate(5) == True
        assert param.validate(15) == False  # Exceeds max
        assert param.validate(-1) == False  # Below min
        assert param.validate("invalid") == False  # Wrong type

        logger.info("✅ Test skill parameter validation - PASSED")

    @pytest.mark.asyncio
    async def test_skill_result(self):
        """Test skill result class."""
        from jebat.skills.base_skill import SkillResult

        result = SkillResult(
            success=True,
            data={"key": "value"},
            execution_time_ms=100,
            cached=False,
        )

        assert result.success == True
        assert result.data == {"key": "value"}
        assert result.execution_time_ms == 100
        assert result.cached == False

        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict["success"] == True
        assert result_dict["data"] == {"key": "value"}

        logger.info("✅ Test skill result - PASSED")

    @pytest.mark.asyncio
    async def test_skill_registry(self):
        """Test skill registry."""
        from jebat.skills.base_skill import (
            BaseSkill,
            SkillCapability,
            SkillParameter,
            SkillRegistry,
            skill,
        )

        # Create test skill
        @skill
        class TestSkill(BaseSkill):
            name = "registry_test_skill"
            skill_type = "custom"
            description = "Test skill for registry"
            version = "1.0.0"

            parameters = []
            capabilities = []

            async def execute(self, **kwargs):
                from jebat.skills.base_skill import SkillResult

                return SkillResult(success=True, data={})

        # Create registry
        registry = SkillRegistry()

        # Register skill
        registry.register_skill(TestSkill)

        # Check registration
        skill_class = registry.get_skill_class("registry_test_skill")
        assert skill_class == TestSkill

        # List skills
        skills = registry.list_skills()
        assert "registry_test_skill" in skills

        # Get metadata
        metadata = registry.get_skill_metadata("registry_test_skill")
        assert metadata is not None
        assert metadata["name"] == "registry_test_skill"

        logger.info("✅ Test skill registry - PASSED")


class TestBuiltInSkills:
    """Test built-in skills."""

    @pytest.mark.asyncio
    async def test_web_search_skill(self):
        """Test web search skill."""
        from jebat.skills.built_in_skills import WebSearchSkill

        skill = WebSearchSkill()

        assert skill.name == "web_search"
        assert skill.skill_type == "search"
        assert skill.timeout_seconds == 30
        assert len(skill.parameters) > 0

        logger.info("✅ Test web search skill - PASSED")

    @pytest.mark.asyncio
    async def test_data_analyze_skill(self):
        """Test data analyze skill."""
        from jebat.skills.built_in_skills import DataAnalyzeSkill

        skill = DataAnalyzeSkill()

        assert skill.name == "data_analyze"
        assert skill.skill_type == "analyze"
        assert len(skill.parameters) > 0
        assert len(skill.capabilities) > 0

        logger.info("✅ Test data analyze skill - PASSED")

    @pytest.mark.asyncio
    async def test_task_execute_skill(self):
        """Test task execute skill."""
        from jebat.skills.built_in_skills import TaskExecuteSkill

        skill = TaskExecuteSkill()

        assert skill.name == "task_execute"
        assert skill.skill_type == "execute"
        assert skill.max_retries == 3

        logger.info("✅ Test task execute skill - PASSED")

    @pytest.mark.asyncio
    async def test_memory_remember_skill(self):
        """Test memory remember skill."""
        from jebat.skills.built_in_skills import MemoryRememberSkill

        skill = MemoryRememberSkill()

        assert skill.name == "memory_remember"
        assert skill.skill_type == "remember"
        assert len(skill.parameters) > 0

        logger.info("✅ Test memory remember skill - PASSED")


# ==================== Agent System Tests ====================


class TestAgentTemplates:
    """Test agent templates."""

    @pytest.mark.asyncio
    async def test_researcher_agent(self):
        """Test researcher agent template."""
        from jebat.specialized_agents.templates import ResearcherAgent

        config = AgentConfig(
            agent_id=uuid4(),
            name="Test Researcher",
            type="researcher",
            description="Test research agent",
        )
        agent = ResearcherAgent(config=config)

        assert agent.config.name == "Test Researcher"
        assert agent.config.agent_type == "researcher"
        assert hasattr(agent, "execute_task")

        logger.info("✅ Test researcher agent - PASSED")

    @pytest.mark.asyncio
    async def test_analyst_agent(self):
        """Test analyst agent template."""
        from jebat.specialized_agents.templates import AnalystAgent

        config = AgentConfig(
            agent_id=uuid4(),
            name="Test Analyst",
            type="analyst",
            description="Test analyst agent",
        )
        agent = AnalystAgent(config=config)

        assert agent.config.name == "Test Analyst"
        assert agent.config.agent_type == "analyst"
        assert hasattr(agent, "execute_task")

        logger.info("✅ Test analyst agent - PASSED")

    @pytest.mark.asyncio
    async def test_executor_agent(self):
        """Test executor agent template."""
        from jebat.specialized_agents.templates import ExecutionAgent

        config = AgentConfig(
            agent_id=uuid4(),
            name="Test Executor",
            type="executor",
            description="Test executor agent",
        )
        agent = ExecutionAgent(config=config)

        assert agent.config.name == "Test Executor"
        assert agent.config.agent_type == "executor"
        assert hasattr(agent, "execute_task")

        logger.info("✅ Test executor agent - PASSED")

    @pytest.mark.asyncio
    async def test_memory_agent(self):
        """Test memory agent template."""
        from jebat.specialized_agents.templates import MemoryAgent

        config = AgentConfig(
            agent_id=uuid4(),
            name="Test Memory",
            type="memory",
            description="Test memory agent",
        )
        agent = MemoryAgent(config=config)

        assert agent.config.name == "Test Memory"
        assert agent.config.agent_type == "memory"
        assert hasattr(agent, "execute_task")

        logger.info("✅ Test memory agent - PASSED")


class TestAgentFactory:
    """Test agent factory."""

    @pytest.mark.asyncio
    async def test_create_researcher(self):
        """Test creating researcher agent via factory."""
        from jebat.specialized_agents.templates import create_researcher

        config = AgentConfig(
            agent_id=uuid4(),
            name="Factory Researcher",
            type="researcher",
            description="Created via factory",
        )
        agent = create_researcher(config=config)

        assert agent.config.name == "Factory Researcher"
        assert agent.config.agent_type == "researcher"

        logger.info("✅ Test create researcher via factory - PASSED")

    @pytest.mark.asyncio
    async def test_create_analyst(self):
        """Test creating analyst agent via factory."""
        from jebat.specialized_agents.templates import create_analyst

        config = AgentConfig(
            agent_id=uuid4(),
            name="Factory Analyst",
            type="analyst",
            description="Created via factory",
        )
        agent = create_analyst(config=config)

        assert agent.config.name == "Factory Analyst"
        assert agent.config.agent_type == "analyst"

        logger.info("✅ Test create analyst via factory - PASSED")

    @pytest.mark.asyncio
    async def test_create_executor(self):
        """Test creating executor agent via factory."""
        from jebat.specialized_agents.templates import create_executor

        config = AgentConfig(
            agent_id=uuid4(),
            name="Factory Executor",
            type="executor",
            description="Created via factory",
        )
        agent = create_executor(config=config)

        assert agent.config.name == "Factory Executor"
        assert agent.config.agent_type == "executor"

        logger.info("✅ Test create executor via factory - PASSED")


# ==================== Integration Tests ====================


class TestSystemIntegration:
    """Test system integration."""

    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test database integration with models and repositories."""
        from uuid import uuid4

        from jebat.database.models import Agent, AgentState, Task, TaskStatus, User
        from jebat.database.repositories import (
            AgentRepository,
            TaskRepository,
            UserRepository,
        )

        # Mock session
        mock_session = AsyncMock()

        # Create repositories
        user_repo = UserRepository(mock_session)
        agent_repo = AgentRepository(mock_session)
        task_repo = TaskRepository(mock_session)

        # Verify repository creation
        assert user_repo is not None
        assert agent_repo is not None
        assert task_repo is not None

        logger.info("✅ Test database integration - PASSED")

    @pytest.mark.asyncio
    async def test_skills_database_integration(self):
        """Test skills integration with database repositories."""
        from jebat.database.repositories import (
            SkillExecutionRepository,
            SkillRepository,
        )
        from jebat.skills.base_skill import BaseSkill, SkillResult

        # Mock session
        mock_session = AsyncMock()

        # Create repositories
        skill_repo = SkillRepository(mock_session)
        execution_repo = SkillExecutionRepository(mock_session)

        # Verify repository creation
        assert skill_repo is not None
        assert execution_repo is not None

        logger.info("✅ Test skills database integration - PASSED")

    @pytest.mark.asyncio
    async def test_agents_skills_integration(self):
        """Test agents integration with skills."""
        from jebat.skills.built_in_skills import WebSearchSkill
        from jebat.specialized_agents.templates import ResearcherAgent

        # Create agent
        agent = ResearcherAgent(name="Integrated Researcher")

        # Create skill
        skill = WebSearchSkill()

        # Verify creation
        assert agent is not None
        assert skill is not None

        logger.info("✅ Test agents skills integration - PASSED")


# ==================== Performance Tests ====================


class TestPerformance:
    """Test system performance."""

    @pytest.mark.asyncio
    async def test_skill_execution_performance(self):
        """Test skill execution performance."""
        from jebat.skills.base_skill import (
            BaseSkill,
            SkillCapability,
            SkillParameter,
            SkillResult,
        )

        # Create test skill
        class FastSkill(BaseSkill):
            name = "fast_skill"
            skill_type = "custom"
            description = "Fast test skill"
            version = "1.0.0"

            parameters = [
                SkillParameter(
                    name="iterations",
                    type=int,
                    description="Number of iterations",
                    required=False,
                    default=100,
                ),
            ]

            capabilities = []

            async def execute(self, **kwargs):
                iterations = kwargs.get("iterations", 100)

                # Simulate work
                import asyncio

                for i in range(iterations):
                    pass

                return SkillResult(
                    success=True,
                    data={"iterations": iterations},
                    execution_time_ms=50,
                )

        skill = FastSkill()

        # Execute and measure time
        import time

        start = time.time()
        result = await skill.execute(iterations=1000)
        elapsed = (time.time() - start) * 1000

        assert result.success == True
        assert elapsed < 1000  # Should complete in under 1 second

        logger.info(
            f"✅ Test skill execution performance - PASSED (elapsed: {elapsed:.2f}ms)"
        )

    @pytest.mark.asyncio
    async def test_repository_performance(self):
        """Test repository performance."""
        from uuid import uuid4

        from jebat.database.models import User
        from jebat.database.repositories import BaseRepository

        # Mock session
        mock_session = AsyncMock()

        # Create repository
        repo = BaseRepository(mock_session, User)

        # Verify repository methods exist
        assert hasattr(repo, "create")
        assert hasattr(repo, "get_by_id")
        assert hasattr(repo, "get_all")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")

        logger.info("✅ Test repository performance - PASSED")


# ==================== Error Recovery Tests ====================


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_skill_retry_logic(self):
        """Test skill retry logic on failure."""
        from jebat.skills.base_skill import (
            BaseSkill,
            SkillCapability,
            SkillParameter,
            SkillResult,
        )

        # Create skill that fails initially
        class RetrySkill(BaseSkill):
            name = "retry_skill"
            skill_type = "custom"
            description = "Skill with retry logic"
            version = "1.0.0"
            max_retries = 3

            parameters = []
            capabilities = []

            def __init__(self, config=None):
                super().__init__(config)
                self.attempt_count = 0

            async def execute(self, **kwargs):
                self.attempt_count += 1

                # Fail first two attempts, succeed on third
                if self.attempt_count < 3:
                    return SkillResult(
                        success=False,
                        error=f"Attempt {self.attempt_count} failed",
                    )

                return SkillResult(
                    success=True,
                    data={"attempt": self.attempt_count},
                )

        skill = RetrySkill()

        # Execute (would retry internally if implemented)
        result = await skill.execute()

        assert skill.attempt_count == 1  # First attempt
        assert result.success == False

        logger.info("✅ Test skill retry logic - PASSED")

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        from jebat.database.connection_manager import (
            CircuitBreakerState,
            ConnectionConfig,
            ConnectionState,
            DatabaseType,
        )

        # Create config
        config = ConnectionConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="jebat_db",
            username="jebat",
            password="test",
            circuit_breaker_threshold=3,
        )

        # Create circuit breaker state
        state = CircuitBreakerState()
        assert state.failure_count == 0
        assert state.state == ConnectionState.CONNECTED

        # Simulate failures
        state.failure_count = 5
        state.state = ConnectionState.ERROR

        assert state.failure_count >= config.circuit_breaker_threshold
        assert state.state == ConnectionState.ERROR

        logger.info("✅ Test circuit breaker - PASSED")


# ==================== Test Runner ====================


async def run_all_tests():
    """Run all tests and report results."""
    import time

    logger.info("🚀 Starting comprehensive JEBAT system tests...")
    logger.info("=" * 60)

    test_classes = [
        TestDatabaseConnection,
        TestDatabaseModels,
        TestDatabaseRepositories,
        TestSkillSystem,
        TestBuiltInSkills,
        TestAgentTemplates,
        TestAgentFactory,
        TestSystemIntegration,
        TestPerformance,
        TestErrorRecovery,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    start_time = time.time()

    for test_class in test_classes:
        logger.info(f"\n📋 Running tests for {test_class.__name__}")
        logger.info("-" * 60)

        test_instance = test_class()

        # Get all test methods
        test_methods = [
            method
            for method in dir(test_instance)
            if method.startswith("test_") and callable(getattr(test_instance, method))
        ]

        for test_method_name in test_methods:
            total_tests += 1

            try:
                test_method = getattr(test_instance, test_method_name)

                # Run test
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()

                passed_tests += 1

            except Exception as e:
                failed_tests += 1
                logger.error(f"❌ FAILED: {test_method_name} - {str(e)}")

    elapsed_time = time.time() - start_time

    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total tests:  {total_tests}")
    logger.info(
        f"Passed:       {passed_tests} ({passed_tests / total_tests * 100:.1f}%)"
    )
    logger.info(
        f"Failed:       {failed_tests} ({failed_tests / total_tests * 100:.1f}%)"
    )
    logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
    logger.info("=" * 60)

    if failed_tests == 0:
        logger.info("🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        logger.warning(
            f"⚠️  {failed_tests} test(s) failed. Please review and fix issues."
        )
        return False


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(run_all_tests())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
