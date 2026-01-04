"""Main CLI entry point for bwctl."""

import typer
from rich.console import Console

from bwctl import __version__
from bwctl.commands import index, search

console = Console()

app = typer.Typer(
    name="bwctl",
    help="Bitwig Studio command line controller",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(search.app, name="search")
app.add_typer(index.app, name="index")


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
    search.search(
        query=query,
        content_type=content_type,
        device=device,
        category=None,
        limit=limit,
        offset=0,
        output="table",
    )


# Future command stubs
@app.command(hidden=True)
def insert() -> None:
    """Insert content into Bitwig (coming soon)."""
    console.print("[yellow]Insert command coming soon![/yellow]")


@app.command(hidden=True)
def track() -> None:
    """Track operations (coming soon)."""
    console.print("[yellow]Track command coming soon![/yellow]")


@app.command(hidden=True)
def device() -> None:
    """Device operations (coming soon)."""
    console.print("[yellow]Device command coming soon![/yellow]")


@app.command(hidden=True)
def clip() -> None:
    """Clip operations (coming soon)."""
    console.print("[yellow]Clip command coming soon![/yellow]")


if __name__ == "__main__":
    app()
