"""Track command for bwctl."""

import time
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from bwctl.osc.bridge import get_bridge

console = Console()

app = typer.Typer(help="Track operations")


@app.command()
def add(
    track_type: str = typer.Option(
        "instrument", "-t", "--type", help="Track type: audio, instrument, effect"
    ),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="Track name"),
) -> None:
    """Add a new track.

    Examples:
        bwctl track add --type instrument --name "Lead"
        bwctl track add -t audio
        bwctl track add -t effect
    """
    valid_types = ["audio", "instrument", "effect"]
    if track_type not in valid_types:
        console.print(f"[red]Invalid track type: {track_type}[/red]")
        console.print(f"Valid types: {', '.join(valid_types)}")
        raise typer.Exit(1)

    bridge = get_bridge()
    bridge.add_track(track_type)

    msg = f"[green]Added {track_type} track[/green]"
    if name:
        msg += f" '{name}'"
    console.print(msg)


@app.command()
def select(
    track_number: int = typer.Argument(..., help="Track number (1-indexed)"),
) -> None:
    """Select a track by number.

    Example:
        bwctl track select 2
    """
    if track_number < 1 or track_number > 8:
        console.print("[yellow]Note: Track bank is 1-8. Use bank navigation for more.[/yellow]")

    bridge = get_bridge()
    bridge.select_track(track_number)
    console.print(f"[green]Selected track {track_number}[/green]")


@app.command()
def enter(
    track_number: int = typer.Argument(..., help="Group track number to enter"),
) -> None:
    """Enter a group track (hierarchical mode).

    Example:
        bwctl track enter 1
    """
    bridge = get_bridge()
    bridge.enter_group(track_number)
    console.print(f"[green]Entered group track {track_number}[/green]")


@app.command()
def exit() -> None:
    """Exit current group to parent (hierarchical mode).

    Example:
        bwctl track exit
    """
    bridge = get_bridge()
    bridge.exit_group()
    console.print("[green]Exited to parent[/green]")


@app.command()
def mute(
    track_numbers: list[int] = typer.Argument(..., help="Track number(s) to mute"),
    off: bool = typer.Option(False, "--off", help="Unmute instead of mute"),
) -> None:
    """Mute track(s).

    Examples:
        bwctl track mute 1
        bwctl track mute 1 2 3
        bwctl track mute 1 --off
    """
    bridge = get_bridge()
    action = "Unmuted" if off else "Muted"

    for num in track_numbers:
        bridge.set_track_mute(num, mute=not off)
        console.print(f"[green]{action} track {num}[/green]")


@app.command()
def solo(
    track_numbers: list[int] = typer.Argument(..., help="Track number(s) to solo"),
    off: bool = typer.Option(False, "--off", help="Unsolo instead of solo"),
) -> None:
    """Solo track(s).

    Examples:
        bwctl track solo 1
        bwctl track solo 1 2 --off
    """
    bridge = get_bridge()
    action = "Unsoloed" if off else "Soloed"

    for num in track_numbers:
        bridge.set_track_solo(num, solo=not off)
        console.print(f"[green]{action} track {num}[/green]")


@app.command()
def arm(
    track_numbers: list[int] = typer.Argument(..., help="Track number(s) to arm"),
    off: bool = typer.Option(False, "--off", help="Disarm instead of arm"),
) -> None:
    """Arm track(s) for recording.

    Examples:
        bwctl track arm 1
        bwctl track arm 1 2 3 --off
    """
    bridge = get_bridge()
    action = "Disarmed" if off else "Armed"

    for num in track_numbers:
        bridge.set_track_arm(num, arm=not off)
        console.print(f"[green]{action} track {num}[/green]")


@app.command()
def volume(
    track_number: int = typer.Argument(..., help="Track number"),
    value: float = typer.Argument(..., help="Volume (0.0 to 1.0)"),
) -> None:
    """Set track volume.

    Example:
        bwctl track volume 1 0.75
    """
    if value < 0 or value > 1:
        console.print("[red]Volume must be between 0.0 and 1.0[/red]")
        raise typer.Exit(1)

    bridge = get_bridge()
    bridge.set_track_volume(track_number, value)
    console.print(f"[green]Set track {track_number} volume to {value:.0%}[/green]")


@app.command()
def pan(
    track_number: int = typer.Argument(..., help="Track number"),
    value: float = typer.Argument(..., help="Pan (-1.0 = left, 0.0 = center, 1.0 = right)"),
) -> None:
    """Set track pan.

    Examples:
        bwctl track pan 1 0      # Center
        bwctl track pan 3 -0.3   # 30% left
        bwctl track pan 8 0.2    # 20% right
    """
    if value < -1 or value > 1:
        console.print("[red]Pan must be between -1.0 (left) and 1.0 (right)[/red]")
        raise typer.Exit(1)

    bridge = get_bridge()
    bridge.set_track_pan(track_number, value)

    if value < 0:
        pos = f"{abs(value):.0%} L"
    elif value > 0:
        pos = f"{value:.0%} R"
    else:
        pos = "Center"
    console.print(f"[green]Set track {track_number} pan to {pos}[/green]")


@app.command("list")
def list_tracks(
    count: int = typer.Option(20, "-n", "--count", help="Number of tracks to scan"),
) -> None:
    """List tracks with their names and devices.

    Queries Bitwig via OSC to get track names by selecting each track
    and listening for the response.

    Examples:
        bwctl track list
        bwctl track list -n 10
    """
    from bwctl.osc.bridge import BitwigOSCBridge

    # Create fresh bridge instance for receiving
    bridge = BitwigOSCBridge()

    results = []
    current = {"num": 0, "name": None, "device": None}

    import logging
    logger = logging.getLogger(__name__)

    def handle_all(address, *args):
        logger.debug(f"OSC RECV: {address} {args}")
        if address == "/track/selected/name" and args and args[0]:
            current["name"] = args[0]
        elif address == "/device/name" and args and args[0]:
            current["device"] = args[0]

    bridge.dispatcher.set_default_handler(handle_all)
    bridge.start_server()

    console.print(f"[dim]Scanning {count} tracks...[/dim]")

    for i in range(1, count + 1):
        current["num"] = i
        current["name"] = None
        current["device"] = None

        bridge.select_track(i)
        time.sleep(0.3)

        if current["name"]:
            results.append({
                "num": i,
                "name": current["name"],
                "device": current["device"]
            })

    bridge.stop_server()

    # Build table
    table = Table(title="Tracks")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("Device", style="green")

    for info in results:
        table.add_row(str(info["num"]), info["name"], info["device"] or "")

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} tracks[/dim]")
