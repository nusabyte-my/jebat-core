"""
Test MemoryManager Integration with Ultra-Think

Demonstrates memory-augmented thinking.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat import MemoryManager
from jebat.features.ultra_think import ThinkingMode, create_ultra_think


async def test_memory_integration():
    """Test Ultra-Think with MemoryManager integration"""
    print("\n" + "=" * 60)
    print("Testing MemoryManager Integration with Ultra-Think")
    print("=" * 60)

    # Initialize MemoryManager
    print("\n1. Initializing MemoryManager...")
    memory_manager = MemoryManager()
    print("   MemoryManager initialized")

    # Store some test memories
    print("\n2. Storing test memories...")
    from jebat.core.memory.layers import MemoryLayer

    await memory_manager.store(
        content="The user prefers Python for development and uses Windows OS",
        layer=MemoryLayer.M1_EPISODIC,
        user_id="test_user",
    )
    await memory_manager.store(
        content="Project deadline is next Friday for the database integration",
        layer=MemoryLayer.M1_EPISODIC,
        user_id="test_user",
    )
    await memory_manager.store(
        content="User likes to work with async/await patterns",
        layer=MemoryLayer.M2_SEMANTIC,
        user_id="test_user",
    )
    print("   Stored 3 test memories")

    # Initialize Ultra-Think with memory integration
    print("\n3. Initializing Ultra-Think with memory integration...")
    thinker = await create_ultra_think(
        config={"max_thoughts": 15, "default_mode": "deliberate"},
        memory_manager=memory_manager,
        enable_db_persistence=False,  # Disable DB for this test
        enable_memory_integration=True,
    )
    print("   Ultra-Think initialized")

    # Run thinking session with memory context
    print("\n4. Running thinking session with memory context...")
    result = await thinker.think(
        problem="What programming language and OS does the user prefer?",
        mode=ThinkingMode.DELIBERATE,
        user_id="test_user",  # This enables memory retrieval
        timeout=10,
    )

    print(f"\n5. Thinking Result:")
    print(f"   Success: {result.success}")
    print(f"   Conclusion: {result.conclusion}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Thoughts: {len(result.reasoning_steps)}")

    # Show thought chain
    print(f"\n6. Thought Chain:")
    for i, thought in enumerate(result.reasoning_steps[:5], 1):
        print(f"   {i}. {thought[:80]}...")

    print("\n" + "=" * 60)
    print("Memory integration test completed successfully!")
    print("=" * 60)

    return result.success


if __name__ == "__main__":
    success = asyncio.run(test_memory_integration())
    exit(0 if success else 1)
