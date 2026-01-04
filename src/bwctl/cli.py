"""Main CLI entry point for bwctl."""

import typer
from rich.console import Console

from bwctl import __version__
from bwctl.commands import clip, device, index, track, transport
from bwctl.commands.insert import insert as insert_cmd
from bwctl.commands.search import search as search_cmd, stats as stats_cmd

console = Console()

app = typer.Typer(
    name="bwctl",
    help="Bitwig Studio command line controller",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(index.app, name="index")
app.add_typer(track.app, name="track")
app.add_typer(device.app, name="device")
app.add_typer(clip.app, name="clip")
app.add_typer(transport.app, name="transport")

# Register direct commands
app.command(name="search")(search_cmd)
app.command(name="stats")(stats_cmd)
app.command(name="insert")(insert_cmd)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"bwctl version {__version__}")


@app.command(name="s")
def search_shortcut(
    query: str = typer.Argument(..., help="Search query"),
    content_type: str = typer.Option(None, "-t", "--type"),
    device: str = typer.Option(None, "-d", "--device"),
    limit: int = typer.Option(20, "-n", "--limit"),
) -> None:
    """Quick search (alias for 'search').

    Example: bwctl s "warm pad"
    """
    search_cmd(
        query=query,
        content_type=content_type,
        device=device,
        category=None,
        limit=limit,
        offset=0,
        output="table",
    )


# Transport shortcuts
@app.command()
def play() -> None:
    """Start playback (shortcut for 'transport play')."""
    transport.play()


@app.command()
def stop() -> None:
    """Stop playback (shortcut for 'transport stop')."""
    transport.stop()


@app.command()
def rec() -> None:
    """Toggle recording (shortcut for 'transport record')."""
    transport.record()


if __name__ == "__main__":
    app()
