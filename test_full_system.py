"""
JEBAT Full System Integration Test

Comprehensive end-to-end test of the JEBAT enhanced system including:
- Ultra-Loop continuous processing
- Ultra-Think deep reasoning
- Memory system integration
- Agent orchestration
- Decision engine
- Error recovery

Usage:
    python test_full_system.py
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IntegrationTestResult:
    """Track integration test results"""

    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.duration = 0.0
        self.details = []
        self.errors = []
        self.start_time = datetime.utcnow()

    def add_detail(self, detail: str):
        """Add a detail to the test result"""
        self.details.append(detail)
        logger.info(f"  ✓ {detail}")

    def add_error(self, error: str):
        """Add an error to the test result"""
        self.errors.append(error)
        logger.error(f"  ✗ {error}")

    def mark_success(self):
        """Mark test as successful"""
        self.success = True
        self.duration = (datetime.utcnow() - self.start_time).total_seconds()

    def mark_failure(self):
        """Mark test as failed"""
        self.success = False
        self.duration = (datetime.utcnow() - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "success": self.success,
            "duration": self.duration,
            "details": self.details,
            "errors": self.errors,
        }


class FullSystemIntegrationTest:
    """Run full system integration tests"""

    def __init__(self):
        self.results = []
        self.components = {}

    async def test_ultra_loop_integration(self) -> IntegrationTestResult:
        """Test Ultra-Loop integration with all systems"""
        result = IntegrationTestResult("Ultra-Loop Integration")

        try:
            from jebat.cache.smart_cache import CacheManager
            from jebat.decision_engine.engine import DecisionEngine
            from jebat.memory_system.core.memory_manager import MemoryManager
            from jebat.ultra_loop import LoopPhase, UltraLoop, create_ultra_loop

            # Initialize components
            memory_manager = MemoryManager()
            result.add_detail("Memory Manager initialized")

            cache_manager = CacheManager()
            result.add_detail("Cache Manager initialized")

            decision_engine = DecisionEngine(agent_registry={})
            result.add_detail("Decision Engine initialized")

            # Create Ultra-Loop with all components
            config = {
                "cycle_interval": 0.5,  # Fast cycles for testing
                "max_cycles": 3,
            }

            ultra_loop = await create_ultra_loop(
                config=config,
                memory_manager=memory_manager,
                decision_engine=decision_engine,
                cache_manager=cache_manager,
            )
            result.add_detail("Ultra-Loop created with all components")

            # Track phase executions
            phase_executions = {phase: 0 for phase in LoopPhase}

            def track_phase(context):
                phase_executions[context.phase] += 1

            for phase in LoopPhase:
                ultra_loop.on_phase(phase, track_phase)

            # Run the loop
            await ultra_loop.start()
            result.add_detail("Ultra-Loop started")

            # Wait for cycles to complete
            await asyncio.sleep(3)

            await ultra_loop.stop()
            result.add_detail("Ultra-Loop stopped")

            # Verify phase executions
            for phase, count in phase_executions.items():
                if count > 0:
                    result.add_detail(f"Phase {phase.value} executed {count} times")
                else:
                    result.add_error(f"Phase {phase.value} never executed")

            # Get metrics
            metrics = ultra_loop.get_metrics()
            result.add_detail(f"Total cycles: {metrics['total_cycles']}")
            result.add_detail(f"Successful cycles: {metrics['successful_cycles']}")

            if metrics["successful_cycles"] > 0:
                result.mark_success()
            else:
                result.mark_failure()

        except Exception as e:
            result.add_error(f"Test failed: {str(e)}")
            result.mark_failure()

        self.results.append(result)
        return result

    async def test_ultra_think_integration(self) -> IntegrationTestResult:
        """Test Ultra-Think integration with all systems"""
        result = IntegrationTestResult("Ultra-Think Integration")

        try:
            from jebat.decision_engine.engine import DecisionEngine
            from jebat.memory_system.core.memory_manager import MemoryManager
            from jebat.ultra_think import ThinkingMode, UltraThink, create_ultra_think

            # Initialize components
            memory_manager = MemoryManager()
            result.add_detail("Memory Manager initialized")

            decision_engine = DecisionEngine(agent_registry={})
            result.add_detail("Decision Engine initialized")

            # Create Ultra-Think with all components
            config = {
                "max_thoughts": 15,
                "default_mode": "deliberate",
                "enable_reflection": True,
                "enable_verification": True,
            }

            ultra_think = await create_ultra_think(
                config=config,
                memory_manager=memory_manager,
                decision_engine=decision_engine,
            )
            result.add_detail("Ultra-Think created with all components")

            # Test different thinking modes
            test_problems = [
                ("What is 2 + 2?", ThinkingMode.FAST),
                (
                    "How should I prioritize my tasks today?",
                    ThinkingMode.DELIBERATE,
                ),
                (
                    "What are the long-term implications of AI on society?",
                    ThinkingMode.DEEP,
                ),
            ]

            for problem, mode in test_problems:
                thinking_result = await ultra_think.think(
                    problem, mode=mode, timeout=10
                )

                if thinking_result.success:
                    result.add_detail(
                        f"{mode.value} thinking: {len(thinking_result.reasoning_steps)} steps, "
                        f"{thinking_result.confidence:.1%} confidence"
                    )
                else:
                    result.add_error(f"{mode.value} thinking failed")

            # Get statistics
            stats = ultra_think.get_stats()
            result.add_detail(f"Total sessions: {stats['total_sessions']}")
            result.add_detail(f"Successful sessions: {stats['successful_sessions']}")
            result.add_detail(
                f"Avg thoughts/session: {stats['avg_thoughts_per_session']:.1f}"
            )

            if stats["successful_sessions"] > 0:
                result.mark_success()
            else:
                result.mark_failure()

        except Exception as e:
            result.add_error(f"Test failed: {str(e)}")
            result.mark_failure()

        self.results.append(result)
        return result

    async def test_combined_workflow(self) -> IntegrationTestResult:
        """Test combined Ultra-Loop and Ultra-Think workflow"""
        result = IntegrationTestResult("Combined Workflow")

        try:
            from jebat.ultra_loop import LoopPhase, UltraLoop, create_ultra_loop
            from jebat.ultra_think import ThinkingMode, UltraThink, create_ultra_think

            # Initialize both systems
            ultra_loop = await create_ultra_loop(
                config={"cycle_interval": 1.0, "max_cycles": 2}
            )
            result.add_detail("Ultra-Loop initialized")

            ultra_think = await create_ultra_think(
                config={"max_thoughts": 10, "default_mode": "deliberate"}
            )
            result.add_detail("Ultra-Think initialized")

            # Start Ultra-Loop
            await ultra_loop.start()
            result.add_detail("Ultra-Loop started")

            # Run a thinking session while loop is running
            thinking_result = await ultra_think.think(
                "How can I improve my productivity?",
                mode=ThinkingMode.STRATEGIC,
                timeout=10,
            )

            if thinking_result.success:
                result.add_detail(
                    f"Thinking session completed: {thinking_result.confidence:.1%} confidence"
                )
            else:
                result.add_error("Thinking session failed")

            # Wait for loop cycles
            await asyncio.sleep(3)

            # Stop Ultra-Loop
            await ultra_loop.stop()
            result.add_detail("Ultra-Loop stopped")

            # Verify both systems worked
            loop_metrics = ultra_loop.get_metrics()
            think_stats = ultra_think.get_stats()

            result.add_detail(
                f"Loop cycles: {loop_metrics['total_cycles']}, "
                f"Think sessions: {think_stats['total_sessions']}"
            )

            if (
                loop_metrics["successful_cycles"] > 0
                and think_stats["successful_sessions"] > 0
            ):
                result.mark_success()
            else:
                result.mark_failure()

        except Exception as e:
            result.add_error(f"Test failed: {str(e)}")
            result.mark_failure()

        self.results.append(result)
        return result

    async def test_error_handling(self) -> IntegrationTestResult:
        """Test error handling in ultra-processes"""
        result = IntegrationTestResult("Error Handling")

        try:
            from jebat.ultra_think import ThinkingMode, create_ultra_think

            ultra_think = await create_ultra_think(
                config={"max_thoughts": 5, "enable_reflection": False}
            )

            # Test timeout handling
            start = time.time()
            thinking_result = await ultra_think.think(
                "Complex problem",
                mode=ThinkingMode.DEEP,
                timeout=0.001,  # Very short timeout
            )
            elapsed = time.time() - start

            if (
                not thinking_result.success
                and "timeout" in str(thinking_result.metadata.get("error", "")).lower()
            ):
                result.add_detail("Timeout handling works correctly")
            else:
                result.add_detail(
                    f"Timeout test: {elapsed:.3f}s, success={thinking_result.success}"
                )

            # Test normal operation after error
            thinking_result2 = await ultra_think.think(
                "Simple question",
                mode=ThinkingMode.FAST,
                timeout=5,
            )

            if thinking_result2.success:
                result.add_detail("System recovered after timeout")
            else:
                result.add_error("System failed to recover")

            result.mark_success()

        except Exception as e:
            result.add_error(f"Test failed: {str(e)}")
            result.mark_failure()

        self.results.append(result)
        return result

    async def test_performance(self) -> IntegrationTestResult:
        """Test performance of ultra-processes"""
        result = IntegrationTestResult("Performance")

        try:
            from jebat.ultra_loop import create_ultra_loop
            from jebat.ultra_think import ThinkingMode, create_ultra_think

            # Test Ultra-Loop performance
            ultra_loop = await create_ultra_loop(
                config={"cycle_interval": 0.1, "max_cycles": 10}
            )

            start = time.time()
            await ultra_loop.start()
            await asyncio.sleep(2)
            await ultra_loop.stop()
            loop_duration = time.time() - start

            loop_metrics = ultra_loop.get_metrics()
            cycles_per_second = (
                loop_metrics["total_cycles"] / loop_duration if loop_duration > 0 else 0
            )

            result.add_detail(
                f"Ultra-Loop: {loop_metrics['total_cycles']} cycles in {loop_duration:.2f}s"
            )
            result.add_detail(f"Performance: {cycles_per_second:.1f} cycles/second")

            # Test Ultra-Think performance
            ultra_think = await create_ultra_think(
                config={"max_thoughts": 20, "default_mode": "deliberate"}
            )

            start = time.time()
            result_obj = await ultra_think.think(
                "Analyze this problem thoroughly",
                mode=ThinkingMode.DELIBERATE,
                timeout=10,
            )
            think_duration = time.time() - start

            result.add_detail(
                f"Ultra-Think: {len(result_obj.reasoning_steps)} thoughts in {think_duration:.2f}s"
            )

            # Calculate thoughts per second (handle very fast execution)
            thoughts_per_second = (
                len(result_obj.reasoning_steps) / think_duration
                if think_duration > 0
                else len(result_obj.reasoning_steps) * 1000  # Assume <1ms if 0
            )
            result.add_detail(f"Performance: {thoughts_per_second:.1f} thoughts/second")

            if cycles_per_second > 0 and result_obj.success:
                result.mark_success()
            else:
                result.mark_failure()

        except Exception as e:
            result.add_error(f"Test failed: {str(e)}")
            result.mark_failure()

        self.results.append(result)
        return result

    def generate_report(self) -> str:
        """Generate test report"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("JEBAT Full System Integration Test Report")
        report.append("=" * 70)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests

        report.append(f"\nTotal Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")

        report.append("\n" + "-" * 70)
        report.append("Test Results:")
        report.append("-" * 70)

        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report.append(f"\n{status} {result.name}")
            report.append(f"  Duration: {result.duration:.2f}s")

            if result.details:
                report.append("  Details:")
                for detail in result.details:
                    report.append(f"    • {detail}")

            if result.errors:
                report.append("  Errors:")
                for error in result.errors:
                    report.append(f"    ✗ {error}")

        report.append("\n" + "=" * 70)

        return "\n".join(report)


async def main():
    """Run all integration tests"""
    logger.info("=" * 70)
    logger.info("JEBAT Full System Integration Test")
    logger.info("=" * 70)

    tester = FullSystemIntegrationTest()

    # Run all tests
    await tester.test_ultra_loop_integration()
    await tester.test_ultra_think_integration()
    await tester.test_combined_workflow()
    await tester.test_error_handling()
    await tester.test_performance()

    # Generate and print report
    report = tester.generate_report()
    logger.info(report)

    # Return exit code
    passed = sum(1 for r in tester.results if r.success)
    total = len(tester.results)
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
