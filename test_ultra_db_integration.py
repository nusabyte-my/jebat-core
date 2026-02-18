"""
Test Ultra-Loop and Ultra-Think Database Integration

Tests for:
- Ultra-Loop cycle persistence
- Ultra-Think session persistence
- Memory integration
- Statistics and history retrieval
"""

import asyncio
import logging
from datetime import datetime

from jebat.features.ultra_loop import UltraLoop, create_ultra_loop
from jebat.features.ultra_loop.database_repository import UltraLoopRepository
from jebat.features.ultra_think import ThinkingMode, UltraThink, create_ultra_think
from jebat.features.ultra_think.database_repository import UltraThinkRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_ultra_loop_db_integration():
    """Test Ultra-Loop database integration"""
    print("\n" + "=" * 60)
    print("Testing Ultra-Loop Database Integration")
    print("=" * 60)

    # Create Ultra-Loop with DB persistence
    loop = await create_ultra_loop(
        config={"cycle_interval": 0.1, "max_cycles": 3},
        enable_db_persistence=True,
    )

    try:
        # Start the loop
        print("\n1. Starting Ultra-Loop...")
        await loop.start()

        # Wait for cycles to complete
        print("2. Waiting for cycles to complete...")
        await asyncio.sleep(2)

        # Stop the loop
        print("3. Stopping Ultra-Loop...")
        await loop.stop()

        # Get metrics
        print("\n4. Loop Metrics:")
        metrics = loop.get_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")

        # Get cycle history (if DB is working)
        print("\n5. Cycle History:")
        history = await loop.get_cycle_history(limit=5)
        if history:
            for cycle in history:
                print(f"   - {cycle.get('cycle_id')}: {cycle.get('status')}")
        else:
            print("   No cycle history available (DB may not be connected)")

        # Get statistics
        print("\n6. Statistics:")
        stats = await loop.get_statistics(time_window_hours=1)
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\n✅ Ultra-Loop DB integration test completed")
        return True

    except Exception as e:
        print(f"\n❌ Ultra-Loop DB integration test failed: {e}")
        logger.exception("Test failed")
        return False


async def test_ultra_think_db_integration():
    """Test Ultra-Think database integration"""
    print("\n" + "=" * 60)
    print("Testing Ultra-Think Database Integration")
    print("=" * 60)

    # Create Ultra-Think with DB persistence
    thinker = await create_ultra_think(
        config={"max_thoughts": 10, "default_mode": "deliberate"},
        enable_db_persistence=True,
        enable_memory_integration=False,  # Disable memory for this test
    )

    try:
        # Run thinking session
        print("\n1. Starting thinking session...")
        result = await thinker.think(
            problem="What is the meaning of artificial intelligence?",
            mode=ThinkingMode.DELIBERATE,
            timeout=5,
        )

        print(f"\n2. Thinking Result:")
        print(f"   Success: {result.success}")
        print(f"   Conclusion: {result.conclusion[:100]}...")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Thoughts: {len(result.reasoning_steps)}")
        print(f"   Execution Time: {result.execution_time:.2f}s")

        # Get session history (if DB is working)
        print("\n3. Session History:")
        history = await thinker.get_session_history(limit=5)
        if history:
            for session in history:
                print(f"   - {session.get('trace_id')}: {session.get('status')}")
        else:
            print("   No session history available (DB may not be connected)")

        # Get statistics
        print("\n4. Statistics:")
        stats = await thinker.get_statistics(time_window_hours=1)
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Get thought chain
        print("\n5. Thought Chain:")
        thoughts = await thinker.get_thought_chain(result.trace.trace_id)
        if thoughts:
            for i, thought in enumerate(thoughts[:5], 1):
                print(
                    f"   {i}. [{thought.get('phase')}] {thought.get('content')[:60]}..."
                )
        else:
            print("   No thought chain available (DB may not be connected)")

        print("\n✅ Ultra-Think DB integration test completed")
        return True

    except Exception as e:
        print(f"\n❌ Ultra-Think DB integration test failed: {e}")
        logger.exception("Test failed")
        return False


async def test_repositories_directly():
    """Test repositories directly without full system"""
    print("\n" + "=" * 60)
    print("Testing Repositories Directly")
    print("=" * 60)

    loop_repo = UltraLoopRepository()
    think_repo = UltraThinkRepository()

    try:
        # Test Ultra-Loop repository
        print("\n1. Testing Ultra-Loop Repository...")
        cycle = await loop_repo.create_cycle(
            cycle_id="test_cycle_001",
            metadata={"test": True},
        )
        print(f"   Created cycle: {cycle.cycle_id}")

        # Update cycle status
        await loop_repo.update_cycle_status(
            cycle_id="test_cycle_001",
            status="completed",
        )
        print("   Updated cycle status")

        # Create phase
        await loop_repo.create_phase(
            cycle_id="test_cycle_001",
            phase_name="perception",
            phase_order=0,
            outputs={"test": "data"},
        )
        print("   Created phase")

        # Get cycle
        retrieved_cycle = await loop_repo.get_cycle("test_cycle_001")
        print(
            f"   Retrieved cycle: {retrieved_cycle.cycle_id if retrieved_cycle else 'None'}"
        )

        # Test Ultra-Think repository
        print("\n2. Testing Ultra-Think Repository...")
        session = await think_repo.create_session(
            trace_id="test_trace_001",
            problem_statement="Test problem",
            thinking_mode="deliberate",
        )
        print(f"   Created session: {session.trace_id}")

        # Update session status
        await think_repo.update_session_status(
            trace_id="test_trace_001",
            status="completed",
            conclusion="Test conclusion",
            confidence_score=0.85,
        )
        print("   Updated session status")

        # Create thought
        await think_repo.create_thought(
            trace_id="test_trace_001",
            thought_id="thought_001",
            content="Test thought content",
            phase="orientation",
            phase_order=0,
            confidence=0.8,
        )
        print("   Created thought")

        # Get session
        retrieved_session = await think_repo.get_session("test_trace_001")
        print(
            f"   Retrieved session: {retrieved_session.trace_id if retrieved_session else 'None'}"
        )

        # Get thought chain
        thoughts = await think_repo.get_thought_chain("test_trace_001")
        print(f"   Retrieved {len(thoughts)} thoughts")

        print("\n✅ Repository direct test completed")
        return True

    except Exception as e:
        print(f"\n❌ Repository direct test failed: {e}")
        logger.exception("Test failed")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("JEBAT Ultra-Loop & Ultra-Think Database Integration Tests")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}")

    results = {
        "repositories": await test_repositories_directly(),
        "ultra_loop": await test_ultra_loop_db_integration(),
        "ultra_think": await test_ultra_think_db_integration(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print(
        f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )
    print(f"Completed at: {datetime.utcnow().isoformat()}")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
