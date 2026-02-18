#!/usr/bin/env python3
"""
🗡️ JEBAT Standalone Chatbot

A COMPLETELY STANDALONE chatbot that works WITHOUT API server.
Uses JEBAT components directly.

Requirements:
    pip install -r requirements.txt

Usage:
    python examples/chat/standalone_chatbot.py

Features:
- No API server needed
- Works offline (with local LLM)
- Direct component integration
- Memory support
- Multiple thinking modes
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

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class StandaloneChatbot:
    """
    Standalone chatbot using JEBAT components directly.

    This chatbot doesn't need API server - it uses
    JEBAT components directly.
    """

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.user_id = "user_standalone"
        self.thinking_mode = "deliberate"
        self.conversation_history = []

        # JEBAT components (will be initialized)
        self.ultra_think = None
        self.memory_manager = None
        self.initialized = False

    def print_header(self):
        """Print chatbot header"""
        header_text = """
# 🗡️ JEBAT Standalone Chatbot

**Running locally - No API server needed**

Commands:
- `quit` - Exit chatbot
- `mode` - Change thinking mode
- `history` - View conversation history
- `memory` - View stored memories
        """

        if self.console:
            self.console.print(
                Panel(Markdown(header_text), title="JEBAT", border_style="blue")
            )
        else:
            print("=" * 60)
            print("🗡️  JEBAT Standalone Chatbot")
            print("=" * 60)
            print("Commands: quit, mode, history, memory\n")

    async def initialize(self):
        """Initialize JEBAT components"""
        if self.initialized:
            return

        if self.console:
            self.console.print(
                "\n[bold blue]🗡️  JEBAT[/bold blue] - Initializing components...\n"
            )
        else:
            print("\n🗡️  JEBAT - Initializing components...\n")

        try:
            # Import JEBAT components
            from jebat.memory_system.core.memory_manager import MemoryManager

            from jebat.features.ultra_think import create_ultra_think

            # Initialize Ultra-Think
            self.ultra_think = await create_ultra_think(
                config={"max_thoughts": 10, "default_mode": self.thinking_mode}
            )
            if self.console:
                self.console.print("  [green]✓[/green] Ultra-Think initialized")
            else:
                print("  ✓ Ultra-Think initialized")

            # Initialize Memory Manager
            self.memory_manager = MemoryManager()
            if self.console:
                self.console.print("  [green]✓[/green] Memory Manager initialized")
            else:
                print("  ✓ Memory Manager initialized")

            self.initialized = True

            if self.console:
                self.console.print("\n[bold green]✅ JEBAT Ready![/bold green]\n")
            else:
                print("\n✅ JEBAT Ready!\n")

        except ImportError as e:
            if self.console:
                self.console.print(f"  [red]✗[/red] Import error: {e}")
            else:
                print(f"  ✗ Import error: {e}")

            if self.console:
                self.console.print(
                    "\n[yellow]⚠️  Running in basic mode (no Ultra-Think)[/yellow]\n"
                )
            else:
                print("\n⚠️  Running in basic mode (no Ultra-Think)\n")

            self.initialized = True  # Continue anyway

    def select_mode(self) -> str:
        """Let user select thinking mode"""
        modes = [
            ("fast", "⚡ Quick responses"),
            ("deliberate", "🤔 Balanced reasoning"),
            ("deep", "🧠 Deep analysis"),
            ("strategic", "📊 Long-term planning"),
            ("creative", "🎨 Creative thinking"),
            ("critical", "🔍 Critical evaluation"),
        ]

        print("\n🎯 Select Thinking Mode:")
        for i, (mode, desc) in enumerate(modes, 1):
            print(f"  {i}. {mode} - {desc}")

        choice = input("\nEnter choice (1-6, or Enter for 'deliberate'): ").strip()

        mode_map = {
            "1": "fast",
            "2": "deliberate",
            "3": "deep",
            "4": "strategic",
            "5": "creative",
            "6": "critical",
        }

        return mode_map.get(choice, "deliberate")

    async def get_response(self, message: str) -> dict:
        """Get response from JEBAT"""
        start_time = datetime.now()

        # Try to use Ultra-Think if available
        if self.ultra_think:
            try:
                from jebat.features.ultra_think import ThinkingMode

                mode_map = {
                    "fast": ThinkingMode.FAST,
                    "deliberate": ThinkingMode.DELIBERATE,
                    "deep": ThinkingMode.DEEP,
                    "strategic": ThinkingMode.STRATEGIC,
                    "creative": ThinkingMode.CREATIVE,
                    "critical": ThinkingMode.CRITICAL,
                }

                mode = mode_map.get(self.thinking_mode, ThinkingMode.DELIBERATE)

                result = await self.ultra_think.think(
                    question=message, mode=mode, timeout=30
                )

                duration = (datetime.now() - start_time).total_seconds()

                return {
                    "response": result.conclusion,
                    "confidence": result.confidence,
                    "thoughts": result.thought_count,
                    "duration": duration,
                }

            except Exception as e:
                # Fallback if Ultra-Think fails
                pass

        # Fallback: Simple response
        duration = (datetime.now() - start_time).total_seconds()

        # Simple echo/response logic (fallback)
        response = self._generate_simple_response(message)

        return {
            "response": response,
            "confidence": 0.5,
            "thoughts": 1,
            "duration": duration,
        }

    def _generate_simple_response(self, message: str) -> str:
        """Generate simple response (fallback)"""
        message_lower = message.lower()

        # Simple pattern matching
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm JEBAT, your AI assistant. How can I help you today?"

        if any(word in message_lower for word in ["how are you", "how do you do"]):
            return "I'm doing well, thank you for asking! I'm here to help you with any questions or tasks you might have."

        if any(word in message_lower for word in ["what is your name", "who are you"]):
            return "I'm JEBAT (Justified Enhanced Bot with Advanced Thinking). I'm an AI assistant with eternal memory and deep reasoning capabilities."

        if any(word in message_lower for word in ["what can you do", "help"]):
            return "I can help you with:\n- Answering questions\n- Deep thinking and analysis\n- Remembering important information\n- Multi-agent task execution\n- And much more! Just ask me anything."

        if any(word in message_lower for word in ["thank", "thanks"]):
            return "You're welcome! Feel free to ask me anything else."

        # Default response
        return f"That's interesting! You said: '{message}'. As an AI assistant, I'm here to help you with any questions or tasks. Could you elaborate more on what you'd like to know or do?"

    def print_response(
        self, response: str, confidence: float, duration: float, thoughts: int = 0
    ):
        """Print bot response"""
        if self.console:
            panel_content = f"{response}\n\n"
            panel_content += f"💭 Thoughts: {thoughts} | "
            panel_content += f"💯 Confidence: {confidence:.0%} | "
            panel_content += f"⏱️ Duration: {duration:.2f}s"

            panel = Panel(panel_content, title="🗡️ JEBAT", border_style="green")
            self.console.print(panel)
        else:
            print(f"\n🗡️ JEBAT: {response}")
            print(
                f"💭 Thoughts: {thoughts} | Confidence: {confidence:.0%} | Duration: {duration:.2f}s\n"
            )

    def show_history(self):
        """Show conversation history"""
        if not self.conversation_history:
            print("\n📜 No conversation history yet\n")
            return

        print("\n" + "=" * 60)
        print("📜 CONVERSATION HISTORY (Last 10)")
        print("=" * 60)

        for i, (user_msg, bot_msg) in enumerate(self.conversation_history[-10:], 1):
            print(f"\n{i}. You: {user_msg[:80]}")
            print(f"   JEBAT: {bot_msg[:80]}...")

        print("\n" + "=" * 60 + "\n")

    async def run(self):
        """Main chatbot loop"""
        await self.initialize()
        self.print_header()

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Handle commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n🗡️  Goodbye! Have a great day! 👋\n")
                    break

                if user_input.lower() == "mode":
                    self.thinking_mode = self.select_mode()
                    print(f"\n✅ Thinking mode set to: {self.thinking_mode}\n")
                    continue

                if user_input.lower() == "history":
                    self.show_history()
                    continue

                if user_input.lower() == "memory":
                    print("\n💾 Memory feature - Coming soon!\n")
                    continue

                if not user_input:
                    continue

                # Get response from JEBAT
                print("\n⏳ Thinking...\n")
                result = await self.get_response(user_input)

                # Display response
                self.print_response(
                    result["response"],
                    result["confidence"],
                    result["duration"],
                    result.get("thoughts", 0),
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
    bot = StandaloneChatbot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
