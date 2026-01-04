"""Device command for bwctl."""

from typing import Optional

import typer
from rich.console import Console

from bwctl.db.search import search_content
from bwctl.db.models import ContentType
from bwctl.osc.bridge import get_bridge

console = Console()

app = typer.Typer(help="Device operations")


@app.command()
def add(
    name: str = typer.Argument(..., help="Device name (fuzzy search)"),
    track: Optional[int] = typer.Option(None, "-t", "--track", help="Target track"),
) -> None:
    """Add a device to the current or specified track.

    Uses fuzzy search to find the device. Opens the browser with results.

    Examples:
        bwctl device add Polymer
        bwctl device add "EQ-5" -t 1
        bwctl device add reverb
    """
    bridge = get_bridge()

    # Select track if specified
    if track:
        bridge.select_track(track)
        console.print(f"[dim]Selected track {track}[/dim]")

    # Search for device in database
    results = search_content(
        query=name,
        content_type=ContentType.PRESET,
        limit=5,
    )

    if results:
        console.print(f"[dim]Found {len(results)} matches:[/dim]")
        for r in results[:3]:
            console.print(f"  - {r.name} ({r.parent_device or 'device'})")

    # Open device browser
    bridge.open_device_browser()
    console.print()
    console.print(f"[green]Opening browser for:[/green] {name}")
    console.print("[dim]Use browser navigation or type to search[/dim]")


@app.command()
def bypass(
    toggle: bool = typer.Option(True, "--toggle/--no-toggle", help="Toggle bypass"),
    enable: bool = typer.Option(False, "--on", help="Enable device (unbypass)"),
    disable: bool = typer.Option(False, "--off", help="Disable device (bypass)"),
) -> None:
    """Toggle or set device bypass state.

    Examples:
        bwctl device bypass           # Toggle
        bwctl device bypass --on      # Enable (unbypass)
        bwctl device bypass --off     # Disable (bypass)
    """
    bridge = get_bridge()

    if enable:
        bridge.set_device_bypass(bypass=False)
        console.print("[green]Device enabled[/green]")
    elif disable:
        bridge.set_device_bypass(bypass=True)
        console.print("[yellow]Device bypassed[/yellow]")
    else:
        bridge.set_device_bypass(bypass=None)  # Toggle
        console.print("[green]Toggled device bypass[/green]")


@app.command()
def param(
    name: Optional[str] = typer.Option(None, "-n", "--name", help="Parameter name"),
    index: Optional[int] = typer.Option(None, "-i", "--index", help="Parameter index (1-8)"),
    value: float = typer.Argument(..., help="Parameter value (0.0 to 1.0)"),
) -> None:
    """Set a device parameter value.

    Examples:
        bwctl device param -i 1 0.75
        bwctl device param --name Cutoff 0.5
    """
    if index is None and name is None:
        console.print("[red]Specify either --index or --name[/red]")
        raise typer.Exit(1)

    if value < 0 or value > 1:
        console.print("[red]Value must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)

    bridge = get_bridge()

    if index:
        bridge.set_device_param(index, value)
        console.print(f"[green]Set parameter {index} to {value:.0%}[/green]")
    else:
        # For named parameters, we'd need to search the parameter list
        # This requires bidirectional OSC which we haven't implemented
        console.print(f"[yellow]Named parameter lookup not yet implemented[/yellow]")
        console.print(f"[dim]Use --index instead for now[/dim]")


@app.command()
def preset(
    action: str = typer.Argument("browse", help="Action: browse, next, prev"),
) -> None:
    """Browse or navigate device presets.

    Examples:
        bwctl device preset browse    # Open preset browser
        bwctl device preset next      # Next preset
        bwctl device preset prev      # Previous preset
    """
    bridge = get_bridge()

    if action == "browse":
        bridge.open_preset_browser()
        console.print("[green]Opening preset browser[/green]")
    elif action == "next":
        bridge.browser_navigate(1)
        console.print("[green]Next preset[/green]")
    elif action == "prev":
        bridge.browser_navigate(-1)
        console.print("[green]Previous preset[/green]")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: browse, next, prev")
        raise typer.Exit(1)
