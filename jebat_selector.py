"""
🗡️ JEBAT Product Selector

Interactive menu to select and launch different JEBAT variants.
OpenClaw-style interface with rich UI.

Variants:
- JEBAT Core (Main Platform)
- JEBAT Security (AI Pentest)
- JEBAT Dev (Development Assistant)
- JEBAT Companion (Chat Assistant)
- JEBAT Nexus (Bot/Orchestration)
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Rich UI
try:
    from rich.box import DOUBLE, ROUNDED
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import IntPrompt, Prompt
    from rich.style import Style
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ==================== Product Definitions ====================

PRODUCTS = [
    {
        "id": 1,
        "name": "JEBAT Core",
        "codename": "Hang Jebat",
        "type": "platform",
        "description": "Main JEBAT AI Platform with Ultra-Think, Ultra-Loop, and Memory System",
        "module": "jebat",
        "entry": "jebat.core",
        "icon": "🗡️",
        "status": "active",
        "version": "2.0.0",
        "features": [
            "5-Layer Eternal Memory",
            "Ultra-Think Reasoning",
            "Ultra-Loop Processing",
            "Multi-Agent Orchestration",
            "Sentinel Security",
        ],
        "use_cases": [
            "General AI tasks",
            "Complex reasoning",
            "Memory-intensive operations",
            "Multi-agent coordination",
        ],
    },
    {
        "id": 2,
        "name": "JEBAT Security",
        "codename": "Keris",  # Traditional Malay dagger - symbolic of protection
        "type": "security",
        "description": "AI-Powered Penetration Testing & Security Assessment",
        "module": "jebat_security",
        "entry": "jebat_security.cli",
        "icon": "🛡️",
        "status": "coming_soon",
        "version": "1.0.0-dev",
        "features": [
            "Vulnerability Scanning",
            "Exploit Generation",
            "Security Auditing",
            "Threat Detection",
            "Compliance Checking",
        ],
        "use_cases": [
            "Penetration testing",
            "Security assessments",
            "Vulnerability analysis",
            "Red team operations",
        ],
    },
    {
        "id": 3,
        "name": "JEBAT Dev",
        "codename": "Pandai",  # Malay for "clever/smart"
        "type": "development",
        "description": "Interactive Development Assistant with Code Generation & Review",
        "module": "jebat_dev",
        "entry": "jebat_dev.gateway.interactive_cli",
        "icon": "💻",
        "status": "active",
        "version": "1.0.0",
        "features": [
            "Code Generation",
            "Code Review",
            "Project Scaffolding",
            "Git Integration",
            "Test Running",
            "Debug Analysis",
        ],
        "use_cases": [
            "Software development",
            "Code review",
            "Project creation",
            "Debugging",
        ],
    },
    {
        "id": 4,
        "name": "JEBAT Companion",
        "codename": "Sahabat",  # Malay for "friend/companion"
        "type": "chat",
        "description": "Conversational AI Assistant for Daily Tasks & Communication",
        "module": "jebat_companion",
        "entry": "jebat_companion.cli",
        "icon": "🤖",
        "status": "planned",
        "version": "0.1.0-planning",
        "features": [
            "Natural Conversation",
            "Task Management",
            "Schedule Integration",
            "Email Assistance",
            "Research Help",
        ],
        "use_cases": [
            "Daily assistance",
            "Communication",
            "Task management",
            "Information retrieval",
        ],
    },
    {
        "id": 5,
        "name": "JEBAT Nexus",
        "codename": "Perisai",  # Malay for "shield" - protects and connects
        "type": "bot",
        "description": "OpenClaw-Style Bot Orchestrator for Multi-Channel Deployment",
        "module": "jebat_nexus",
        "entry": "jebat_nexus.bot",
        "icon": "🔗",
        "status": "planned",
        "version": "0.1.0-planning",
        "features": [
            "Multi-Channel Support",
            "Bot Orchestration",
            "Plugin System",
            "Event-Driven Architecture",
            "Real-Time Processing",
        ],
        "use_cases": [
            "Discord bot",
            "Telegram bot",
            "Slack integration",
            "WhatsApp assistant",
            "Custom deployments",
        ],
    },
]


# ==================== Selector Class ====================


class ProductSelector:
    """
    Interactive product selector with OpenClaw-style UI.
    """

    BANNER = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         🗡️  J E B A T   P L A T F O R M  🗡️              ║
    ║                                                           ║
    ║    Select Your AI Assistant                               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """

    def __init__(self):
        """Initialize product selector."""
        self.console = Console() if RICH_AVAILABLE else None
        self.selected_product: Optional[Dict] = None

    def print_banner(self):
        """Print welcome banner."""
        if self.console:
            self.console.print(
                Panel(
                    Text(self.BANNER, style="bold cyan"),
                    border_style="green",
                    padding=(1, 2),
                )
            )
        else:
            print(self.BANNER)

    def print_product_table(self):
        """Display all products in a table."""
        if not self.console:
            # Plain text fallback
            print("\nAvailable Products:\n")
            for p in PRODUCTS:
                status_icon = "✓" if p["status"] == "active" else "○"
                print(f"  [{p['id']}] {p['icon']} {p['name']} ({p['codename']})")
                print(f"      {p['description']}")
                print(f"      Status: {p['status']} | Version: {p['version']}")
                print()
            return

        table = Table(
            title="🗡️ JEBAT Product Family",
            box=ROUNDED,
            border_style="green",
            title_style="bold cyan",
        )

        table.add_column("ID", style="yellow", width=4, justify="center")
        table.add_column("Product", style="cyan", width=20)
        table.add_column("Codename", style="magenta", width=12)
        table.add_column("Type", style="blue", width=12)
        table.add_column("Status", style="green", width=12)
        table.add_column("Description", style="white", width=50)

        for p in PRODUCTS:
            status_style = {
                "active": "[green]✓ Active[/green]",
                "coming_soon": "[yellow]⏳ Soon[/yellow]",
                "planned": "[blue]○ Planned[/blue]",
            }.get(p["status"], p["status"])

            table.add_row(
                str(p["id"]),
                f"{p['icon']} {p['name']}",
                p["codename"],
                p["type"],
                status_style,
                p["description"][:48] + "..."
                if len(p["description"]) > 50
                else p["description"],
            )

        self.console.print(table)

    def print_product_details(self, product: Dict):
        """Print detailed information about a product."""
        if not self.console:
            print(f"\n{product['icon']} {product['name']} ({product['codename']})")
            print(f"    Version: {product['version']}")
            print(f"    Status: {product['status']}")
            print(f"\n    Description: {product['description']}")
            print(f"\n    Features:")
            for f in product["features"]:
                print(f"      • {f}")
            print(f"\n    Use Cases:")
            for u in product["use_cases"]:
                print(f"      • {u}")
            return

        self.console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        self.console.print(
            f"[bold green]{product['icon']} {product['name']}[/bold green] [magenta]({product['codename']})[/magenta]"
        )
        self.console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

        # Info panel
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Key", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("Version", product["version"])
        info_table.add_row("Status", product["status"])
        info_table.add_row("Module", product["module"])
        info_table.add_row("Entry Point", product["entry"])

        self.console.print(info_table)

        # Features
        self.console.print(f"\n[bold yellow]📌 Features:[/bold yellow]")
        for feature in product["features"]:
            self.console.print(f"  [green]✓[/green] {feature}")

        # Use Cases
        self.console.print(f"\n[bold yellow]🎯 Use Cases:[/bold yellow]")
        for use in product["use_cases"]:
            self.console.print(f"  [cyan]•[/cyan] {use}")

        self.console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]\n")

    def select_product(self) -> Optional[Dict]:
        """
        Let user select a product.

        Returns:
            Selected product dict or None
        """
        self.print_banner()
        self.print_product_table()

        if not self.console:
            try:
                choice = input("\nEnter product ID (1-5) or 'q' to quit: ").strip()
            except EOFError:
                return None
        else:
            choice = Prompt.ask(
                "\n[bold yellow]Select Product[/bold yellow]",
                choices=[str(i) for i in range(1, len(PRODUCTS) + 1)] + ["q"],
                default="1",
            )

        if choice.lower() == "q":
            return None

        try:
            product_id = int(choice)
            if 1 <= product_id <= len(PRODUCTS):
                self.selected_product = PRODUCTS[product_id - 1]
                self.print_product_details(self.selected_product)
                return self.selected_product
            else:
                print(f"Invalid ID: {product_id}")
                return None
        except ValueError:
            print(f"Invalid input: {choice}")
            return None

    def launch_product(self, product: Dict) -> bool:
        """
        Launch the selected product.

        Args:
            product: Product dict to launch

        Returns:
            True if launched successfully
        """
        if product["status"] == "planned":
            if self.console:
                self.console.print(
                    f"\n[yellow]⚠️  {product['name']} is in planning phase.[/yellow]"
                )
                self.console.print(
                    "[yellow]   This product is not yet available.[/yellow]\n"
                )
            else:
                print(
                    f"\n⚠️  {product['name']} is in planning phase. Not yet available.\n"
                )
            return False

        if product["status"] == "coming_soon":
            if self.console:
                self.console.print(
                    f"\n[yellow]⏳ {product['name']} is coming soon![/yellow]"
                )
                self.console.print(
                    "[yellow]   Check back later for updates.[/yellow]\n"
                )
            else:
                print(f"\n⏳ {product['name']} is coming soon! Check back later.\n")
            return False

        # Active product - launch it
        if self.console:
            self.console.print(
                f"\n[bold green]🚀 Launching {product['name']}...[/bold green]\n"
            )

        try:
            # Import and run the entry point
            module_name = product["entry"].rsplit(".", 1)[0]
            module = __import__(module_name, fromlist=[""])

            if hasattr(module, "main"):
                module.main()
                return True
            else:
                if self.console:
                    self.console.print(
                        f"[red]Error: No main() function in {module_name}[/red]"
                    )
                else:
                    print(f"Error: No main() function in {module_name}")
                return False

        except ImportError as e:
            if self.console:
                self.console.print(
                    f"[red]Error: Could not import {product['module']}[/red]"
                )
                self.console.print(f"[dim]{str(e)}[/dim]")
            else:
                print(f"Error: Could not import {product['module']}")
                print(f"  {str(e)}")
            return False
        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error launching {product['name']}[/red]")
                self.console.print(f"[dim]{str(e)}[/dim]")
            else:
                print(f"Error launching {product['name']}: {str(e)}")
            return False

    def run(self):
        """Run the product selector loop."""
        while True:
            product = self.select_product()

            if product is None:
                if self.console:
                    self.console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")
                else:
                    print("\n👋 Goodbye!")
                break

            # Confirm launch
            if self.console:
                from rich.prompt import Confirm

                if Confirm.ask(f"\nLaunch [green]{product['name']}[/green]?"):
                    self.launch_product(product)
            else:
                confirm = input(f"\nLaunch {product['name']}? (y/n): ").strip().lower()
                if confirm == "y":
                    self.launch_product(product)

            # Return to selection
            if self.console:
                from rich.prompt import Prompt

                if (
                    not Prompt.ask("\nContinue?", choices=["y", "n"], default="y")
                    == "y"
                ):
                    break


# ==================== Main Entry Point ====================


def main():
    """Main entry point for product selector."""
    selector = ProductSelector()

    try:
        selector.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
