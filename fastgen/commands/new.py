#!/usr/bin/env python3
"""
FastAPI Template Generator - Main CLI Command (Feature-based)
"""

from pathlib import Path
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from fastgen.core.utils import (
    create_directory_structure,
    create_init_files,
    cleanup_project,
    validate_project_name,
    write_file,
)
from ..core.config import FEATURES
from ..core.templates import TemplateRenderer, TemplateContext
from ..core.config import collect_postgresql_config

from rich.console import Console
console = Console()



class TemplateContext:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.context = {
            "project_name": project_name,
            "project_slug": project_name.lower().replace(" ", "_").replace("-", "_"),
            # Default values
            **{key: config['default'] for key, config in FEATURES.items()}
        }

    def add_metadata(self):
        console.print("\n[bold]Project Metadata:[/bold]")

        self.context["author_name"] = Prompt.ask(
            "Author name", default="Your Name"
        )
        self.context["author_email"] = Prompt.ask(
            "Author email", default="@gmail.com"
        )
        self.context["project_description"] = Prompt.ask(
            "Project description"
        )

    def add_interactive_context(self):
        """
        ### <-- ENHANCEMENT: This entire method is upgraded for a better interactive experience.
        """
        console.print("\n[bold]Configure your project features:[/bold]")

        for feature_key, feature_config in FEATURES.items():
            question = f"[bold spring_green3]?[/bold spring_green3] {feature_config['question']}"

            feature_type = feature_config.get("type", "boolean")

            # Use Confirm for simple Yes/No
            if feature_config['type'] == 'boolean':
                self.context[feature_key] = Confirm.ask(
                    question, default=feature_config['default']
                )
            # Use Prompt with choices for multiple options
            elif feature_config['type'] == 'choice':
                self.context[feature_key] = Prompt.ask(
                    question,
                    choices=feature_config['options'],
                    default=feature_config['default']
                )
        console.print("[green]✓ Feature configuration complete.[/green]")


# --------------------------------------------------------------------------------

app = typer.Typer(
    name="fastgen",
    help="FastAPI Template Generator - Create FastAPI projects quickly",
    rich_markup_mode="markdown"  # Enable rich markup in help text
)




class ProjectGenerator:
    """Main project generator class"""

    def __init__(self, project_name: str, interactive: bool = False):
        self.project_name = project_name
        self.project_path = Path.home() / "fastapi_test_projects" / project_name
        self.context_manager = TemplateContext(project_name)
        self.renderer = TemplateRenderer()

        if interactive:
            self.context_manager.add_metadata()
            self.context_manager.add_interactive_context()


    def create_project(self) -> None:
        """Create the complete project"""
        try:
            self._validate_project()
            self._create_project_directory()

            if self.context_manager.context.get("include_database"):
                console.print("\n[bold yellow]Database Configuration Required[/bold yellow]")
                db_config = collect_postgresql_config(
                    self.context_manager.context["project_slug"],
                    is_async=self.context_manager.context.get("is_async", True)
                )
                self.context_manager.context.update({
                    "database_url": db_config["database_url"],
                    "db_host": db_config["db_host"],
                    "db_port": db_config["db_port"],
                    "db_name": db_config["db_name"],
                    "db_user": db_config["db_user"],
                    "db_password": db_config["db_password"],
                })
                console.print("[green]✓ Database configuration completed[/green]\n")

            with Progress(
                    SpinnerColumn(spinner_name="dots"),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
            ) as progress:
                tasks = [
                    ("Creating folder structure...",
                     lambda: create_directory_structure(self.project_path, self.context_manager.context)),
                    ("Generating files from templates...", self._render_templates),
                    ("Creating __init__.py files...",
                     lambda: create_init_files(self.project_path, self.context_manager.context)),
                ]
                for desc, func in tasks:
                    task_id = progress.add_task(description=desc, total=None)
                    func()
                    progress.update(task_id, completed=1, description=f"[green]✓[/green] {desc}")

            self._show_success_message()

        except Exception as e:
            console.print(Panel(f"[bold red]An error occurred:[/bold red]\n{e}", title="Error", border_style="red"))
            cleanup_project(self.project_path)
            raise typer.Exit(1)

    def _validate_project(self) -> None:
        """Validate project name and check if directory exists"""
        if not validate_project_name(self.project_name):
            console.print(f"[red]Invalid project name: '{self.project_name}'[/red]")
            console.print(
                "[yellow]Project name must start with a letter and contain only letters, numbers, hyphens, and underscores.[/yellow]")
            raise typer.Exit(1)

        if self.project_path.exists():
            console.print(f"[yellow]Directory [bold]'{self.project_path}'[/bold] already exists.[/yellow]")
            if not Confirm.ask("[bold]Do you want to overwrite it?[/bold]", default=False):
                console.print("[red]Project creation aborted.[/red]")
                raise typer.Exit()
            console.print("[yellow]Overwriting existing project folder...[/yellow]")
            cleanup_project(self.project_path)

    def _create_project_directory(self) -> None:
        self.project_path.mkdir(parents=True)

    def _render_templates(self) -> None:
        mappings = self.renderer.get_template_mappings(self.context_manager.context)
        for template_file, output_file in mappings.items():
            content = self.renderer.render_template(template_file, self.context_manager.context)
            write_file(self.project_path / output_file, content)

    def _show_success_message(self) -> None:
        """
        ### <-- ENHANCEMENT: A much-improved success message panel.
        """

        project_name_str = self.project_name

        message = (
            f"✓ Project [bold cyan]'{project_name_str}'[/bold cyan] created successfully!\n\n"
            "[bold]Next Steps:[/bold]\n"
            f"  1. [cyan]cd {project_name_str}[/cyan]\n"
            "  2. [cyan]make install[/cyan]  # Install dependencies\n"
            "  3. [cyan]make dev[/cyan]      # Start development environment\n\n"
            "[bold]Your API will be available at:[/bold]\n"
            "  - [link=http://127.0.0.1:8000]http://127.0.0.1:8000[/link]\n"
            "  - [link=http://127.0.0.1:8000/docs]API Docs: http://127.0.0.1:8000/docs[/link]\n"
        )

        if self.context_manager.context.get("include_celery"):
            message += "  - [link=http://127.0.0.1:5555]Celery Monitor: http://127.0.0.1:5555[/link]\n"

        console.print(Panel(message, title=" [bold green]Success![/bold green] ", border_style="green"))


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
        title=" [bold]Fastgen Project Generator[/bold] ",
        border_style="blue"
    ))

    generator = ProjectGenerator(project_name, interactive)
    generator.create_project()


@app.command("features")
def list_features():
    """
    ### <-- ENHANCEMENT: Replaced the simple print loop with a beautiful rich.Table.
    """
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
    console.print(f"🚀 [bold]Fastgen v{__version__}[/bold]")


if __name__ == "__main__":
    app()