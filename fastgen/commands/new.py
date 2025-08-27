import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def create(project_name: str):
    """
    Create a new FastAPI project (placeholder for now).
    """
    console.print(f"[bold green]Project '{project_name}' has been created![/bold green]")
