import typer
from rich.console import Console

from fastapi_generator.commands import new_app


app = typer.Typer(help="FastAPI Project Generator & Scaffolder")
console = Console()


# --------------------------
# Root CLI Commands
# --------------------------

@app.command()
def version():
    """Show the current version of FastAPI generator."""
    console.print("[bold green]FastAPI generator v1.0.0[/bold green]")


# --------------------------
# Sub-command groups
# --------------------------

# # Project creation
app.add_typer(new_app, name="new", help="Create a new FastAPI project")



# --------------------------
# Entrypoint
# --------------------------

def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
