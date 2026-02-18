#!/usr/bin/env python3
"""
🗡️ JEBAT Simple Chatbot

A simple, working chatbot powered by JEBAT.

Requirements:
    pip install jebat-sdk

Usage:
    python examples/chat/simple_chatbot.py

Features:
- Simple conversation interface
- No configuration needed (uses local API)
- Shows confidence scores
- Easy to customize
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import aiohttp

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("⚠️  SDK not available. Install with: pip install aiohttp")


async def chat_with_jebat():
    """Simple chatbot loop"""

    print("=" * 60)
    print("🗡️  JEBAT Simple Chatbot")
    print("=" * 60)
    print("\nType your message and press Enter")
    print("Commands: 'quit', 'exit', or 'bye' to stop\n")

    # API Configuration
    API_URL = "http://localhost:8000/api/v1"
    USER_ID = "default_user"

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n🗡️  JEBAT: Goodbye! Have a great day! 👋\n")
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Call JEBAT API
                async with session.post(
                    f"{API_URL}/chat/completions",
                    json={
                        "message": user_input,
                        "user_id": USER_ID,
                        "mode": "deliberate",
                        "timeout": 30,
                    },
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        print(f"\n🗡️  JEBAT: {data.get('response', 'No response')}")
                        print(f"💭 Confidence: {data.get('confidence', 0):.1%}")
                        print(f"⏱️  Duration: {data.get('execution_time', 0):.2f}s\n")
                    else:
                        print(f"\n⚠️  Error: API returned status {response.status}")
                        print("Make sure JEBAT API is running: docker-compose up -d\n")

            except aiohttp.ClientError as e:
                print(f"\n❌ Connection error: {e}")
                print("Make sure JEBAT API is running (http://localhost:8000)\n")
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    if SDK_AVAILABLE:
        asyncio.run(chat_with_jebat())
    else:
        print("\nPlease install required packages:")
        print("  pip install aiohttp\n")
