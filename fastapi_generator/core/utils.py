import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console

console = Console()


def create_directory_structure(project_path: Path, context: Dict[str, Any]) -> List[str]:
    """Create the folder structure based on template features"""

    # Base folders (always created)
    base_folders = [
        "app",
        "app/api",
        "app/api/v1",
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "tests",
    ]

    # Add conditional folders
    conditional_folders = []

    if context.get("include_database"):
        conditional_folders.extend([
            "app/db",
            "alembic",
            "alembic/versions"
        ])

    if context.get("include_auth"):
        conditional_folders.extend([
            "app/auth",
        ])

    if context.get("include_middlewares"):
        conditional_folders.extend([
            "app/middleware",
        ])

    if context.get("include_docker"):
        conditional_folders.extend([
            "docker",
            "docker/fastapi",
            "docker/postgres",
            "docker/traefik",
        ])

        # Add PostgreSQL docker folder if database is included
        if context.get("include_database") and context.get("database_type") == "postgresql":
            conditional_folders.append("docker/postgres")

    if context.get("include_celery"):
        conditional_folders.extend([
            "app/tasks",
            "app/tasks/templates",
        ])

        if context.get("include_docker"):
            conditional_folders.extend([
                "docker/fastapi/celery",
                "docker/fastapi/celery/beat",
                "docker/fastapi/celery/flower",
                "docker/fastapi/celery/worker"
            ])


    # Combine all folders
    all_folders = base_folders + conditional_folders

    # Create each folder
    for folder in all_folders:
        folder_path = project_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Create default env files inside envs folder
    create_env_files(project_path / "envs")

    return all_folders

def create_env_files(env_folder: Path) -> None:
    """
    Create the default environment files inside the envs folder:
    - .env.local
    - .env.example
    - .env.production
    """
    env_folder.mkdir(parents=True, exist_ok=True)

    env_files = {
        ".env.local": "# Local environment variables\n",
        ".env.production": "# Production environment variables\n"
    }

    for file_name, content in env_files.items():
        file_path = env_folder / file_name
        if not file_path.exists():  # avoid overwriting existing files
            file_path.write_text(content, encoding="utf-8")

def write_file(file_path: Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed"""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Make shell scripts executable
    if file_path.suffix == '.sh':
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(file_path, 0o755)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


def create_init_files(project_path: Path, context: Dict[str, Any]) -> None:
    """Create empty __init__.py files in Python packages"""
    init_files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/core/__init__.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "tests/__init__.py",
    ]


    if context.get("include_auth"):
        init_files.append("app/auth/__init__.py")

    if context.get("include_celery"):
        init_files.extend([
            "app/tasks/__init__.py",
        ])

    # Create each init file
    for init_file in init_files:
        init_path = project_path / init_file
        write_file(init_path, "")


def cleanup_project(project_path: Path) -> None:
    """Clean up project directory on error"""
    if project_path.exists():
        shutil.rmtree(project_path)
        console.print(f"[yellow]Cleaned up incomplete project: {project_path}[/yellow]")


def validate_project_name(project_name: str) -> bool:
    """Validate project name for legal filesystem and Python package names"""
    import re

    # Check for valid Python identifier (with hyphens allowed)
    pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$'

    if not re.match(pattern, project_name):
        return False

    # Check for reserved Python keywords
    import keyword
    slug = project_name.lower().replace("-", "_")
    if keyword.iskeyword(slug):
        return False

    return True