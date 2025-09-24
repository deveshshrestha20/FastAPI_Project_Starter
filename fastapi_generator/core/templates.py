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
        base_context = {
            "project_name": self.project_name,
            "project_slug": self._to_slug(self.project_name),
            "project_class": self._to_class_name(self.project_name),
            "author": "Your Name",
            "email": "your.email@example.com",
            "version": "0.1.0",
            "description": f"FastAPI project: {self.project_name}",
            "versions": DEFAULT_VERSIONS,
        }

        # Add feature defaults and convert is_async properly
        for key, config in FEATURES.items():
            if key == "is_async":
                # Convert string default to boolean
                base_context[key] = config['default'] == "async"
            else:
                base_context[key] = config['default']

        return base_context

    def _to_slug(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("-", "_")

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
        console.print("\n[bold]Configure Features:[/bold]")
        for key, feature in FEATURES.items():
            if feature.get("type") == "boolean":
                answer = Prompt.ask(
                    f"{feature['question']} (y/n)",
                    choices=["y", "n"],
                    default=feature['default']
                )
                self.context[key] = answer.lower() == "y"



        console.print("\n[green] Configuration completed![/green]\n")


class TemplateRenderer:
    """Render Jinja2 templates based on user-provided features"""

    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a single template with the provided context"""
        try:
            template = self.jinja_env.get_template(template_path)
            return template.render(**context)
        except Exception as e:
            console.print(f"[red]Error rendering template {template_path}: {e}[/red]")
            raise

    def get_template_mappings(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Determine which templates to render based on user's chosen features.
        Returns a mapping {template_path: destination_path}.
        """
        mappings = {}

        # Base templates - always included
        base_templates = [
            ("base/main.py.jinja", "app/main.py"),
            ("base/config.py.jinja", "app/core/config.py"),
            ("base/README.md.jinja", "README.md"),
            ("base/.gitignore.jinja", ".gitignore"),
            ("base/__init__.py.jinja", "app/__init__.py"),
            ("base/pyproject.toml.jinja", "pyproject.toml"),
            ("base/api_v1__init__.py.jinja", "app/api/v1/__init__.py"),
            ("base/.env.jinja", "envs/.env.local"),
        ]
        mappings.update(dict(base_templates))

        # Conditional templates based on user features
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

        if context.get("include_middlewares"):
            mappings.update({
                "middlewares/middleware_config.py.jinja": "app/middleware/config.py",
                "middlewares/__init__.py.jinja": "app/middleware/__init__.py",
                "middlewares/error_handling.py.jinja": "app/middleware/error_handling.py",
                "middlewares/request_id.py.jinja": "app/middleware/request_id.py",
                "middlewares/setup.py.jinja": "app/middleware/setup.py",
                "middlewares/timer.py.jinja": "app/middleware/timer.py",
            })

        if context.get("include_docker"):
            mappings.update({
                "docker/docker-compose.yml.jinja": "docker-compose.yml",
                "docker/fastapi/entrypoint.sh.jinja": "docker/fastapi/entrypoint.sh",
                "docker/fastapi/start.sh.jinja": "docker/fastapi/start.sh",
                "docker/fastapi/Dockerfile": "docker/fastapi/Dockerfile",
                "docker/traefik/traefik.yml.jinja": "docker/traefik/traefik.yml",
            })

            if context.get("include_database"):
                mappings["docker/postgres/Dockerfile.jinja"] = "docker/postgres/Dockerfile"

        if context.get("include_loguru"):
            mappings["base/loguru.py.jinja"] = "app/core/logger.py"

        if context.get("include_celery"):
            mappings.update({
                "celery/celery_app.py.jinja": "app/core/celery_app.py",
                "celery/tasks.py.jinja": "app/tasks/tasks.py",
                "celery/config.py.jinja": "app/tasks/email_config.py",
                "celery/email_base.py.jinja": "app/tasks/email_base.py",
                "template/welcome.html": "app/tasks/templates/welcome.html",
                "template/welcome.txt": "app/tasks/templates/welcome.txt",
                "template/password_reset.html": "app/tasks/templates/password_reset.html",
                "template/password_reset.txt": "app/tasks/templates/password_reset.txt",
            })

            # Celery Docker scripts (only if docker is enabled)
            if context.get("include_docker"):
                async_prefix = "async" if context.get("is_async") else "sync"
                mappings.update({
                    f"docker/fastapi/celery/{async_prefix}/worker/start.sh.jinja": "docker/fastapi/celery/worker/start.sh",
                    f"docker/fastapi/celery/{async_prefix}/beat/start.sh.jinja": "docker/fastapi/celery/beat/start.sh",
                    f"docker/fastapi/celery/{async_prefix}/flower/start.sh.jinja": "docker/fastapi/celery/flower/start.sh",
                })

        # Database templates based on async/sync mode
        if context.get("is_async"):
            mappings["async/async_db.py.jinja"] = "app/db/async_db.py"
        else:
            mappings.update({
                "sync/sync_db.py.jinja": "app/db/sync_db.py",
                "sync/session.py.jinja": "app/db/session.py",
                "sync/base.py.jinja": "app/db/base.py",
            })

        if context.get("include_Makefile"):
            mappings["Makefile.jinja"] = "Makefile"

        return mappings