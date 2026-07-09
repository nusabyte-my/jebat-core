"""
CLI module for JEBAT SDK.

Provides command-line interface for common operations.
"""

import sys
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .client import JebatClient
from .async_client import AsyncJebatClient
from .models import *

app = typer.Typer(help="JEBAT SDK CLI")
console = Console()


@app.command()
def login(
    username: str = typer.Argument(..., help="Username"),
    password: str = typer.Argument(..., help="Password"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u", help="API base URL"),
):
    """Authenticate and show tokens."""
    client = JebatClient(base_url=url)
    try:
        token = client.login(username, password)
        console.print(f"[green]Login successful![/green]")
        console.print(f"Access Token: {token.access_token[:20]}...")
        console.print(f"Refresh Token: {token.refresh_token[:20]}...")
        console.print(f"Expires in: {token.expires_in}s")
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send"),
    mode: str = typer.Option("deliberate", "--mode", "-m", help="Thinking mode"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t", help="Access token"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream response"),
):
    """Send a chat message."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        if stream:
            console.print("[bold blue]Streaming response:[/bold blue]")
            for chunk in client.chat_stream(message, mode=mode):
                if chunk.type == "content":
                    console.print(chunk.content, end="")
                elif chunk.type == "error":
                    console.print(f"[red]Error: {chunk.content}[/red]")
                    break
            console.print()
        else:
            response = client.chat(message, mode=mode)
            console.print(f"[bold green]Response:[/bold green] {response.response}")
            console.print(f"Confidence: {response.confidence:.1%}")
            console.print(f"Thinking steps: {response.thinking_steps}")
            console.print(f"Time: {response.execution_time:.2f}s")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def memories(
    query: str = typer.Argument(None, help="Search query"),
    layer: str = typer.Option(None, "--layer", "-l", help="Memory layer"),
    limit: int = typer.Option(20, "--limit", "-l"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t"),
):
    """List or search memories."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        if query:
            result = client.search_memories(query, limit=limit)
        else:
            result = client.list_memories(limit=limit)

        table = Table(title=f"Memories ({result.total} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Layer", style="green")
        table.add_column("Content", style="white", max_width=60)
        table.add_column("Heat", style="yellow")

        for mem in result.memories:
            table.add_row(
                mem.id[:8],
                mem.layer,
                mem.content[:57] + "..." if len(mem.content) > 60 else mem.content,
                f"{mem.heat_score:.0%}",
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def agents(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t"),
):
    """List agents."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        result = client.list_agents()
        table = Table(title=f"Agents ({result.total} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Capabilities", style="white")

        for agent in result.agents:
            capabilities = ", ".join(agent.capabilities[:3])
            if len(agent.capabilities) > 3:
                capabilities += f" +{len(agent.capabilities)-3}"
            table.add_row(agent.id, agent.name, agent.type, agent.status, capabilities)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def health(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
):
    """Check API health."""
    client = JebatClient(base_url=url)
    try:
        result = client.get_health()
        status = "[green]Healthy[/green]" if result.healthy else "[red]Unhealthy[/red]"
        console.print(f"Status: {status}")
        console.print(f"Database: {'[green]OK[/green]' if result.database else '[red]FAIL[/red]'}")
        console.print(f"Redis: {'[green]OK[/green]' if result.redis else '[red]FAIL[/red]'}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def swarm(
    task: str = typer.Argument(..., help="Task description"),
    mode: str = typer.Option("consensus", "--mode", "-m"),
    max_agents: int = typer.Option(5, "--max-agents", "-a"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t"),
):
    """Execute a swarm task."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        console.print("[bold blue]Executing swarm task...[/bold blue]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_id = progress.add_task("Executing swarm...", total=None)
            result = client.execute_swarm(
                description=task,
                execution_mode=mode,
                max_agents=max_agents,
            )
            progress.update(task_id, completed=True)

        console.print(f"[green]Task completed![/green]")
        console.print(f"Task ID: {result.task_id}")
        console.print(f"Success: {result.success}")
        console.print(f"Time: {result.execution_time:.2f}s")
        if result.result:
            console.print(f"\nResult: {result.result}")
        if result.error:
            console.print(f"[red]Error: {result.error}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def apikey_create(
    name: str = typer.Argument(..., help="API key name"),
    expires: int = typer.Option(None, "--expires", "-e", help="Expiry in days"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t"),
):
    """Create a new API key."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        result = client.create_api_key(name, expires_in_days=expires)
        console.print(f"[green]API Key created![/green]")
        console.print(f"Key: {result.key}")
        console.print(f"Prefix: {result.prefix}")
        console.print(f"ID: {result.id}")
        console.print(f"Expires: {result.expires_at or 'Never'}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


@app.command()
def apikey_list(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t"),
):
    """List API keys."""
    client = JebatClient(base_url=url)
    if token:
        client.set_token(token)
    try:
        keys = client.list_api_keys()
        table = Table(title="API Keys")
        table.add_column("Name", style="green")
        table.add_column("Prefix", style="cyan")
        table.add_column("Active", style="yellow")
        table.add_column("Last Used", style="blue")
        table.add_column("Expires", style="magenta")

        for key in keys:
            table.add_row(
                key.name,
                key.prefix,
                "Yes" if key.is_active else "No",
                key.last_used or "Never",
                key.expires_at or "Never",
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        client.close()


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()