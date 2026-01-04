"""Track command for bwctl."""

from typing import Optional

import typer
from rich.console import Console

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
