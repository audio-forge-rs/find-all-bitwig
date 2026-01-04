"""Index command for bwctl."""

from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from bwctl.db.indexer import run_indexer

console = Console()

app = typer.Typer(help="Index Bitwig content")


@app.callback(invoke_without_command=True)
def index(
    full: bool = typer.Option(False, "--full", help="Full reindex (clear existing)"),
    path: Optional[str] = typer.Option(None, "--path", help="Index specific path"),
    workers: int = typer.Option(4, "--workers", "-w", help="Parallel workers"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be indexed"),
) -> None:
    """Index Bitwig content into the database.

    Examples:
        bwctl index --full
        bwctl index --path ~/Documents/Bitwig\\ Studio/Library
        bwctl index --incremental
    """
    paths = [path] if path else None

    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/yellow]")
        # TODO: Implement dry run discovery
        return

    console.print("[bold]Indexing Bitwig content...[/bold]")

    if full:
        console.print("[yellow]Full reindex - clearing existing data[/yellow]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            stats = run_indexer(
                paths=paths,
                full=full,
                workers=workers,
                progress=progress,
            )
    except Exception as e:
        console.print(f"[red]Indexing failed: {e}[/red]")
        console.print("[dim]Is the database running? Try: docker-compose up -d[/dim]")
        raise typer.Exit(1)

    console.print()
    console.print("[bold green]Indexing complete![/bold green]")
    console.print(f"  Packages: {stats['packages']}")
    console.print(f"  Files:    {stats['files']}")
    if stats['errors'] > 0:
        console.print(f"  [yellow]Errors:   {stats['errors']}[/yellow]")
