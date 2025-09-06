
"""
Post-project creation setup automation
"""

import subprocess
import os
import time
from pathlib import Path
from typing import Tuple, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


class SetupError(Exception):
    """Custom exception for setup errors"""
    pass


class PostSetupManager:
    """Manages post-project creation setup tasks"""

    def __init__(self, project_name: str, project_path: Path):
        self.project_name = project_name
        self.project_path = project_path
        self.original_dir = os.getcwd()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_dir)

    def run_command_with_spinner(
            self,
            command: List[str],
            description: str,
            timeout: int = 300
    ) -> Tuple[bool, str, str]:
        """
        Run a command with spinner animation and timeout
        """
        try:
            os.chdir(self.project_path)

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
            ) as progress:
                task = progress.add_task(description=description, total=None)

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                try:
                    stdout, stderr = process.communicate(timeout=timeout)

                    if process.returncode == 0:
                        progress.update(task, description=f"[green]✓[/green] {description}")
                        return True, stdout, stderr
                    else:
                        progress.update(task, description=f"[red]✗[/red] {description}")
                        return False, stdout, stderr

                except subprocess.TimeoutExpired:
                    process.kill()
                    progress.update(task, description=f"[yellow]⚠[/yellow] {description} (timed out)")
                    return False, "", "Command timed out"

        except Exception as e:
            console.print(f"[red]Error running command:[/red] {str(e)}")
            return False, "", str(e)
        finally:
            os.chdir(self.original_dir)

    def check_prerequisites(self) -> bool:
        """Check if required tools are available"""
        required_tools = ["make", "docker", "docker-compose"]
        missing_tools = []

        for tool in required_tools:

            try:
                result = subprocess.run([tool, "--version"], capture_output=True, timeout=5)
                if result.returncode != 0:
                    missing_tools.append(tool)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_tools.append(tool)

        if missing_tools:
            console.print("[red]❌ Missing required tools:[/red]")
            for tool in missing_tools:
                console.print(f"  • [bold]{tool}[/bold]")
            console.print("\nPlease install these tools before running auto-setup.")
            return False

        console.print("[green] All prerequisites available[/green]")
        return True

    def install_dependencies(self) -> bool:
        """Install project dependencies using make install"""
        console.print("\n[bold cyan] Installing Dependencies[/bold cyan]")

        success, stdout, stderr = self.run_command_with_spinner(
            ["make", "install"],
            "Installing dependencies with Poetry...",
            timeout=600  # 10 minutes for dependency installation
        )

        if success:
            console.print("[green] Dependencies installed successfully![/green]")
            return True
        else:
            console.print(f"[red]❌ Failed to install dependencies[/red]")
            if stderr:
                console.print(f"[red]Error details:[/red] {stderr}")
            return False

    def start_development_environment(self) -> bool:
        """Start development environment using make dev"""
        console.print("\n[bold cyan]🐋Starting Development Environment[/bold cyan]")

        success, stdout, stderr = self.run_command_with_spinner(
            ["make", "dev"],
            "Starting Docker containers...",
            timeout=180  # 3 minutes for Docker startup
        )

        if not success:
            console.print(f"[red]❌ Failed to start development environment[/red]")
            if stderr:
                console.print(f"[red]Error details:[/red] {stderr}")
            return False

        # Wait a bit for services to initialize
        console.print(" Waiting for services to start...")
        time.sleep(8)

        console.print("[green] Development environment started![/green]")
        return True

    def print_success_info(self, context: dict):
        """Print success information and next steps"""
        endpoints_table = Table(title=" Available Endpoints", show_header=True, header_style="bold magenta")
        endpoints_table.add_column("Service", style="cyan", no_wrap=True)
        endpoints_table.add_column("URL", style="green")
        endpoints_table.add_column("Description", style="dim")

        # Basic endpoints
        endpoints_table.add_row("API", "http://127.0.0.1:8000", "Main FastAPI application")
        endpoints_table.add_row("API Docs", "http://127.0.0.1:8000/docs", "Interactive API documentation")
        endpoints_table.add_row("Redoc", "http://127.0.0.1:8000/redoc", "Alternative API documentation")
        endpoints_table.add_row("Mailpit", "http://mailpit.localhost", "Email testing interface")
        endpoints_table.add_row("Traefik", "http://127.0.0.1:8080", "Traefik Dashboard")

        # Conditional endpoints
        if context.get("include_celery"):
            endpoints_table.add_row("Flower", "http://flower.localhost", "Celery task monitoring")

        console.print(endpoints_table)

        # Commands table
        commands_table = Table(title=" Useful Commands", show_header=True, header_style="bold magenta")
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="dim")

        commands_table.add_row("make dev", "Start development environment")
        commands_table.add_row("make down", "Stop all services")
        commands_table.add_row("make logs", "View application logs")
        commands_table.add_row("make db-shell", "Access DB shell")
        commands_table.add_row("make migrate", "Run migrations")
        commands_table.add_row("make migration", "Create new migration")
        commands_table.add_row("make clean", "Clean up environment")

        console.print(commands_table)

    def run_full_setup(self, context: dict) -> bool:
        """
        Run the complete post-creation setup process
        """
        console.print(Panel(
            f" Setting up [bold cyan]{self.project_name}[/bold cyan]...",
            title="Automatic Setup",
            border_style="blue"
        ))

        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                raise SetupError("Missing required tools")

            # Step 2: Install dependencies
            if not self.install_dependencies():
                raise SetupError("Failed to install dependencies")

            # Step 3: Start development environment
            if not self.start_development_environment():
                raise SetupError("Failed to start development environment")

            console.print(Panel(
                f"Project [bold cyan]'{self.project_name}'[/bold cyan] is fully set up and running!",
                title="[bold green]Setup Complete![/bold green]",
                border_style="green"
            ))

            self.print_success_info(context)
            return True

        except SetupError as e:
            console.print(Panel(
                f"[red]Setup failed: {str(e)}[/red]\n\n"
                "You can complete the setup manually:\n"
                f"1. [cyan]cd {self.project_name}[/cyan]\n"
                "2. [cyan]make install[/cyan]\n"
                "3. [cyan]make dev[/cyan]",
                title="[bold red]Setup Failed[/bold red]",
                border_style="red"
            ))
            return False

        except KeyboardInterrupt:
            console.print("\n[yellow]Setup interrupted by user[/yellow]")
            return False

        except Exception as e:
            console.print(Panel(
                f"[red]Unexpected error during setup: {str(e)}[/red]",
                title="[bold red]Setup Error[/bold red]",
                border_style="red"
            ))
            return False


def run_post_setup(project_name: str, context: dict) -> bool:
    """
    Main function to run post-project creation setup
    """
    if not context.get("auto_setup", False):
        console.print(f"[blue]⏭Skipping automatic setup for '{project_name}'[/blue]")
        _print_manual_instructions(project_name)
        return True

    project_path = Path(project_name)
    if not project_path.exists():
        console.print(f"[red] Project directory '{project_name}' not found![/red]")
        return False

    with PostSetupManager(project_name, project_path) as setup_manager:
        return setup_manager.run_full_setup(context)


def _print_manual_instructions(project_name: str):
    """Print manual setup instructions"""
    console.print(Panel(
        f" To set up your project manually:\n\n"
        f"1. Navigate to project: [cyan]cd {project_name}[/cyan]\n"
        f"2. Install dependencies: [cyan]make install[/cyan]\n"
        f"3. Start development: [cyan]make dev[/cyan]\n\n"
        f"Your API will be available at: [link=http://127.0.0.1:8000]http://127.0.0.1:8000[/link]",
        title="Manual Setup Instructions",
        border_style="yellow"
    ))