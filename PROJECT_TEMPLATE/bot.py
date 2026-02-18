"""
My JEBAT-Powered AI Assistant

Run: python bot.py
"""

import asyncio
import os

from jebat_sdk import JEBATClient

# Configuration
API_URL = os.getenv("JEBAT_API_URL", "http://localhost:8000")
USER_ID = os.getenv("USER_ID", "default_user")
BOT_NAME = os.getenv("BOT_NAME", "JEBAT Assistant")


async def main():
    """Main chatbot loop"""
    print(f"🗡️  {BOT_NAME}")
    print(f"API: {API_URL}")
    print("Type 'quit' to exit\n")

    async with JEBATClient(base_url=API_URL) as client:
        while True:
            # Get user input
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print(f"{BOT_NAME}: Goodbye! 👋")
                break

            if not user_input:
                continue

            # Get response from JEBAT
            try:
                response = await client.chat(
                    message=user_input, user_id=USER_ID, mode="deliberate", timeout=30
                )

                print(f"{BOT_NAME}: {response.response}")
                print(f"Confidence: {response.confidence:.1%}\n")

            except Exception as e:
                print(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
