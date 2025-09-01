#!/usr/bin/env python3
"""
FastAPI Template Generator - Main CLI Command (Feature-based)
"""

from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Confirm

from fastgen.core.utils import (
    create_directory_structure,
    create_init_files,
    cleanup_project,
    validate_project_name,
    write_file,
)
from ..core.config import FEATURES
from ..core.templates import TemplateRenderer, TemplateContext
from ..core.config import collect_postgresql_config, generate_env_file  # <- Import DB helpers

app = typer.Typer(
    name="fastgen",
    help="FastAPI Template Generator - Create FastAPI projects quickly"
)

console = Console()


class ProjectGenerator:
    """Main project generator class"""

    def __init__(self, project_name: str, interactive: bool = False):
        self.project_name = project_name
        self.interactive = interactive
        self.project_path = Path.home() / "fastapi_test_projects" / project_name

        # Initialize feature-driven context
        self.context_manager = TemplateContext(project_name)
        self.renderer = TemplateRenderer()

        # Ask user interactively for feature configuration if requested
        if interactive:
            self.context_manager.add_interactive_context()

    def create_project(self) -> None:
        """Create the complete project"""
        try:
            self._validate_project()
            self._create_project_directory()

            # Collect database config if database feature is enabled
            if self.context_manager.context.get("include_database"):
                console.print("\n[bold yellow]Database Configuration Required[/bold yellow]")
                db_config = collect_postgresql_config(
                    self.context_manager.context["project_slug"],
                    is_async=self.context_manager.context.get("is_async", True)
                )

                # Add database config to template context
                self.context_manager.context.update({
                    "database_url": db_config["database_url"],
                    "db_host": db_config["db_host"],
                    "db_port": db_config["db_port"],
                    "db_name": db_config["db_name"],
                    "db_user": db_config["db_user"],
                    "db_password": db_config["db_password"],
                })

                console.print("[green]✓ Database configuration completed[/green]\n")

            # ----------------------------
            # Progress spinner for file operations
            # ----------------------------
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
            ) as progress:

                progress.add_task("Creating folder structure...", total=None)
                create_directory_structure(self.project_path, self.context_manager.context)

                progress.add_task("Generating files from templates...", total=None)
                self._render_templates()

                progress.add_task("Creating additional files...", total=None)
                create_init_files(self.project_path, self.context_manager.context)

            self._show_success_message()

        except Exception as e:
            console.print(f"[red]Error creating project: {str(e)}[/red]")
            cleanup_project(self.project_path)
            raise typer.Exit(1)

    def _validate_project(self) -> None:
        """Validate project name and check if directory exists"""
        if not validate_project_name(self.project_name):
            console.print(f"[red]Invalid project name: {self.project_name}[/red]")
            console.print(
                "[yellow]Project name must start with a letter and contain only letters, numbers, hyphens, and underscores[/yellow]"
            )
            raise typer.Exit(1)

        if self.project_path.exists():
            console.print(f"[yellow]Directory already exists: {self.project_path}[/yellow]")

            # Ask user whether to overwrite
            if Confirm.ask("Do you want to overwrite it?"):
                console.print("[yellow]Deleting existing project folder...[/yellow]")
                cleanup_project(self.project_path)
            else:
                console.print("[red]Project creation aborted.[/red]")
                raise typer.Exit(1)

    def _create_project_directory(self) -> None:
        """Create the main project directory"""
        self.project_path.mkdir(parents=True)

    def _render_templates(self) -> None:
        """Render all templates and write to files"""
        mappings = self.renderer.get_template_mappings(self.context_manager.context)
        for template_file, output_file in mappings.items():
            try:
                content = self.renderer.render_template(template_file, self.context_manager.context)
                output_path = self.project_path / output_file
                write_file(output_path, content)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not process template {template_file}: {e}[/yellow]")

    def _show_success_message(self) -> None:
        """Show project creation success message"""
        next_steps = [
            f"cd {self.project_name}",
            "python -m venv venv",
            "source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
            "pip install -r requirements.txt"
        ]

        if self.context_manager.context.get("include_database"):
            next_steps.extend([
                "cp envs/.env.local .env",
                "# Configure your database settings in .env",
                "alembic upgrade head"
            ])

        next_steps.append("uvicorn app.main:app --reload")

        console.print(Panel.fit(
            f"[green]✓ Successfully created FastAPI project: {self.project_name}[/green]\n\n"
            f"[bold]Next steps:[/bold]\n" +
            "\n".join(f"  {step}" for step in next_steps) +
            f"\n\n[dim]Visit: http://127.0.0.1:8000[/dim]\n"
            f"[dim]API docs: http://127.0.0.1:8000/docs[/dim]\n\n",
            title="Project Created Successfully"
        ))


@app.command()
def create(
        project_name: str = typer.Argument(..., help="Name of the FastAPI project to create"),
        interactive: bool = typer.Option(False, "--interactive", "-i",
                                         help="Interactive mode for project configuration")
):
    """Create a new FastAPI project"""
    console.print(Panel.fit(
        f"[bold blue]FastAPI Template Generator[/bold blue]\n\n"
        f"[bold]Project:[/bold] {project_name}\n"
        f"[bold]Interactive:[/bold] {'Yes' if interactive else 'No'}",
        title="Creating FastAPI Project"
    ))

    generator = ProjectGenerator(project_name, interactive)
    generator.create_project()


@app.command("features")
def list_features():
    """List all available features that can be configured"""
    console.print("[bold]Available Features:[/bold]\n")
    for feature_key, feature_config in FEATURES.items():
        console.print(f"[green]{feature_key:20}[/green] {feature_config['question']}")
        if feature_config['options']:
            console.print(f"{'':20} Options: {', '.join(feature_config['options'])}")
            console.print(f"{'':20} Default: {feature_config['default']}")
        console.print()


@app.command()
def version():
    """Show version information"""
    from .. import __version__
    console.print(f"FastAPI Template Generator v{__version__}")


if __name__ == "__main__":
    app()