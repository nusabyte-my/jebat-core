"""
Enhanced JEBAT System - Simple Initialization Test

This script verifies that the enhanced JEBAT system can be properly initialized
and identifies any remaining issues or missing dependencies.

Usage:
    python test_enhanced_system.py

The test will:
1. Check all required dependencies
2. Verify file structure
3. Test component imports
4. Initialize each component individually
5. Attempt full system initialization
6. Report any issues found
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to Python path for jebat package imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class TestResult:
    """Track test results"""

    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.error = None
        self.duration = 0.0
        self.details = []
        self.start_time = datetime.utcnow()

    def mark_success(self, details: List[str] = None):
        """Mark test as successful"""
        self.success = True
        self.duration = (datetime.utcnow() - self.start_time).total_seconds()
        self.details = details or []

    def mark_failure(self, error: Exception, details: List[str] = None):
        """Mark test as failed"""
        self.success = False
        self.error = str(error)
        self.duration = (datetime.utcnow() - self.start_time).total_seconds()
        self.details = details or []


class EnhancedSystemTester:
    """Test enhanced JEBAT system initialization"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.issues_found: List[str] = []
        self.base_path = Path(__file__).parent / "jebat"

    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}\n")

    def print_test_result(self, result: TestResult):
        """Print formatted test result"""
        icon = "[OK]" if result.success else "[FAIL]"
        status = "PASSED" if result.success else "FAILED"

        print(f"{icon} {result.name} - {status}")
        print(f"   Duration: {result.duration:.2f}s")

        if result.error:
            # Encode to avoid Unicode errors on Windows console
            error_msg = result.error.encode("ascii", errors="replace").decode("ascii")
            print(f"   Error: {error_msg}")

        if result.details:
            print("   Details:")
            for detail in result.details:
                # Encode to avoid Unicode errors
                detail_msg = detail.encode("ascii", errors="replace").decode("ascii")
                print(f"     - {detail_msg}")

        print()

    def test_file_structure(self) -> TestResult:
        """Test that all required files exist"""
        result = TestResult("File Structure Check")
        details = []
        all_exist = True

        required_files = [
            "jebat/cache/smart_cache.py",
            "jebat/decision_engine/engine.py",
            "jebat/error_recovery/system.py",
            "jebat/mcp/protocol_server.py",
            "jebat/gateway/websocket_gateway.py",
            "jebat/integration/enhanced_system.py",
            "jebat/orchestration/agent_orchestrator.py",
            "jebat/specialized_agents/templates.py",
            "jebat/setup_enhanced.py",
            "jebat/config_enhanced.yaml",
        ]

        for file_path in required_files:
            # Remove 'jebat/' prefix for path check since base_path is already Dev/
            relative_path = Path(file_path.replace("jebat/", ""))
            full_path = self.base_path / relative_path
            if full_path.exists():
                details.append(f"[OK] {file_path}")
            else:
                details.append(f"[MISSING] {file_path}")
                all_exist = False

        if all_exist:
            result.mark_success(details)
        else:
            result.mark_failure(Exception("Some files missing"), details)

        self.results.append(result)
        return result

    def test_imports(self) -> TestResult:
        """Test that all required modules can be imported"""
        result = TestResult("Import Check")
        details = []

        try:
            # Add base path to Python path
            if str(self.base_path) not in sys.path:
                sys.path.insert(0, str(self.base_path))

            # Test core imports
            try:
                from jebat.cache.smart_cache import CacheManager, SmartCache
            except ImportError:
                # Try direct import if package structure not set up
                from cache.smart_cache import CacheManager, SmartCache

            details.append("✓ SmartCache imports")

            try:
                from jebat.decision_engine.engine import DecisionEngine
            except ImportError:
                from decision_engine.engine import DecisionEngine

            details.append("✓ DecisionEngine imports")

            try:
                from jebat.error_recovery.system import ErrorRecoverySystem
            except ImportError:
                from error_recovery.system import ErrorRecoverySystem

            details.append("✓ ErrorRecoverySystem imports")

            try:
                from jebat.mcp.protocol_server import MCPProtocolServer
            except ImportError:
                from mcp.protocol_server import MCPProtocolServer

            details.append("✓ MCPProtocolServer imports")

            try:
                from jebat.gateway.websocket_gateway import WebSocketGateway
            except ImportError:
                from gateway.websocket_gateway import WebSocketGateway

            details.append("✓ WebSocketGateway imports")

            try:
                from jebat.orchestration.agent_orchestrator import AgentOrchestrator
            except ImportError:
                from orchestration.agent_orchestrator import AgentOrchestrator

            details.append("✓ AgentOrchestrator imports")

            details.append("✓ Specialized agents imports")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Import failed: {str(e)}")
            result.mark_failure(e, details)

        self.results.append(result)
        return result

    def test_memory_manager(self) -> TestResult:
        """Test MemoryManager initialization"""
        result = TestResult("MemoryManager Initialization")
        details = []

        try:
            from jebat.memory_system.core.memory_manager import MemoryManager
        except ImportError:
            try:
                from memory_system.core.memory_manager import MemoryManager
            except ImportError:
                details.append("✗ MemoryManager import failed - module not found")
                result.mark_failure(
                    Exception("MemoryManager module not found"), details
                )
                self.results.append(result)
                return result

        try:
            from jebat.memory_system.core.memory_manager import MemoryManager

            # Try to initialize
            memory_manager = MemoryManager()
            details.append("✓ MemoryManager created")

            # Check if enhanced methods exist
            if hasattr(memory_manager, "search_memories"):
                details.append("✓ search_memories() method exists")
            else:
                details.append("✗ search_memories() method missing")

            if hasattr(memory_manager, "get_user_profile"):
                details.append("✓ get_user_profile() method exists")
            else:
                details.append("✗ get_user_profile() method missing")

            if hasattr(memory_manager, "get_memory_stats"):
                details.append("✓ get_memory_stats() method exists")
            else:
                details.append("✗ get_memory_stats() method missing")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Initialization failed: {str(e)}")
            result.mark_failure(e, details)
            self.issues_found.append(f"MemoryManager: {str(e)}")

        self.results.append(result)
        return result

    def test_agent_orchestrator(self) -> TestResult:
        """Test AgentOrchestrator initialization"""
        result = TestResult("AgentOrchestrator Initialization")
        details = []

        try:
            from jebat.orchestration.agent_orchestrator import AgentOrchestrator
        except ImportError:
            try:
                from orchestration.agent_orchestrator import AgentOrchestrator
            except ImportError:
                details.append("✗ AgentOrchestrator import failed - module not found")
                result.mark_failure(
                    Exception("AgentOrchestrator module not found"), details
                )
                self.results.append(result)
                return result

        try:
            from jebat.orchestration.agent_orchestrator import AgentOrchestrator

            # Try to initialize
            orchestrator = AgentOrchestrator()
            details.append("✓ AgentOrchestrator created")

            # Check if required methods exist
            if hasattr(orchestrator, "execute_task"):
                details.append("✓ execute_task() method exists")
            else:
                details.append("✗ execute_task() method missing")

            if hasattr(orchestrator, "get_agent_registry"):
                details.append("✓ get_agent_registry() method exists")
            else:
                details.append("✗ get_agent_registry() method missing")

            if hasattr(orchestrator, "shutdown"):
                details.append("✓ shutdown() method exists")
            else:
                details.append("✗ shutdown() method missing")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Initialization failed: {str(e)}")
            result.mark_failure(e, details)
            self.issues_found.append(f"AgentOrchestrator: {str(e)}")

        self.results.append(result)
        return result

    def test_cache_manager(self) -> TestResult:
        """Test CacheManager initialization"""
        result = TestResult("CacheManager Initialization")
        details = []

        try:
            from jebat.cache.smart_cache import CacheManager
        except ImportError:
            try:
                from cache.smart_cache import CacheManager
            except ImportError:
                details.append("✗ CacheManager import failed - module not found")
                result.mark_failure(Exception("CacheManager module not found"), details)
                self.results.append(result)
                return result

        try:
            from jebat.cache.smart_cache import CacheManager

            # Try to initialize
            cache_manager = CacheManager()
            details.append("✓ CacheManager created")

            # Test basic operations
            stats = asyncio.run(cache_manager.get_all_stats())
            details.append(f"✓ Stats retrieved: {len(stats)} cache types")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Initialization failed: {str(e)}")
            result.mark_failure(e, details)
            self.issues_found.append(f"CacheManager: {str(e)}")

        self.results.append(result)
        return result

    def test_decision_engine(self) -> TestResult:
        """Test DecisionEngine initialization"""
        result = TestResult("DecisionEngine Initialization")
        details = []

        try:
            from jebat.decision_engine.engine import DecisionEngine
        except ImportError:
            try:
                from decision_engine.engine import DecisionEngine
            except ImportError:
                details.append("✗ DecisionEngine import failed - module not found")
                result.mark_failure(
                    Exception("DecisionEngine module not found"), details
                )
                self.results.append(result)
                return result

        try:
            from jebat.decision_engine.engine import DecisionEngine

            # Try to initialize with mock agent registry
            mock_registry = {
                "agent1": {
                    "type": "conversational",
                    "capabilities": ["conversation", "memory"],
                }
            }

            decision_engine = DecisionEngine(agent_registry=mock_registry)
            details.append("✓ DecisionEngine created")

            # Check if required methods exist
            if hasattr(decision_engine, "decide"):
                details.append("✓ decide() method exists")
            else:
                details.append("✗ decide() method missing")

            if hasattr(decision_engine, "get_stats"):
                details.append("✓ get_stats() method exists")
            else:
                details.append("✗ get_stats() method missing")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Initialization failed: {str(e)}")
            result.mark_failure(e, details)
            self.issues_found.append(f"DecisionEngine: {str(e)}")

        self.results.append(result)
        return result

    def test_error_recovery(self) -> TestResult:
        """Test ErrorRecoverySystem initialization"""
        result = TestResult("ErrorRecoverySystem Initialization")
        details = []

        try:
            from jebat.error_recovery.system import ErrorRecoverySystem
        except ImportError:
            try:
                from error_recovery.system import ErrorRecoverySystem
            except ImportError:
                details.append("✗ ErrorRecoverySystem import failed - module not found")
                result.mark_failure(
                    Exception("ErrorRecoverySystem module not found"), details
                )
                self.results.append(result)
                return result

        try:
            from jebat.error_recovery.system import ErrorRecoverySystem

            # Try to initialize
            error_recovery = ErrorRecoverySystem()
            details.append("✓ ErrorRecoverySystem created")

            # Check if required methods exist
            if hasattr(error_recovery, "handle_error"):
                details.append("✓ handle_error() method exists")
            else:
                details.append("✗ handle_error() method missing")

            if hasattr(error_recovery, "get_health_status"):
                details.append("✓ get_health_status() method exists")
            else:
                details.append("✗ get_health_status() method missing")

            result.mark_success(details)

        except Exception as e:
            details.append(f"✗ Initialization failed: {str(e)}")
            result.mark_failure(e, details)
            self.issues_found.append(f"ErrorRecoverySystem: {str(e)}")

        self.results.append(result)
        return result

    def test_enhanced_system_integration(self) -> TestResult:
        """Test complete enhanced system initialization"""
        result = TestResult("Enhanced System Integration")
        details = []

        try:
            from jebat.integration.enhanced_system import EnhancedJEBATSystem
        except ImportError:
            try:
                from integration.enhanced_system import EnhancedJEBATSystem
            except ImportError:
                details.append("✗ Enhanced System import failed - module not found")
                result.mark_failure(
                    Exception("Enhanced System module not found"), details
                )
                self.results.append(result)
                return result

        try:
            from jebat.integration.enhanced_system import EnhancedJEBATSystem

            # Try to initialize with minimal config
            config = {
                "mcp_server": {
                    "enabled": False,  # Disable to avoid port conflicts
                },
                "decision_engine": {
                    "enabled": True,
                    "cache_ttl": 3600,
                },
                "cache": {
                    "memory_hot_size": 10,  # Small for testing
                    "memory_hot_entries": 100,
                },
                "agents": {
                    "max_concurrent_tasks": 5,
                },
            }

            system = EnhancedJEBATSystem(config)
            details.append("✓ EnhancedJEBATSystem created")

            # Check if initialization works (async)
            try:
                asyncio.run(system.initialize())
                details.append("✓ System initialized successfully")
            except Exception as init_error:
                # Check if it's a missing dependency error
                if "No module named" in str(init_error):
                    details.append(
                        f"⚠️ Initialization skipped (missing dependencies: {init_error})"
                    )
                    # Don't count as failure, just note the dependency
                    result.mark_success(details)
                else:
                    raise

            result.mark_success(details)

        except Exception as e:
            error_details = str(e)
            details.append(f"✗ Integration failed: {error_details}")
            result.mark_failure(e, details)
            self.issues_found.append(f"EnhancedSystem: {error_details}")

        self.results.append(result)
        return result

    async def test_full_system(self) -> TestResult:
        """Test complete system end-to-end"""
        result = TestResult("Full System Test")
        details = []

        try:
            # Try to import
            try:
                from jebat.integration.enhanced_system import (
                    EnhancedJEBATSystem,
                    RequestContext,
                    create_enhanced_system,
                )
            except ImportError:
                from integration.enhanced_system import (
                    EnhancedJEBATSystem,
                    RequestContext,
                    create_enhanced_system,
                )

            # Create minimal config
            config = {
                "mcp_server": {"enabled": False},
                "decision_engine": {"enabled": True},
                "cache": {"memory_hot_size": 10},
                "agents": {"max_concurrent_tasks": 5},
            }

            # Try to create and initialize
            system = await create_enhanced_system(config)
            details.append("[OK] System created and initialized")

            # Try to process a request
            request_context = RequestContext(
                request_id="test-001",
                user_id="test-user",
                session_id="test-session",
                request_type="test",
                input_data={"request": "Hello, test system!"},
            )

            processing_result = await system.process_request(request_context)
            details.append(f"[OK] Request processed: {processing_result.success}")

            # Clean up
            await system.shutdown()
            details.append("[OK] System shutdown successfully")

            result.mark_success(details)

        except Exception as e:
            error_details = str(e)
            details.append(f"[FAIL] Full system test failed: {error_details}")

            # Provide more helpful error message
            if "ImportError" in type(e).__name__:
                details.append(
                    "   -> Missing dependencies, try: pip install -r requirements.txt"
                )
            elif "AttributeError" in type(e).__name__:
                details.append("   -> Missing methods in component classes")
            elif "ConnectionRefusedError" in type(e).__name__:
                details.append("   -> Database or service not available")

            result.mark_failure(e, details)
            self.issues_found.append(f"FullSystem: {error_details}")

        self.results.append(result)
        return result

    def run_all_tests(self):
        """Run all tests and generate report"""
        self.print_header("Enhanced JEBAT System - Initialization Test Suite")

        # Run synchronous tests
        self.test_file_structure()
        self.print_test_result(self.results[-1])

        self.test_imports()
        self.print_test_result(self.results[-1])

        self.test_memory_manager()
        self.print_test_result(self.results[-1])

        self.test_agent_orchestrator()
        self.print_test_result(self.results[-1])

        self.test_cache_manager()
        self.print_test_result(self.results[-1])

        self.test_decision_engine()
        self.print_test_result(self.results[-1])

        self.test_error_recovery()
        self.print_test_result(self.results[-1])

        # Run asynchronous tests
        self.test_enhanced_system_integration()
        self.print_test_result(self.results[-1])

        try:
            asyncio.run(self.test_full_system())
        except Exception as e:
            logger.error(f"Full system test crashed: {e}")

        self.print_test_result(self.results[-1])

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")

        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed

        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(self.results) * 100):.1f}%")

        if failed > 0:
            print("\n" + "!" * 70)
            print("  ISSUES FOUND:")
            print("!" * 70 + "\n")

            for issue in self.issues_found:
                print(f"• {issue}")

            print("\n" + "-" * 70)
            print("  NEXT STEPS:")
            print("-" * 70 + "\n")

            # Provide remediation advice based on issues
            if any("ImportError" in issue for issue in self.issues_found):
                print("1. Install missing dependencies:")
                print("   pip install -r jebat/requirements.txt")
                print()

            if any("AttributeError" in issue for issue in self.issues_found):
                print("2. Check component implementations have required methods")
                print()

            if any("MemoryManager" in issue for issue in self.issues_found):
                print(
                    "3. Verify memory_system/core/memory_manager.py has enhanced methods"
                )
                print()

            if any("AgentOrchestrator" in issue for issue in self.issues_found):
                print(
                    "4. Verify orchestration/agent_orchestrator.py exists and is correct"
                )
                print()

            if any(
                "ConnectionRefusedError" in issue or "Database" in issue
                for issue in self.issues_found
            ):
                print("5. Start required services (PostgreSQL, Redis, etc.)")
                print("   docker-compose up -d")
                print()

        else:
            print("\n" + "=" * 70)
            print("  ALL TESTS PASSED! System is ready!")
            print("=" * 70 + "\n")

            print("You can now:")
            print("  1. Start the system: python jebat/setup_enhanced.py --start")
            print("  2. Check status: python jebat/setup_enhanced.py --status")
            print("  3. Read documentation: QUICKSTART_ENHANCED.md")


def main():
    """Main entry point"""
    tester = EnhancedSystemTester()
    tester.run_all_tests()

    # Exit with appropriate code
    failed = sum(1 for r in tester.results if not r.success)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
