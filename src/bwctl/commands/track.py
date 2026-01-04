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
def bank(
    direction: str = typer.Argument("show", help="Direction: next, prev, page-next, page-prev, or show"),
) -> None:
    """Navigate or show track bank position.

    The track bank is a sliding window over tracks.
    Use this to scroll to see different tracks.

    Examples:
        bwctl track bank show      # Show current bank position
        bwctl track bank next      # Scroll one track forward
        bwctl track bank prev      # Scroll one track back
        bwctl track bank page-next # Scroll one page forward
        bwctl track bank page-prev # Scroll one page back
    """
    from bwctl.osc.bridge import BitwigOSCBridge

    bridge = BitwigOSCBridge()

    if direction == "show":
        # Query current bank position
        track_slots = set()

        def handler(addr, *args):
            if addr.startswith("/track/"):
                parts = addr.split("/")
                if len(parts) >= 3 and parts[2].isdigit():
                    track_slots.add(int(parts[2]))

        bridge.dispatcher.set_default_handler(handler)
        bridge.start_server()
        time.sleep(0.1)
        bridge.send("/refresh")
        time.sleep(1.5)
        bridge.stop_server()

        if track_slots:
            slots = sorted(track_slots)
            console.print(f"Track bank showing slots: [cyan]{min(slots)}[/cyan] - [cyan]{max(slots)}[/cyan]")
        else:
            console.print("[yellow]No track data received[/yellow]")

    elif direction == "next":
        bridge.scroll_track_bank(1)
        console.print("[green]Scrolled track bank forward[/green]")

    elif direction == "prev":
        bridge.scroll_track_bank(-1)
        console.print("[green]Scrolled track bank back[/green]")

    elif direction == "page-next":
        bridge.scroll_track_bank_page(1)
        console.print("[green]Scrolled track bank forward one page[/green]")

    elif direction == "page-prev":
        bridge.scroll_track_bank_page(-1)
        console.print("[green]Scrolled track bank back one page[/green]")

    else:
        console.print(f"[red]Unknown direction: {direction}[/red]")
        console.print("Valid: show, next, prev, page-next, page-prev")
        raise typer.Exit(1)


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
def list_tracks() -> None:
    """List tracks in the current track bank.

    Shows tracks visible in the current track bank view.
    Use 'bwctl track bank' commands to navigate.

    Examples:
        bwctl track list
    """
    from bwctl.osc.bridge import BitwigOSCBridge
    import logging
    logger = logging.getLogger(__name__)

    bridge = BitwigOSCBridge()
    tracks = {}  # {track_num: {name, type, isGroup, ...}}

    def handle_all(address, *args):
        logger.debug(f"OSC RECV: {address} {args}")
        # Parse /track/N/property messages (skip clip/send data)
        if address.startswith("/track/") and "/clip/" not in address and "/send/" not in address:
            parts = address.split("/")
            if len(parts) >= 4 and parts[2].isdigit():
                track_num = int(parts[2])
                prop = parts[3]
                if track_num not in tracks:
                    tracks[track_num] = {}
                if args and args[0] not in (None, ""):
                    tracks[track_num][prop] = args[0]

    bridge.dispatcher.set_default_handler(handle_all)
    bridge.start_server()
    time.sleep(0.1)  # Let server start

    console.print(f"[dim]Querying track bank...[/dim]")
    bridge.send("/refresh")
    time.sleep(2.5)  # Wait for response flood

    bridge.stop_server()

    # Find tracks that exist
    valid_tracks = [(num, info) for num, info in sorted(tracks.items())
                    if info.get("exists") == 1 and info.get("name")]

    logger.debug(f"Valid tracks: {len(valid_tracks)}")

    # Build table
    table = Table(title="Track Bank")
    table.add_column("Slot", style="dim", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Pos", style="dim", width=4)

    for num, info in valid_tracks:
        name = info.get("name", "")
        is_group = info.get("isGroup", 0)
        track_type = "Group" if is_group else info.get("type", "track")
        position = info.get("position", "?")
        table.add_row(str(num), name, track_type, str(position))

    console.print(table)
    console.print(f"\n[dim]Showing {len(valid_tracks)} tracks in current bank[/dim]")
