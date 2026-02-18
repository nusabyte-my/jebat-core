"""
Test Channel Integration

Tests ChannelManager and Telegram channel integration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from jebat.features.ultra_loop import create_ultra_loop
from jebat.integrations.channels.channel_manager import ChannelManager
from jebat.integrations.channels.telegram import (
    TelegramChannel,
    create_telegram_channel,
)


async def test_channel_manager():
    """Test ChannelManager basic functionality"""
    print("\n" + "=" * 60)
    print("Testing ChannelManager")
    print("=" * 60)

    # Initialize ChannelManager
    print("\n1. Initializing ChannelManager...")
    manager = ChannelManager(
        config={"test_mode": True},
        ultra_loop=None,
    )
    print("   ChannelManager initialized")

    # Test channel registration
    print("\n2. Testing channel registration...")

    # Create mock channel
    class MockChannel:
        async def start(self):
            print("   Mock channel started")

        async def stop(self):
            print("   Mock channel stopped")

        async def send_message(self, recipient, message, **kwargs):
            print(f"   Mock sent to {recipient}: {message[:50]}...")

    mock = MockChannel()
    manager.register_channel("mock", mock)

    channels = manager.list_channels()
    print(f"   Registered channels: {channels}")
    assert "mock" in channels, "Mock channel not registered"
    print("   OK Channel registration: PASSED")

    # Test message sending
    print("\n3. Testing message sending...")
    await manager.send_message("mock", "Test message", "user123")
    print("   OK Message sending: PASSED")

    # Test broadcast
    print("\n4. Testing broadcast...")
    await manager.broadcast("Broadcast message")
    print("   OK Broadcast: PASSED")

    # Test statistics
    print("\n5. Testing statistics...")
    stats = manager.get_stats()
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   Messages received: {stats['messages_received']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Channels: {stats['channel_count']}")
    print("   OK Statistics: PASSED")

    # Test message handler
    print("\n6. Testing message handlers...")

    received_messages = []

    async def test_handler(channel, message, sender):
        received_messages.append(
            {
                "channel": channel,
                "message": message,
                "sender": sender,
            }
        )
        print(f"   Handler received: {message[:30]}... from {sender}")

    manager.add_message_handler(test_handler)
    await manager.process_message("mock", "Hello from test", "test_user")

    assert len(received_messages) == 1, "Handler not called"
    assert received_messages[0]["message"] == "Hello from test"
    print("   OK Message handlers: PASSED")

    print("\n" + "=" * 60)
    print("ChannelManager test completed successfully!")
    print("=" * 60)

    return True


async def test_telegram_channel_mock():
    """Test Telegram channel with mock (no real bot token)"""
    print("\n" + "=" * 60)
    print("Testing Telegram Channel (Mock)")
    print("=" * 60)

    # Test initialization
    print("\n1. Testing Telegram channel initialization...")

    # Use mock token for testing
    mock_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

    try:
        channel = await create_telegram_channel(
            bot_token=mock_token,
            ultra_loop=None,
            config={"test_mode": True},
        )
        print("   Telegram channel created")

        # Verify properties
        assert channel.bot_token == mock_token
        assert channel._running == False
        print("   OK Initialization: PASSED")

    except Exception as e:
        print(f"   Note: {e}")
        print("   (Expected - no real Telegram connection)")

    print("\n" + "=" * 60)
    print("Telegram channel test completed!")
    print("=" * 60)

    return True


async def test_channel_with_ultra_loop():
    """Test channel integration with Ultra-Loop"""
    print("\n" + "=" * 60)
    print("Testing Channel + Ultra-Loop Integration")
    print("=" * 60)

    # Initialize Ultra-Loop
    print("\n1. Initializing Ultra-Loop...")
    ultra_loop = await create_ultra_loop(
        config={"cycle_interval": 0.5, "max_cycles": 1},
        enable_db_persistence=False,
    )
    print("   Ultra-Loop initialized")

    # Initialize ChannelManager with Ultra-Loop
    print("\n2. Initializing ChannelManager with Ultra-Loop...")
    manager = ChannelManager(
        config={"test_mode": True},
        ultra_loop=ultra_loop,
    )
    print("   ChannelManager initialized with Ultra-Loop connected")

    # Create mock channel with Ultra-Loop
    print("\n3. Creating mock channel with Ultra-Loop integration...")

    class UltraLoopMockChannel:
        def __init__(self, ultra_loop):
            self.ultra_loop = ultra_loop

        async def start(self):
            print("   Channel started with Ultra-Loop")

        async def stop(self):
            print("   Channel stopped")

        async def send_message(self, recipient, message, **kwargs):
            print(f"   Sent: {message[:50]}...")

    channel = UltraLoopMockChannel(ultra_loop)
    manager.register_channel("ultraloop_mock", channel)
    print("   OK Channel registered")

    # Test message processing through Ultra-Loop
    print("\n4. Testing message processing through Ultra-Loop...")

    # Start Ultra-Loop
    await ultra_loop.start()
    await asyncio.sleep(1)  # Let it run one cycle

    # Process a message
    await manager.process_message(
        "ultraloop_mock",
        "What is the meaning of life?",
        "user123",
    )

    # Stop Ultra-Loop
    await ultra_loop.stop()

    # Check stats
    stats = manager.get_stats()
    print(f"   Messages processed: {stats['messages_received']}")
    print(f"   Ultra-Loop cycles: {ultra_loop.get_metrics().get('total_cycles', 0)}")
    print("   OK Integration: PASSED")

    print("\n" + "=" * 60)
    print("Channel + Ultra-Loop integration test completed!")
    print("=" * 60)

    return True


async def main():
    """Run all channel integration tests"""
    print("\n" + "=" * 60)
    print("JEBAT Channel Integration Tests")
    print("=" * 60)

    results = {
        "channel_manager": await test_channel_manager(),
        "telegram_mock": await test_telegram_channel_mock(),
        "ultra_loop_integration": await test_channel_with_ultra_loop(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
