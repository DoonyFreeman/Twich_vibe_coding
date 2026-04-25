"""Main CLI entry point for Vibe Coding."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from vibe_coding.config import get_config, get_twitch_nick, get_twitch_oauth
from vibe_coding.db.models import IdeaStatus
from vibe_coding.db.repository import IdeaRepository

app = typer.Typer(
    name="vibe",
    help="Vibe Coding - Twitch Vibe Coding CLI",
    add_completion=False,
)
console = Console()
log = logging.getLogger(__name__)


def get_db_path() -> Path:
    """Get database path from config."""
    config = get_config()
    return Path(config["database"]["path"])


@app.command()
def ideas(
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status (pending/approved/rejected)"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of ideas to show"
    ),
) -> None:
    """List all ideas with optional status filter."""
    asyncio.run(_list_ideas(status, limit))


async def _list_ideas(status_filter: Optional[str], limit: int) -> None:
    """Async implementation of list ideas command.

    Args:
        status_filter: Optional status to filter by.
        limit: Maximum number of ideas to show.
    """
    repo = IdeaRepository(get_db_path())
    await repo.create_tables()

    if status_filter:
        try:
            status = IdeaStatus(status_filter.lower())
            ideas_list = await repo.get_ideas_by_status(status)
        except ValueError:
            console.print(f"[red]Invalid status: {status_filter}[/red]")
            console.print("Valid statuses: pending, approved, rejected, in_progress, completed")
            await repo.close()
            return
    else:
        ideas_list = await repo.get_all_ideas()

    await repo.close()

    if not ideas_list:
        console.print("[yellow]No ideas found.[/yellow]")
        return

    ideas_list = ideas_list[:limit]

    table = Table(title="Ideas")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Complexity", style="magenta", width=10)
    table.add_column("Priority", style="yellow", width=8)
    table.add_column("Status", style="green", width=12)
    table.add_column("Votes", style="blue", width=6)
    table.add_column("Author", style="white", width=15)

    for idea in ideas_list:
        if idea.id:
            table.add_row(
                str(idea.id),
                idea.description[:40],
                idea.complexity.value,
                idea.priority.value,
                idea.status.value,
                str(idea.vote_count),
                idea.author[:15],
            )

    console.print(table)


@app.command()
def approve(
    idea_id: int = typer.Argument(..., help="Idea ID to approve"),
) -> None:
    """Approve an idea by ID."""
    asyncio.run(_approve_idea(idea_id))


async def _approve_idea(idea_id: int) -> None:
    """Async implementation of approve command.

    Args:
        idea_id: ID of idea to approve.
    """
    repo = IdeaRepository(get_db_path())
    await repo.create_tables()

    idea = await repo.get_idea(idea_id)
    if not idea:
        console.print(f"[red]Idea #{idea_id} not found[/red]")
        await repo.close()
        return

    await repo.update_idea_status(idea_id, IdeaStatus.APPROVED)
    console.print(f"[green]Approved idea #{idea_id}: {idea.description}[/green]")
    await repo.close()


@app.command()
def reject(
    idea_id: int = typer.Argument(..., help="Idea ID to reject"),
) -> None:
    """Reject an idea by ID."""
    asyncio.run(_reject_idea(idea_id))


async def _reject_idea(idea_id: int) -> None:
    """Async implementation of reject command.

    Args:
        idea_id: ID of idea to reject.
    """
    repo = IdeaRepository(get_db_path())
    await repo.create_tables()

    idea = await repo.get_idea(idea_id)
    if not idea:
        console.print(f"[red]Idea #{idea_id} not found[/red]")
        await repo.close()
        return

    await repo.update_idea_status(idea_id, IdeaStatus.REJECTED)
    console.print(f"[yellow]Rejected idea #{idea_id}: {idea.description}[/yellow]")
    await repo.close()


@app.command()
def pending(
    threshold: Optional[int] = typer.Option(
        None, "--threshold", "-t", help="Override vote threshold"
    ),
) -> None:
    """Show pending ideas needing approval."""
    asyncio.run(_list_pending(threshold))


async def _list_pending(threshold: Optional[int]) -> None:
    """Async implementation of pending command.

    Args:
        threshold: Optional vote threshold override.
    """
    config = get_config()
    vote_threshold = threshold or config["vibe_coding"]["vote_threshold"]

    repo = IdeaRepository(get_db_path())
    await repo.create_tables()

    pending = await repo.get_ideas_by_status(IdeaStatus.PENDING)
    await repo.close()

    if not pending:
        console.print("[yellow]No pending ideas.[/yellow]")
        return

    table = Table(title=f"Pending Ideas (need {vote_threshold}+ votes)")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Votes", style="blue", width=6)
    table.add_column("Author", style="white", width=15)

    for idea in pending:
        if idea.id:
            needs = vote_threshold - idea.vote_count
            vote_str = f"{idea.vote_count}/{vote_threshold}"
            if idea.vote_count >= vote_threshold:
                vote_str = f"[green]{vote_str}[/green] ✓"
            else:
                vote_str = f"[yellow]{vote_str}[/yellow] (need {needs})"

            table.add_row(
                str(idea.id),
                idea.description[:40],
                vote_str,
                idea.author[:15],
            )

    console.print(table)


@app.command()
def stats() -> None:
    """Show statistics about ideas."""
    asyncio.run(_show_stats())


async def _show_stats() -> None:
    """Async implementation of stats command."""
    repo = IdeaRepository(get_db_path())
    await repo.create_tables()

    all_ideas = await repo.get_all_ideas()
    await repo.close()

    total = len(all_ideas)
    pending = sum(1 for i in all_ideas if i.status == IdeaStatus.PENDING)
    approved = sum(1 for i in all_ideas if i.status == IdeaStatus.APPROVED)
    rejected = sum(1 for i in all_ideas if i.status == IdeaStatus.REJECTED)
    in_progress = sum(1 for i in all_ideas if i.status == IdeaStatus.IN_PROGRESS)
    completed = sum(1 for i in all_ideas if i.status == IdeaStatus.COMPLETED)

    console.print("\n[bold]Vibe Coding Statistics[/bold]\n")
    console.print(f"Total ideas: [cyan]{total}[/cyan]")
    console.print(f"  Pending: [yellow]{pending}[/yellow]")
    console.print(f"  Approved: [green]{approved}[/green]")
    console.print(f"  Rejected: [red]{rejected}[/red]")
    console.print(f"  In Progress: [blue]{in_progress}[/blue]")
    console.print(f"  Completed: [magenta]{completed}[/magenta]")


if __name__ == "__main__":
    app()


@app.command()
def init() -> None:
    """Initialize Vibe Coding - create config files and database."""
    console.print("[bold cyan]Initializing Vibe Coding...[/bold cyan]\n")

    base_path = Path(".")

    env_file = base_path / ".env"
    if not env_file.exists():
        env_file.write_text("""# Twitch OAuth Token (получить на https://twitchapps.com/kraken/)
TWITCH_OAUTH_TOKEN=oauth:your_token_here
TWITCH_NICK=your_username
""")
        console.print(f"[green]✓[/green] Created .env")

    config_file = base_path / "config.yaml"
    if not config_file.exists():
        config_file.write_text("""vibe_coding:
  vote_threshold: 3
  bot_nick: "VibeTCoder"
  time_format: "%Y-%m-%d %H:%M:%S"

twitch:
  channel: "your_channel"
  irc_server: "irc.chat.twitch.tv"
  irc_port: 6667

database:
  path: "ideas.db"

agent:
  task_queue_path: "agent/task_queue.txt"
  branch_prefix: "feature/twitch-idea-"
  base_branch: "main"
""")
        console.print(f"[green]✓[/green] Created config.yaml")

    db_path = get_db_path()
    if not db_path.exists():
        console.print(f"[green]✓[/green] Created database: {db_path}")

    console.print("\n[bold yellow]Next steps:[/bold yellow]")
    console.print("1. Edit .env with your Twitch credentials")
    console.print("2. Edit config.yaml with your channel name")
    console.print("3. Run: [cyan]vibe run[/cyan]")


@app.command()
def run() -> None:
    """Run the Vibe Coding bot."""
    asyncio.run(_run_bot())


async def _run_bot() -> None:
    """Run the bot."""
    try:
        oauth = get_twitch_oauth()
    except (ValueError, FileNotFoundError):
        console.print("[bold red]Error:[/bold red] Twitch credentials not configured")
        console.print("Run [cyan]vibe init[/cyan] first, then edit .env")
        sys.exit(1)

    try:
        nick = get_twitch_nick()
    except (ValueError, FileNotFoundError):
        console.print("[bold red]Error:[/bold red] Twitch username not configured")
        console.print("Run [cyan]vibe init[/cyan] first, then edit .env")
        sys.exit(1)

    config = get_config()
    channel = config["twitch"]["channel"]

    if channel == "your_channel":
        console.print("[bold red]Error:[/bold red] Channel not configured")
        console.print("Edit config.yaml and set your twitch channel")
        sys.exit(1)

    console.print(f"[bold]Connecting to #{channel} as {nick}...[/bold]")
    console.print("[yellow]Bot starting... (not implemented yet - see README)[/yellow]")
    console.print("\nCLI commands available:")
    console.print("  vibe ideas     - list all ideas")
    console.print("  vibe pending  - list pending ideas")
    console.print("  vibe approve # - approve an idea")
    console.print("  vibe reject  # - reject an idea")
    console.print("  vibe stats    - show statistics")