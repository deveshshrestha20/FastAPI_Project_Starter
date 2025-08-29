from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.prompt import Prompt

from .config import TEMPLATES_DIR, FEATURES, DEFAULT_VERSIONS

console = Console()


class TemplateContext:
    """Manages project context and user-provided features"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.context: Dict[str, Any] = self._build_base_context()

    def _build_base_context(self) -> Dict[str, Any]:
        """Initialize base context with defaults"""
        return {
            "project_name": self.project_name,
            "project_slug": self._to_slug(self.project_name),
            "project_class": self._to_class_name(self.project_name),
            "author": "Your Name",
            "email": "your.email@example.com",
            "version": "0.1.0",
            "description": f"FastAPI project: {self.project_name}",
            "is_async": True,  # default
            "include_database": False,
            "database_type": None,
            "database_url": "",
            **DEFAULT_VERSIONS,
        }

    def _to_slug(self, name: str) -> str:
        return name.lower().replace(" ", "-").replace("_", "-")

    def _to_class_name(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("-", " ").replace("_", " ").split())

    def add_interactive_context(self) -> None:
        """Ask the user for feature options interactively"""
        console.print("\n[bold blue]Project Configuration[/bold blue]\n")

        # Basic metadata
        self.context["author"] = Prompt.ask("Author name", default=self.context["author"])
        self.context["email"] = Prompt.ask("Author email", default=self.context["email"])
        self.context["description"] = Prompt.ask("Project description", default=self.context["description"])

        # Features
        for key, feature in FEATURES.items():
            answer = Prompt.ask(
                feature["question"],
                choices=feature["options"] if feature["options"] else None,
                default=feature["default"]
            )

            if key == "include_database":
                if answer == "none":
                    self.context["include_database"] = False
                    self.context["database_type"] = None
                    self.context["database_url"] = ""
                else:
                    self.context["include_database"] = True
                    self.context["database_type"] = answer
                    self._update_database(answer)

            elif key == "async_mode":
                self.context["is_async"] = answer == "async"
            else:
                self.context[key] = answer.lower() in ["y", "yes"]

        console.print("\n[green]✅ Configuration completed![/green]\n")

    def _update_database(self, db_type: str) -> None:
        """Update database-specific configuration"""
        if db_type == "postgresql":
            self.context["database_url"] = "postgresql+asyncpg://user:password@localhost:5432/dbname"
        else:
            self.context["database_url"] = ""

class TemplateRenderer:
    """Render Jinja2 template based on the user provided features."""

    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a single template with the provided context."""
        try:
            template = self.jinja_env.get_template(template_path)
            return template.render(**context)
        except Exception as e:
            console.print(f"[red]Error rendering template {template_path}: {e}[/red]")
            raise

    def get_template_mappings(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Determine which templates to render based on the user's chosen features. Returns a mapping {template_path: destination_path}.
        """
        mappings = {}

        # Base templates - They are always included
        base_templates = [
            ("base/main.py.jinja", "app/main.py"),
            ("base/config.py.jinja", "app/core/config.py"),
            ("base/requirements.txt.jinja", "requirements.txt"),
            ("base/README.md.jinja", "README.md"),
            ("base/.gitignore.jinja", ".gitignore"),
            ("base/__init__.py.jinja", "app/__init__.py"),
        ]
        mappings.update(dict(base_templates))

        # Conditional templates based on provided user features
        if context.get("include_database"):
            mappings.update({
                "base/database.py.jinja": "app/db/database.py",
                "base/models.py.jinja": "app/models/__init__.py",
                "base/schemas.py.jinja": "app/schemas/__init__.py",
            })

        if context.get("include_auth"):
            mappings.update({
                "base/auth.py.jinja": "app/auth/auth.py",
                "base/security.py.jinja": "app/core/security.py",
            })

        if context.get("include_docker"):
            mappings.update({
                "base/Dockerfile.jinja": "Dockerfile",
                "base/docker-compose.yml.jinja": "docker-compose.yml",
            })

        if context.get("include_tests"):
            mappings.update({
                "base/test_main.py.jinja": "tests/test_main.py",
                "base/test.py.jinja": "tests/test.py",
            })

        if context.get("include_loguru"):
            mappings["base/loguru.py.jinja"] = "app/core/logger.py"

        if context.get("include_celery"):
            mappings.update({
                "base/celery_app.py.jinja": "app/worker/celery_app.py",
                "base/tasks.py.jinja": "app/tasks/example_tasks.py",
            })

        if context.get("is_async"):
            mappings.update({
                "async/async_db.py.jinja": "app/db/async_db.py",
            })
        else:
            mappings.update({
                "sync/sync_db.py.jinja": "app/db/sync_db.py",
                "sync/session.py.jinja": "app/db/session.py",
                "sync/base.py.jinja": "app/db/base.py",
            })

        return mappings
