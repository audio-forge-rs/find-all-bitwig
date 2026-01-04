"""Clip command for bwctl."""

from typing import Optional

import typer
from rich.console import Console

from bwctl.osc.bridge import get_bridge

console = Console()

app = typer.Typer(help="Clip operations")


def parse_clip_ref(ref: str) -> tuple[int, int]:
    """Parse a clip reference like '1:2' into (track, slot)."""
    if ":" in ref:
        parts = ref.split(":")
        return int(parts[0]), int(parts[1])
    else:
        # Just a slot number, assume current track
        return 1, int(ref)


@app.command()
def create(
    track: int = typer.Option(1, "-t", "--track", help="Track number"),
    slot: int = typer.Option(1, "-s", "--slot", help="Slot number"),
    length: int = typer.Option(4, "-l", "--length", help="Clip length in beats"),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="Clip name"),
) -> None:
    """Create a new empty clip.

    Examples:
        bwctl clip create
        bwctl clip create -t 2 -s 1 -l 8
        bwctl clip create --track 1 --slot 3 --length 16
    """
    bridge = get_bridge()
    bridge.create_clip(track, slot, length)

    console.print(f"[green]Created clip on track {track}, slot {slot}[/green]")
    console.print(f"[dim]Length: {length} beats[/dim]")


@app.command()
def launch(
    clip_refs: list[str] = typer.Argument(..., help="Clip reference(s) as track:slot"),
) -> None:
    """Launch clip(s).

    Examples:
        bwctl clip launch 1:1
        bwctl clip launch 1:1 2:1 3:1
    """
    bridge = get_bridge()

    for ref in clip_refs:
        try:
            track, slot = parse_clip_ref(ref)
            bridge.launch_clip(track, slot)
            console.print(f"[green]Launched clip {track}:{slot}[/green]")
        except ValueError:
            console.print(f"[red]Invalid clip reference: {ref}[/red]")
            console.print("[dim]Format: track:slot (e.g., 1:1)[/dim]")


@app.command()
def stop(
    clip_refs: Optional[list[str]] = typer.Argument(None, help="Clip reference(s) or 'all'"),
    all_clips: bool = typer.Option(False, "--all", "-a", help="Stop all clips"),
) -> None:
    """Stop clip(s).

    Examples:
        bwctl clip stop 1:1
        bwctl clip stop --all
        bwctl clip stop 1:1 2:1
    """
    bridge = get_bridge()

    if all_clips or (clip_refs and clip_refs[0] == "all"):
        bridge.stop_all_clips()
        console.print("[green]Stopped all clips[/green]")
        return

    if not clip_refs:
        console.print("[red]Specify clip references or use --all[/red]")
        raise typer.Exit(1)

    for ref in clip_refs:
        try:
            track, slot = parse_clip_ref(ref)
            bridge.stop_clip(track, slot)
            console.print(f"[green]Stopped clip {track}:{slot}[/green]")
        except ValueError:
            console.print(f"[red]Invalid clip reference: {ref}[/red]")


@app.command()
def record(
    track: int = typer.Option(1, "-t", "--track", help="Track number"),
    slot: int = typer.Option(1, "-s", "--slot", help="Slot number"),
) -> None:
    """Start recording into a clip slot.

    Examples:
        bwctl clip record -t 1 -s 1
    """
    bridge = get_bridge()

    # Create clip if needed and start recording
    bridge.create_clip(track, slot, 4)  # Default 4 beats
    bridge.launch_clip(track, slot)

    console.print(f"[red]Recording to track {track}, slot {slot}[/red]")
    console.print("[dim]Press stop or launch again to finish[/dim]")
