"""
Test Agent Integration with Ultra-Loop

Demonstrates agent execution during Ultra-Loop action phase.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat.core.agents.orchestrator import AgentOrchestrator, AgentTask, TaskPriority
from jebat.features.ultra_loop import UltraLoop, create_ultra_loop


async def test_agent_integration():
    """Test Ultra-Loop with Agent Orchestrator integration"""
    print("\n" + "=" * 60)
    print("Testing Agent Integration with Ultra-Loop")
    print("=" * 60)

    # Initialize Agent Orchestrator
    print("\n1. Initializing Agent Orchestrator...")
    agent_orchestrator = AgentOrchestrator(
        config={"max_concurrent_tasks": 5},
        max_concurrent_tasks=5,
    )
    print("   Agent Orchestrator initialized")

    # Initialize Ultra-Loop with agent integration
    print("\n2. Initializing Ultra-Loop with agent integration...")
    loop = await create_ultra_loop(
        config={
            "cycle_interval": 0.5,  # Fast cycles for testing
            "max_cycles": 3,
        },
        agent_orchestrator=agent_orchestrator,
        enable_db_persistence=False,  # Disable DB for this test
    )
    print("   Ultra-Loop initialized with agent orchestrator connected")

    # Register a simple agent task handler
    print("\n3. Registering test agent task handler...")

    async def test_task_handler(task):
        """Simple test task handler"""
        print(f"   Executing task: {task.description}")
        await asyncio.sleep(0.1)  # Simulate work
        from jebat.core.agents.orchestrator import TaskResult

        return TaskResult(
            task_id=task.task_id,
            success=True,
            result={"message": "Task completed successfully"},
            execution_time=0.1,
        )

    # Add handler to orchestrator (if method exists)
    if hasattr(agent_orchestrator, "register_handler"):
        agent_orchestrator.register_handler("default", test_task_handler)
    else:
        # Fallback: add as attribute
        agent_orchestrator.test_handler = test_task_handler
        print("   Registered test handler (fallback method)")

    print("   Test agent task handler registered")

    # Start Ultra-Loop
    print("\n4. Starting Ultra-Loop...")
    await loop.start()

    # Wait for cycles to complete
    print("5. Waiting for cycles to complete...")
    await asyncio.sleep(3)

    # Stop Ultra-Loop
    print("6. Stopping Ultra-Loop...")
    await loop.stop()

    # Get metrics
    print("\n7. Loop Metrics:")
    metrics = loop.get_metrics()
    print(f"   Total cycles: {metrics.get('total_cycles', 0)}")
    print(f"   Successful cycles: {metrics.get('successful_cycles', 0)}")
    print(f"   Failed cycles: {metrics.get('failed_cycles', 0)}")
    print(
        f"   Success rate: {metrics.get('successful_cycles', 0) / max(metrics.get('total_cycles', 1), 1) * 100:.1f}%"
    )

    # Get agent orchestrator stats
    print("\n8. Agent Orchestrator Stats:")
    if hasattr(agent_orchestrator, "get_stats"):
        stats = agent_orchestrator.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print(
            f"   Active tasks: {len(agent_orchestrator.active_tasks) if hasattr(agent_orchestrator, 'active_tasks') else 'N/A'}"
        )
        print(
            f"   Completed tasks: {len(agent_orchestrator.completed_tasks) if hasattr(agent_orchestrator, 'completed_tasks') else 'N/A'}"
        )

    print("\n" + "=" * 60)
    print("Agent integration test completed!")
    print("=" * 60)

    return metrics.get("successful_cycles", 0) > 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("JEBAT Agent Integration Test")
    print("=" * 60)

    success = asyncio.run(test_agent_integration())

    print(f"\n{'=' * 60}")
    print(f"Test Result: {'PASSED' if success else 'FAILED'}")
    print(f"{'=' * 60}\n")

    exit(0 if success else 1)
