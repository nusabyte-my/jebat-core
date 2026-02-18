#!/usr/bin/env python3
"""
JEBAT CLI - Command Line Interface

Control JEBAT AI Assistant from the command line.

Usage:
    jebat status              - Show system status
    jebat loop start          - Start Ultra-Loop
    jebat loop stop           - Stop Ultra-Loop
    jebat loop status         - Show Ultra-Loop status
    jebat think <question>    - Run thinking session
    jebat memory store <text> - Store a memory
    jebat memory search <q>   - Search memories
    jebat config              - Show configuration
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

# Rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better CLI output: pip install rich")


class JEBATCLI:
    """JEBAT Command Line Interface"""

    def __init__(self):
        """Initialize CLI"""
        self.console = Console() if RICH_AVAILABLE else None
        self.ultra_loop = None
        self.ultra_think = None
        self.memory_manager = None
        self.initialized = False

    def print(self, message: str, style: str = ""):
        """Print message with optional style"""
        if self.console:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)

    async def initialize(self):
        """Initialize JEBAT systems"""
        if self.initialized:
            return

        self.print("\nJEBAT  JEBAT - Initializing systems...", "bold blue")

        try:
            # Import JEBAT components
            from jebat import MemoryManager
            from jebat.features.ultra_loop import create_ultra_loop
            from jebat.features.ultra_think import create_ultra_think

            # Initialize Memory Manager
            self.memory_manager = MemoryManager()
            self.print("  [OK] Memory Manager", "green")

            # Initialize Ultra-Loop
            self.ultra_loop = await create_ultra_loop(
                config={"cycle_interval": 1.0, "max_cycles": 0},
                enable_db_persistence=False,
            )
            self.print("  [OK] Ultra-Loop", "green")

            # Initialize Ultra-Think
            self.ultra_think = await create_ultra_think(
                config={"max_thoughts": 20, "default_mode": "deliberate"},
                memory_manager=self.memory_manager,
                enable_db_persistence=False,
                enable_memory_integration=True,
            )
            self.print("  [OK] Ultra-Think", "green")

            self.initialized = True
            self.print("[OK] All systems initialized\n", "bold green")

        except Exception as e:
            self.print(f"[ERR] Initialization failed: {e}\n", "bold red")
            raise

    async def cmd_status(self):
        """Show system status"""
        await self.initialize()

        self.print("\n" + "=" * 60, "bold blue")
        self.print("JEBAT  JEBAT System Status", "bold blue")
        self.print("=" * 60 + "\n", "bold blue")

        # System components status
        status_table = self._create_table("Component", "Status")
        status_table.add_row(
            "Memory Manager", "[OK] Connected" if self.memory_manager else "[ERR] Disconnected"
        )
        status_table.add_row(
            "Ultra-Loop", "[OK] Ready" if self.ultra_loop else "[ERR] Not initialized"
        )
        status_table.add_row(
            "Ultra-Think", "[OK] Ready" if self.ultra_think else "[ERR] Not initialized"
        )

        self.print(status_table)

        # Ultra-Loop metrics
        if self.ultra_loop:
            metrics = self.ultra_loop.get_metrics()
            self.print("\n Ultra-Loop Metrics:", "bold")
            self.print(f"  Total Cycles: {metrics.get('total_cycles', 0)}")
            self.print(f"  Successful: {metrics.get('successful_cycles', 0)}")
            self.print(f"  Failed: {metrics.get('failed_cycles', 0)}")
            success_rate = (
                metrics.get("successful_cycles", 0)
                / max(metrics.get("total_cycles", 1), 1)
                * 100
            )
            self.print(f"  Success Rate: {success_rate:.1f}%")

        # Ultra-Think stats
        if self.ultra_think:
            stats = self.ultra_think.get_stats()
            self.print("\n Ultra-Think Statistics:", "bold")
            self.print(f"  Total Sessions: {stats.get('total_sessions', 0)}")
            self.print(f"  Total Thoughts: {stats.get('total_thoughts', 0)}")
            avg_thoughts = stats.get("avg_thoughts_per_session", 0)
            self.print(f"  Avg Thoughts/Session: {avg_thoughts:.1f}")

        self.print("\n" + "=" * 60 + "\n", "bold blue")

    async def cmd_loop_start(self, cycles: int = 0):
        """Start Ultra-Loop"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        self.print("\n Starting Ultra-Loop...", "bold blue")

        if cycles > 0:
            self.ultra_loop.max_cycles = cycles
            self.print(f"  Will run for {cycles} cycles", "yellow")

        await self.ultra_loop.start()
        self.print("[OK] Ultra-Loop started", "green")

        if cycles > 0:
            # Wait for cycles to complete
            import time

            start = time.time()
            while self.ultra_loop._current_cycle < cycles:
                await asyncio.sleep(0.1)
            elapsed = time.time() - start
            self.print(f"  Completed {cycles} cycles in {elapsed:.2f}s", "green")

    async def cmd_loop_stop(self):
        """Stop Ultra-Loop"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        self.print("\n  Stopping Ultra-Loop...", "bold blue")
        await self.ultra_loop.stop()
        self.print("[OK] Ultra-Loop stopped", "green")

    async def cmd_loop_status(self):
        """Show Ultra-Loop status"""
        await self.initialize()

        if not self.ultra_loop:
            self.print("[ERR] Ultra-Loop not initialized", "red")
            return

        status = self.ultra_loop.get_status()

        self.print("\n Ultra-Loop Status:", "bold blue")
        self.print(f"  Running: {status['is_running']}")
        self.print(f"  Current Cycle: {status['current_cycle']}")
        self.print(f"  Cycle Interval: {status['cycle_interval']}s")
        self.print(
            f"  Max Cycles: {status['max_cycles'] if status['max_cycles'] > 0 else 'Unlimited'}"
        )

    async def cmd_think(self, question: str, mode: str = "deliberate"):
        """Run thinking session"""
        await self.initialize()

        if not self.ultra_think:
            self.print("[ERR] Ultra-Think not initialized", "red")
            return

        self.print(f"\n Thinking about: {question[:80]}...", "bold blue")
        self.print(f"  Mode: {mode}", "yellow")

        from jebat.features.ultra_think import ThinkingMode

        try:
            thinking_mode = ThinkingMode(mode.lower())
        except ValueError:
            thinking_mode = ThinkingMode.DELIBERATE
            self.print(
                f"  Note: Using DELIBERATE mode (unknown mode: {mode})", "yellow"
            )

        result = await self.ultra_think.think(
            problem=question,
            mode=thinking_mode,
            timeout=30,
        )

        self.print("\n Conclusion:", "bold green")
        self.print(f"  {result.conclusion}", "white")
        self.print(f"\n  Confidence: {result.confidence:.1%}", "cyan")
        self.print(f"  Thinking Steps: {len(result.reasoning_steps)}", "cyan")
        self.print(f"  Execution Time: {result.execution_time:.2f}s", "cyan")

    async def cmd_memory_store(self, text: str):
        """Store a memory"""
        await self.initialize()

        if not self.memory_manager:
            self.print("[ERR] Memory Manager not initialized", "red")
            return

        self.print(f"\n Storing memory: {text[:80]}...", "bold blue")

        from jebat.core.memory.layers import MemoryLayer

        memory_id = await self.memory_manager.store(
            content=text,
            layer=MemoryLayer.M1_EPISODIC,
            user_id="cli_user",
        )

        self.print(f"[OK] Memory stored with ID: {memory_id}", "green")

    async def cmd_memory_search(self, query: str):
        """Search memories"""
        await self.initialize()

        if not self.memory_manager:
            self.print("[ERR] Memory Manager not initialized", "red")
            return

        self.print(f"\n Searching memories: {query}...", "bold blue")

        memories = self.memory_manager.search(
            query=query,
            user_id="cli_user",
            limit=10,
        )

        if memories:
            self.print(f"\n[OK] Found {len(memories)} memories:", "green")
            for i, memory in enumerate(memories[:5], 1):
                content = (
                    memory.content[:100]
                    if hasattr(memory, "content")
                    else str(memory)[:100]
                )
                self.print(f"  {i}. {content}...")
        else:
            self.print("  No memories found", "yellow")

    async def cmd_config(self):
        """Show configuration"""
        self.print("\n  JEBAT Configuration:", "bold blue")

        config = {
            "ultra_loop": {
                "cycle_interval": "1.0s",
                "max_cycles": "0 (unlimited)",
            },
            "ultra_think": {
                "max_thoughts": "20",
                "default_mode": "deliberate",
                "memory_integration": "enabled",
            },
            "memory": {
                "layers": "5 (M0-M4)",
                "consolidation": "automatic",
            },
        }

        for section, settings in config.items():
            self.print(f"\n  {section.upper()}:", "bold cyan")
            for key, value in settings.items():
                self.print(f"    {key}: {value}")

    def _create_table(self, *columns):
        """Create a table (Rich or fallback)"""
        if self.console:
            table = Table(show_header=True, header_style="bold")
            for col in columns:
                table.add_column(col)
            return table
        else:
            # Simple text table
            class SimpleTable:
                def __init__(self, *cols):
                    self.rows = []
                    self.cols = cols

                def add_row(self, *row):
                    self.rows.append(row)

                def __str__(self):
                    lines = [" | ".join(self.cols)]
                    lines.append("-" * len(lines[0]))
                    for row in self.rows:
                        lines.append(" | ".join(str(x) for x in row))
                    return "\n".join(lines)

            return SimpleTable(*columns)


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="JEBAT  JEBAT - AI Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Loop commands
    loop_parser = subparsers.add_parser("loop", help="Ultra-Loop control")
    loop_subparsers = loop_parser.add_subparsers(dest="loop_command")
    loop_subparsers.add_parser("start", help="Start Ultra-Loop")
    loop_subparsers.add_parser("stop", help="Stop Ultra-Loop")
    loop_subparsers.add_parser("status", help="Show Ultra-Loop status")

    # Think command
    think_parser = subparsers.add_parser("think", help="Run thinking session")
    think_parser.add_argument("question", help="Question to think about")
    think_parser.add_argument(
        "--mode",
        default="deliberate",
        help="Thinking mode (fast, deliberate, deep, strategic, creative, critical)",
    )

    # Memory commands
    memory_parser = subparsers.add_parser("memory", help="Memory operations")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_store = memory_subparsers.add_parser("store", help="Store a memory")
    memory_store.add_argument("text", help="Memory text")

    memory_search = memory_subparsers.add_parser("search", help="Search memories")
    memory_search.add_argument("query", help="Search query")

    # Config command
    subparsers.add_parser("config", help="Show configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    cli = JEBATCLI()

    try:
        if args.command == "status":
            await cli.cmd_status()

        elif args.command == "loop":
            if args.loop_command == "start":
                await cli.cmd_loop_start()
            elif args.loop_command == "stop":
                await cli.cmd_loop_stop()
            elif args.loop_command == "status":
                await cli.cmd_loop_status()
            else:
                loop_parser.print_help()

        elif args.command == "think":
            await cli.cmd_think(args.question, args.mode)

        elif args.command == "memory":
            if args.memory_command == "store":
                await cli.cmd_memory_store(args.text)
            elif args.memory_command == "search":
                await cli.cmd_memory_search(args.query)
            else:
                memory_parser.print_help()

        elif args.command == "config":
            await cli.cmd_config()

        else:
            parser.print_help()

        return 0

    except KeyboardInterrupt:
        cli.print("\n\n⚠️  Interrupted by user", "yellow")
        return 130

    except Exception as e:
        cli.print(f"\n[ERR] Error: {e}\n", "bold red")
        if cli.console:
            cli.console.print_exception()
        return 1

    finally:
        # Cleanup
        if cli.ultra_loop and cli.ultra_loop._is_running:
            await cli.ultra_loop.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
