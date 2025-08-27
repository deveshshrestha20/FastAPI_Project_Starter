import typer
from rich.console import Console

from fastgen.commands import new_app

# Subcommands will live in fastgen/commands/
# from fastgen.commands import new, add, generate

app = typer.Typer(help="⚡ Fastgen - FastAPI Project Generator & Scaffolder")
console = Console()


# --------------------------
# Root CLI Commands
# --------------------------

@app.command()
def version():
    """Show the current version of Fastgen."""
    console.print("[bold green]Fastgen v0.1.0[/bold green]")


# --------------------------
# Sub-command groups
# --------------------------

# # Project creation
app.add_typer(new_app, name="new", help="Create a new FastAPI project")
#
# # Add integrations (Celery, RabbitMQ, etc.)
# app.add_typer(add.app, name="add", help="Add integrations like celery, rabbitmq, flower")
#
# # Generate scaffolds (models, routers, workers, etc.)
# app.add_typer(generate.app, name="generate", help="Generate code scaffolds")


# --------------------------
# Entrypoint
# --------------------------

def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
