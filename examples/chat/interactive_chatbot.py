#!/usr/bin/env python3
"""
🗡️ JEBAT Interactive Chatbot

Interactive chatbot with conversation history and memory.

Requirements:
    pip install jebat-sdk rich

Usage:
    python examples/chat/interactive_chatbot.py

Features:
- Beautiful colored output
- Conversation history
- Memory integration
- Multiple thinking modes
- Status display
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import rich for beautiful output
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better output: pip install rich")

try:
    import aiohttp

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class InteractiveChatbot:
    """Interactive chatbot with history and memory"""

    def __init__(self):
        self.api_url = "http://localhost:8000/api/v1"
        self.user_id = "user_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_history = []
        self.console = Console() if RICH_AVAILABLE else None

    def print_header(self):
        """Print chatbot header"""
        if self.console:
            header = """
# 🗡️ JEBAT Interactive Chatbot

**Type your message below**
Commands: `quit` to exit, `history` to view history, `mode` to change thinking mode
            """
            self.console.print(
                Panel(Markdown(header), title="JEBAT", border_style="blue")
            )
        else:
            print("=" * 60)
            print("🗡️  JEBAT Interactive Chatbot")
            print("=" * 60)
            print("Commands: quit, history, mode\n")

    def print_response(self, response: str, confidence: float, duration: float):
        """Print bot response"""
        if self.console:
            panel = Panel(
                response,
                title=f"🗡️ JEBAT (Confidence: {confidence:.0%}, Duration: {duration:.2f}s)",
                border_style="green",
            )
            self.console.print(panel)
        else:
            print(f"\n🗡️ JEBAT: {response}")
            print(f"💭 Confidence: {confidence:.0%} | ⏱️ Duration: {duration:.2f}s\n")

    def show_history(self):
        """Show conversation history"""
        if not self.conversation_history:
            print("\n📜 No conversation history yet\n")
            return

        print("\n" + "=" * 60)
        print("📜 CONVERSATION HISTORY")
        print("=" * 60)

        for i, (user_msg, bot_msg) in enumerate(self.conversation_history[-10:], 1):
            print(f"\n{i}. You: {user_msg}")
            print(f"   JEBAT: {bot_msg[:100]}...")

        print("\n" + "=" * 60 + "\n")

    def select_mode(self) -> str:
        """Let user select thinking mode"""
        modes = {
            "1": ("fast", "⚡ Quick responses"),
            "2": ("deliberate", "🤔 Balanced reasoning"),
            "3": ("deep", "🧠 Deep analysis"),
            "4": ("strategic", "📊 Long-term planning"),
            "5": ("creative", "🎨 Creative thinking"),
            "6": ("critical", "🔍 Critical evaluation"),
        }

        print("\n🎯 Select Thinking Mode:")
        for key, (mode, desc) in modes.items():
            print(f"  {key}. {mode} - {desc}")

        choice = input(
            "\nEnter choice (1-6, or press Enter for 'deliberate'): "
        ).strip()
        return modes.get(choice, ("deliberate", ""))[0]

    async def chat(self, message: str, mode: str = "deliberate"):
        """Send message to JEBAT and get response"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json={
                        "message": message,
                        "user_id": self.user_id,
                        "mode": mode,
                        "timeout": 30,
                    },
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "response": data.get("response", ""),
                            "confidence": data.get("confidence", 0),
                            "duration": data.get("execution_time", 0),
                        }
                    else:
                        return {"error": f"API status: {response.status}"}

        except aiohttp.ClientError as e:
            return {"error": f"Connection error: {e}"}
        except Exception as e:
            return {"error": f"Error: {e}"}

    async def run(self):
        """Main chatbot loop"""
        self.print_header()
        current_mode = "deliberate"

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Handle commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n🗡️  Goodbye! Have a great day! 👋\n")
                    break

                if user_input.lower() == "history":
                    self.show_history()
                    continue

                if user_input.lower() == "mode":
                    current_mode = self.select_mode()
                    print(f"\n✅ Thinking mode set to: {current_mode}\n")
                    continue

                if not user_input:
                    continue

                # Get response from JEBAT
                print("\n⏳ Thinking...\n")
                result = await self.chat(user_input, current_mode)

                if "error" in result:
                    print(f"\n❌ {result['error']}\n")
                    continue

                # Display response
                self.print_response(
                    result["response"], result["confidence"], result["duration"]
                )

                # Save to history
                self.conversation_history.append((user_input, result["response"]))

            except KeyboardInterrupt:
                print("\n\n🗡️  Interrupted. Goodbye! 👋\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


async def main():
    """Main entry point"""
    if not SDK_AVAILABLE:
        print("❌ Please install required packages:")
        print("   pip install aiohttp\n")
        return

    if not RICH_AVAILABLE:
        print("💡 Tip: Install 'rich' for better output:")
        print("   pip install rich\n")

    bot = InteractiveChatbot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
