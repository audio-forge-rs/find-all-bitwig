"""Transport command for bwctl."""

import typer
from rich.console import Console

from bwctl.osc.bridge import get_bridge

console = Console()

app = typer.Typer(help="Transport controls")


@app.command()
def play() -> None:
    """Start playback."""
    bridge = get_bridge()
    bridge.play()
    console.print("[green]▶ Playing[/green]")


@app.command()
def stop() -> None:
    """Stop playback."""
    bridge = get_bridge()
    bridge.stop()
    console.print("[yellow]■ Stopped[/yellow]")


@app.command()
def record() -> None:
    """Toggle recording."""
    bridge = get_bridge()
    bridge.record()
    console.print("[red]● Recording[/red]")


@app.command()
def loop() -> None:
    """Toggle loop mode."""
    bridge = get_bridge()
    bridge.toggle_loop()
    console.print("[green]↻ Toggled loop[/green]")


@app.command()
def tempo(
    bpm: float = typer.Argument(..., help="Tempo in BPM (20-666)"),
) -> None:
    """Set the tempo.

    Examples:
        bwctl transport tempo 120
        bwctl transport tempo 108
    """
    if bpm < 20 or bpm > 666:
        console.print("[red]Tempo must be between 20 and 666 BPM[/red]")
        raise typer.Exit(1)

    bridge = get_bridge()
    bridge.set_tempo(bpm)
    console.print(f"[green]Tempo set to {bpm} BPM[/green]")


@app.command()
def action(
    action_id: str = typer.Argument(..., help="Bitwig action ID to invoke"),
) -> None:
    """Invoke a Bitwig action by ID.

    Examples:
        bwctl transport action group_selected_tracks
        bwctl transport action slice_to_drum_track
    """
    bridge = get_bridge()
    bridge.invoke_action(action_id)
    console.print(f"[green]Invoked action: {action_id}[/green]")
