"""Device command for bwctl."""

import logging
import time
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from bwctl.osc.bridge import get_bridge, BitwigOSCBridge
from bwctl.db.search import search_content
from bwctl.db.models import ContentType

console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(help="Device operations")


@app.command("list")
def list_devices(
    track: Optional[int] = typer.Option(None, "-t", "--track", help="Track to query"),
    count: int = typer.Option(8, "-n", "--count", help="Max devices to scan"),
) -> None:
    """List devices in the current track's device chain.

    Examples:
        bwctl device list
        bwctl device list -t 1
        bwctl device list -n 16
    """
    bridge = BitwigOSCBridge()
    devices = []
    current = {"name": None, "bypassed": None}

    def handle_osc(address, *args):
        logger.debug(f"OSC RECV: {address} {args}")
        if "/device/name" in address and args:
            current["name"] = args[0] if args[0] else None
        elif "/device/isEnabled" in address and args:
            current["bypassed"] = not args[0]

    bridge.dispatcher.set_default_handler(handle_osc)
    bridge.start_server()  # Start server FIRST to catch responses

    console.print(f"[dim]Scanning device chain...[/dim]")

    # Select track to trigger device info (AFTER server fully started)
    target_track = track or 1
    bridge.select_track(target_track)

    # Wait for OSC response (device info takes time to arrive)
    time.sleep(0.8)

    # Check first device
    if current["name"]:
        devices.append({
            "num": 1,
            "name": current["name"],
            "bypassed": current["bypassed"]
        })
    else:
        # No device on this track
        bridge.stop_server()
        console.print("[yellow]No devices found on track[/yellow]")
        return

    # Navigate through siblings
    for i in range(2, count + 1):
        prev_name = current["name"]
        current["name"] = None
        current["bypassed"] = None
        bridge.select_next_device()
        time.sleep(0.2)

        if current["name"] and current["name"] != prev_name:
            devices.append({
                "num": i,
                "name": current["name"],
                "bypassed": current["bypassed"]
            })
        else:
            break  # No more devices or looped back

    bridge.stop_server()

    # Build table
    table = Table(title="Device Chain")
    table.add_column("#", style="dim", width=4)
    table.add_column("Device", style="cyan")
    table.add_column("Status", style="green")

    for dev in devices:
        status = "[yellow]Bypassed[/yellow]" if dev["bypassed"] else "Active"
        table.add_row(str(dev["num"]), dev["name"], status)

    console.print(table)
    console.print(f"\n[dim]Found {len(devices)} devices[/dim]")


@app.command()
def add(
    name: str = typer.Argument(..., help="Device name (exact match for Bitwig devices)"),
    track: Optional[int] = typer.Option(None, "-t", "--track", help="Target track"),
    browse: bool = typer.Option(False, "--browse", "-b", help="Open browser instead of direct insert"),
) -> None:
    """Add a device to the current or specified track.

    Directly inserts the device by name (headless, no browser).
    Use --browse to open the browser for fuzzy search instead.

    Examples:
        bwctl device add Polymer
        bwctl device add "EQ-5" -t 1
        bwctl device add Phase-4
        bwctl device add E-Kick
        bwctl device add Reverb --browse  # Use browser
    """
    bridge = get_bridge()

    # Select track if specified
    if track:
        bridge.select_track(track)
        console.print(f"[dim]Selected track {track}[/dim]")

    if browse:
        # Open device browser for fuzzy search
        bridge.open_device_browser()
        console.print(f"[green]Opening browser for:[/green] {name}")
        console.print("[dim]Use browser navigation or type to search[/dim]")
    else:
        # Direct headless insertion
        bridge.add_device(name)
        console.print(f"[green]Added device:[/green] {name}")


@app.command()
def load(
    preset_name: str = typer.Argument(..., help="Preset name to search and load"),
    device: Optional[str] = typer.Option(None, "-d", "--device", help="Filter by device name"),
    track: Optional[int] = typer.Option(None, "-t", "--track", help="Target track"),
) -> None:
    """Load a preset by name (searches database and inserts the .bwpreset file).

    This is the headless way to load presets with specific settings.

    Examples:
        bwctl device load "DX-80s"
        bwctl device load "Sub Kick" -d E-Kick
        bwctl device load "Dark Snare" -t 7
    """
    bridge = get_bridge()

    # Select track if specified
    if track:
        bridge.select_track(track)
        console.print(f"[dim]Selected track {track}[/dim]")

    # Search for preset in database
    results = search_content(
        query=preset_name,
        content_type=ContentType.PRESET,
        limit=5,
    )

    # Filter by device if specified
    if device and results:
        results = [r for r in results if r.parent_device and device.lower() in r.parent_device.lower()]

    if not results:
        console.print(f"[red]No preset found for:[/red] {preset_name}")
        if device:
            console.print(f"[dim]Filtered by device: {device}[/dim]")
        raise typer.Exit(1)

    # Use the first match
    best_match = results[0]
    if not best_match.file_path:
        console.print(f"[red]Preset found but no file path:[/red] {best_match.name}")
        raise typer.Exit(1)

    # Insert the preset file
    bridge.insert_preset(best_match.file_path)
    console.print(f"[green]Loaded preset:[/green] {best_match.name}")
    if best_match.parent_device:
        console.print(f"[dim]Device: {best_match.parent_device}[/dim]")


@app.command()
def master(
    device_name: str = typer.Argument(..., help="Device name to add to master"),
) -> None:
    """Add a device to the master track.

    Examples:
        bwctl device master "Peak Limiter"
        bwctl device master EQ-5
    """
    bridge = get_bridge()
    bridge.add_master_device(device_name)
    console.print(f"[green]Added to master:[/green] {device_name}")


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
