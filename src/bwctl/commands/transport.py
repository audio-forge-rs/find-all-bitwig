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
