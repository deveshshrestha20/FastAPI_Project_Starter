"""
FastAPI Template Generator
"""

from pathlib import Path
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from fastapi_generator.core.utils import (
    create_directory_structure,
    create_init_files,
    cleanup_project,
    validate_project_name,
    write_file,
)
from fastapi_generator.core.post_deployment_setup import run_post_setup
from ..core.config import (
    FEATURES,
    collect_postgresql_config,
    collect_auto_setup_config,
)
from ..core.templates import TemplateRenderer, TemplateContext

console = Console()

app = typer.Typer(
    name="fastapi_generator",
    help="FastAPI Template Generator - Create FastAPI projects quickly",
    rich_markup_mode="markdown"
)


@app.command()
def create(
        project_name: str = typer.Argument(..., help="Name of the FastAPI project to create."),
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Run in interactive mode to configure features."
        )
):
    """
    Creates a new FastAPI project with a modern, feature-based structure.

    """
    console.print(Panel(
        f"Initializing a new FastAPI project named [bold cyan]{project_name}[/bold cyan]\n"
        f"Interactive Mode: {'[bold green]Enabled[/bold green]' if interactive else '[bold red]Disabled[/bold red]'}",
        title=" [bold]FastAPI Project Generator[/bold] ",
        border_style="blue"
    ))

    project_path = Path.cwd() / project_name
    renderer = TemplateRenderer()

    # Configuration collection
    if interactive:
        # Use TemplateContext with interactive prompts
        context_manager = TemplateContext(project_name)
        context_manager.add_interactive_context()  # This calls the author/email prompts
        context = context_manager.context

        # Then collect database config if needed
        if context.get("include_database"):
            console.print("\n[bold yellow]Database Configuration Required[/bold yellow]")
            db_config = collect_postgresql_config(
                context["project_slug"],
                is_async=context.get("is_async")
            )
            context.update(db_config)

        # Finally collect auto-setup config
        context = collect_auto_setup_config(context)

    else:
        # Non-interactive mode - use defaults with auto-setup enabled
        context_manager = TemplateContext(project_name)
        context = context_manager.context
        context["auto_setup"] = True  # Default to auto-setup in non-interactive mode

        # Handle database configuration if enabled in non-interactive mode
        if context.get("include_database"):
            console.print("\n[bold yellow]Database Configuration Required[/bold yellow]")
            db_config = collect_postgresql_config(
                context["project_slug"],
                is_async=context.get("is_async")
            )
            context.update(db_config)

    try:
        # Validate project
        if not validate_project_name(project_name):
            console.print(f"[red]Invalid project name: '{project_name}'[/red]")
            raise typer.Exit(1)

        if project_path.exists():
            console.print(f"[yellow]Directory [bold]'{project_path}'[/bold] already exists.[/yellow]")
            if not typer.confirm("Do you want to overwrite it?", default=False):
                console.print("[red]Project creation aborted.[/red]")
                raise typer.Exit()
            cleanup_project(project_path)

        # Create project directory
        project_path.mkdir(parents=True)

        # Create project with progress indicator
        console.print("\n[bold cyan]📁 Creating Project Structure[/bold cyan]")
        with Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[progress.description]{task.description}"),
                console=console,
        ) as progress:
            tasks = [
                ("Creating folder structure...",
                 lambda: create_directory_structure(project_path, context)),
                ("Generating files from templates...",
                 lambda: _render_templates(renderer, project_path, context)),
                ("Creating __init__.py files...",
                 lambda: create_init_files(project_path, context)),
            ]

            for desc, func in tasks:
                task_id = progress.add_task(description=desc, total=None)
                func()
                progress.update(task_id, completed=1, description=f"[green]✓[/green] {desc}")

        console.print("[green] Project structure created successfully![/green]")

        # Run post-setup
        setup_success = run_post_setup(
            project_name=project_name,
            context=context
        )

        # Print basic message only if auto-setup was skipped
        if not context.get("auto_setup", False):
            _print_basic_success_message(project_name, context)

    except Exception as e:
        console.print(Panel(f"[bold red]An error occurred:[/bold red]\n{e}", title="Error", border_style="red"))
        cleanup_project(project_path)
        raise typer.Exit(1)


def _render_templates(renderer, project_path, context):
    """Helper function to render templates"""
    mappings = renderer.get_template_mappings(context)
    for template_file, output_file in mappings.items():
        content = renderer.render_template(template_file, context)
        write_file(project_path / output_file, content)


def _print_basic_success_message(project_name: str, context: dict):
    """Print basic success message when auto-setup is skipped"""
    message = f"✓ Project [bold cyan]'{project_name}'[/bold cyan] created successfully!\n\n"

    message += (
        "[bold]Next Steps:[/bold]\n"
        f"  1. [cyan]cd {project_name}[/cyan]\n"
        "  2. [cyan]make install[/cyan]  # Install dependencies\n"
        "  3. [cyan]make dev[/cyan]      # Start development environment\n\n"
    )

    message += (
        "[bold]Your API will be available at:[/bold]\n"
        "  - [link=http://127.0.0.1:8000]http://127.0.0.1:8000[/link]\n"
        "  - [link=http://127.0.0.1:8000/docs]API Docs: http://127.0.0.1:8000/docs[/link]\n"
    )

    if context.get("include_celery"):
        message += "  - [link=http://flower.localhost]Celery Monitor: http://flower.localhost[/link]\n"

    console.print(Panel(message, title=" [bold green]Project Created![/bold green] ", border_style="green"))


@app.command("setup")
def setup_existing(
    project_name: str = typer.Argument(None, help="Project directory name (defaults to current directory)")
):
    """
    Run setup on an existing project.

    This is useful if you created a project without auto-setup
    or if the initial setup failed.
    """
    if not project_name:
        project_name = Path.cwd().name
        project_path = Path.cwd()
    else:
        project_path = Path(project_name)

    if not project_path.exists():
        console.print(f"[red]❌ Project directory '{project_name}' not found![/red]")
        raise typer.Exit(1)

    # Simple context for existing projects
    context = {
        "project_name": project_name,
        "auto_setup": True,
        "include_celery": (project_path / "docker-compose.yml").exists(),
        "include_database": (project_path / "docker-compose.yml").exists(),
    }

    success = run_post_setup(project_name=project_name, context=context)

    if not success:
        raise typer.Exit(1)


@app.command("features")
def list_features():
    """List all available features and their configurations"""
    table = Table(
        title="[bold cyan]Available Features[/bold cyan]",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Feature Key", style="cyan", no_wrap=True, width=25)
    table.add_column("Description", style="green")
    table.add_column("Options", style="yellow")
    table.add_column("Default", style="dim")

    for key, config in FEATURES.items():
        options_str = ", ".join(config.get('options', [])) if config.get('options') else "Yes/No"
        default_str = str(config.get('default', 'N/A'))
        table.add_row(key, config.get('question', ''), options_str, default_str)

    console.print(table)


@app.command()
def version():
    """Show version information"""
    from .. import __version__
    console.print(f" [bold]FastAPI generator v{__version__}[/bold]")


if __name__ == "__main__":
    app()