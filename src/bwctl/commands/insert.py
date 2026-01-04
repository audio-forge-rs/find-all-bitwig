"""Insert command for bwctl."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from bwctl.db.search import get_content_by_id, search_content
from bwctl.osc.bridge import get_bridge

console = Console()


def insert(
    target: str = typer.Argument(..., help="Content ID, file path, or search query"),
    search: bool = typer.Option(False, "-s", "--search", help="Treat target as search query"),
    track: Optional[int] = typer.Option(None, "-t", "--track", help="Target track number"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be inserted"),
) -> None:
    """Insert content into Bitwig.

    TARGET can be:
    - A content ID from search results (e.g., 42)
    - A file path (e.g., ~/presets/my-bass.bwpreset)
    - A search query with --search flag

    Examples:
        bwctl insert 42
        bwctl insert ~/presets/my-bass.bwpreset
        bwctl insert --search "warm pad"
        bwctl insert -s "polymer bass" -t 1
    """
    file_path: str | None = None
    content_name: str = target

    # Determine what type of target we have
    if search:
        # Search and use first result
        results = search_content(query=target, limit=1)
        if not results:
            console.print(f"[red]No results found for '{target}'[/red]")
            raise typer.Exit(1)

        result = results[0]
        file_path = result.file_path
        content_name = result.name
        console.print(f"[dim]Found: {result.name} ({result.content_type.value})[/dim]")

    elif target.isdigit():
        # Content ID
        content_id = int(target)
        result = get_content_by_id(content_id)
        if not result:
            console.print(f"[red]Content ID {content_id} not found[/red]")
            raise typer.Exit(1)

        file_path = result.file_path
        content_name = result.name

    else:
        # File path
        path = Path(target).expanduser()
        if not path.exists():
            console.print(f"[red]File not found: {target}[/red]")
            raise typer.Exit(1)

        file_path = str(path)
        content_name = path.stem

    if dry_run:
        console.print(f"[yellow]Would insert:[/yellow] {content_name}")
        console.print(f"[dim]  Path: {file_path}[/dim]")
        if track:
            console.print(f"[dim]  Track: {track}[/dim]")
        return

    # Get the OSC bridge
    bridge = get_bridge()

    # Select track if specified
    if track:
        bridge.select_track(track)
        console.print(f"[dim]Selected track {track}[/dim]")

    # Insert the file
    # Note: DrivenByMoss doesn't have a direct "insert file" OSC command
    # We need to use the browser or a custom extension
    # For now, we'll open the browser and show what to do

    console.print(f"[green]Inserting:[/green] {content_name}")
    console.print(f"[dim]Path: {file_path}[/dim]")

    # Try to use browser approach
    # This opens the device browser - user needs to navigate to the file
    # A custom extension would allow direct file insertion
    bridge.open_device_browser()
    console.print()
    console.print("[yellow]Browser opened in Bitwig.[/yellow]")
    console.print(f"[dim]Navigate to: {file_path}[/dim]")
    console.print()
    console.print("[dim]Note: Direct file insertion requires DrivenByMoss to be running.[/dim]")
    console.print("[dim]Configure in Bitwig: Settings > Controllers > Open Sound Control[/dim]")
