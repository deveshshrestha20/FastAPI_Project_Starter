import getpass
from pathlib import Path
from urllib.parse import quote_plus

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# ------------------------------
# Project Directories
# ------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

console = Console()

# ------------------------------
# Features / Options
# ------------------------------
FEATURES = {
    "include_database": {
        "question": "Do you want a database?",
        "options": ["y", "n"],
        "default": "n",
        "type": "boolean",
    },
    "include_auth": {
        "question": "Do you want authentication? (y/n)",
        "options": ["y", "n"],
        "default": "n",
        "type": "boolean",
    },
    "include_middlewares": {
        "question": "Do you want middlewares( CORS, RequestID , Error Handling ) ? (y/n)",
        "options": ["y", "n"],
        "default": "y",
        "type": "boolean",
    },
    "include_docker": {
        "question": "Do you want Docker support? (y/n)",
        "options": ["y", "n"],
        "default": "n",
        "type": "boolean",
    },
    "include_celery": {
        "question": "Do you want Celery for background tasks? (y/n)",
        "options": ["y", "n"],
        "default": "n",
        "type": "boolean",
    },
    "is_async": {
        "question": "Do you want async(y) or sync(n) code?",
        "options": ["y", "n"],
        "default": "y",
        "type": "boolean",
    },
    "include_loguru": {
        "question": "Do you want loguru configuration? (y/n)",
        "options": ["y", "n"],
        "default": "y",
        "type": "boolean",
    },
    "include_Makefile": {
        "question": "Do you want Makefile? (y/n)",
        "options": ["y", "n"],
        "default": "y",
        "type": "boolean",
    }
}

# ------------------------------
# PostgreSQL Configuration
# ------------------------------
POSTGRESQL_CONFIG = {
    "dependencies": ["sqlalchemy", "asyncpg", "psycopg"],
    "async_url_template": "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
    "sync_url_template": "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}",
    "default_port": "5432"
}


# ------------------------------
# Collect PostgreSQL Config
# ------------------------------
def collect_postgresql_config(project_slug: str, is_async: bool = True) -> dict:
    title = "[bold cyan]POSTGRESQL CONFIGURATION[/bold cyan]"
    console.print(
        Panel(
            "Fill in your database details below.\n"
            "Password input will be hidden.",
            title=title,
            expand=False,
            border_style="bright_blue"
        )
    )

    host = Prompt.ask("Database host", default="localhost")
    port = Prompt.ask("Database port", default="5432")
    database = Prompt.ask("Database name", default=f"{project_slug}_db")
    user = Prompt.ask("Database username", default="postgres")

    password = getpass.getpass("Enter password: ")

    if not password:
        use_empty = Prompt.ask("Use empty password? [y/n]", default="n").lower().startswith("y")
        if not use_empty:
            password = getpass.getpass("Please enter a password: ")

    console.print("\n[green] Database configuration completed[/green]")

    encoded_password = quote_plus(password)
    url_template = POSTGRESQL_CONFIG["async_url_template"] if is_async else POSTGRESQL_CONFIG["sync_url_template"]
    database_url = url_template.format(user=user, password=encoded_password, host=host, port=port, database=database)

    return {
        "database_url": database_url,
        "dependencies": POSTGRESQL_CONFIG["dependencies"],
        "db_host": host,
        "db_port": port,
        "db_name": database,
        "db_user": user,
        "db_password": password
    }



# Auto-Setup Configuration

def collect_auto_setup_config(context: dict) -> dict:
    """
    Ask user about auto-setup after all other configuration is complete
    """
    console.print("\n" + "=" * 60)
    console.print(Panel(
        "[bold cyan] AUTOMATIC SETUP[/bold cyan]\n\n"
        "After creating your project, the following will be done automatically:\n\n"
        "  1. Install dependencies with Poetry\n"
        "  2. Start the Docker development environment\n"
        "  3. Launch all required services\n\n"
        "[dim]This requires Docker and Make to be installed on your system.[/dim]",
        title="Post-Creation Setup",
        expand=False,
        border_style="bright_green"
    ))

    auto_setup = Confirm.ask(
        "Do you want to automatically install dependencies and start the development environment?",
        default=True
    )

    context["auto_setup"] = auto_setup

    if auto_setup:
        console.print("[green] Automatic setup will begin after project creation.[/green]")
    else:
        console.print(Panel(
            "[yellow]Automatic setup disabled.[/yellow]\n\n"
            "You'll need to run these commands manually:\n"
            f"  [cyan]cd {context.get('project_name', 'your_project')}[/cyan]\n"
            "  [cyan]make install[/cyan]\n"
            "  [cyan]make dev[/cyan]",
            title="Manual Setup Required",
            border_style="yellow"
        ))

    return context

    # Interactive Configuration
def collect_interactive_configuration(project_name: str) -> dict:
    """
    Collect all interactive configuration including auto-setup
    """
    context = {"project_name": project_name}

    # Basic project configuration
    console.print(Panel(
        "Configure your FastAPI project features:",
        title="[bold]Project Configuration[/bold]",
        border_style="blue"
    ))

    # Collect standard features
    for key, config in FEATURES.items():
        if config["type"] == "boolean":
            default_value = config["default"] == "y"
            response = Confirm.ask(config["question"], default=default_value)
            context[key] = response

    # Database configuration if enabled
    if context.get("include_database"):
        db_config = collect_postgresql_config(
            project_name.lower().replace("-", "_").replace(" ", "_"),
            is_async=context.get("is_async", True)
        )
        context.update(db_config)

    # Auto-setup configuration (comes last)
    context = collect_auto_setup_config(context)

    return context

DEFAULT_VERSIONS = {
    # Base packages
    "fastapi": "0.104.1",
    "uvicorn": "0.24.0",
    "pydantic": "2.5.0",

    # PostgreSQL packages
    "sqlalchemy": "2.0.23",
    "alembic": "1.12.1",
    "asyncpg": "0.29.0",

    # Authentication packages
    "passlib": "1.7.4",
    "python_jose": "3.3.0",
    "email_validator": "2.1.0",

    # Celery / Redis / Other
    "celery": "5.3.4",
    "redis": "5.0.1",
    "loguru": "0.7.2"
}