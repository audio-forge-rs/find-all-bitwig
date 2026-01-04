"""Search command for bwctl."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from bwctl.db.models import ContentType, DeviceType
from bwctl.db.search import get_stats, search_content

console = Console()


def search(
    query: str = typer.Argument(..., help="Search query (supports fuzzy matching)"),
    content_type: Optional[str] = typer.Option(
        None, "-t", "--type", help="Filter by type: preset, sample, clip, etc."
    ),
    device: Optional[str] = typer.Option(
        None, "-d", "--device", help="Filter by parent device name"
    ),
    category: Optional[str] = typer.Option(
        None, "-c", "--category", help="Filter by category"
    ),
    limit: int = typer.Option(20, "-n", "--limit", help="Maximum results"),
    offset: int = typer.Option(0, "--offset", help="Skip first N results"),
    output: str = typer.Option(
        "table", "-o", "--output", help="Output format: table, json, paths"
    ),
) -> None:
    """Search for Bitwig content with fuzzy matching.

    Examples:
        bwctl search "warm pad"
        bwctl search "bass" -t preset -d Polymer
        bwctl search "kick" -t sample -c Drums
    """
    # Parse content type
    ct = None
    if content_type:
        try:
            ct = ContentType(content_type.lower())
        except ValueError:
            console.print(f"[red]Invalid content type: {content_type}[/red]")
            console.print(f"Valid types: {', '.join(t.value for t in ContentType)}")
            raise typer.Exit(1)

    # Search
    try:
        results = search_content(
            query=query,
            content_type=ct,
            parent_device=device,
            category=category,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        console.print("[dim]Is the database running? Try: docker-compose up -d[/dim]")
        raise typer.Exit(1)

    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        raise typer.Exit(0)

    # Output results
    if output == "json":
        import json
        data = [r.model_dump() for r in results]
        console.print(json.dumps(data, indent=2, default=str))
    elif output == "paths":
        for r in results:
            console.print(r.file_path)
    else:
        # Table output
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Name", width=35)
        table.add_column("Type", width=10)
        table.add_column("Device", width=15)
        table.add_column("Category", width=15)
        table.add_column("Package", width=15)

        for r in results:
            table.add_row(
                str(r.id),
                r.name[:35],
                r.content_type.value,
                (r.parent_device or "")[:15],
                (r.category or "")[:15],
                (r.package_name or "")[:15],
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(results)} results[/dim]")


def stats() -> None:
    """Show content statistics."""
    try:
        content_stats = get_stats()
    except Exception as e:
        console.print(f"[red]Failed to get stats: {e}[/red]")
        raise typer.Exit(1)

    table = Table(title="Content Statistics", show_header=True)
    table.add_column("Type", style="bold")
    table.add_column("Count", justify="right")

    total = 0
    for content_type, count in sorted(content_stats.items()):
        table.add_row(content_type, str(count))
        total += count

    table.add_row("", "")
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

    console.print(table)
