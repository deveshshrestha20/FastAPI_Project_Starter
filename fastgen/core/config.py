from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Templates directory
TEMPLATES_DIR = PROJECT_ROOT / "templates"


FEATURES = {
    "include_database": {
        "question": "Do you want a database? (none/postgresql)",
        "options": ["none", "postgresql"],
        "default": "none",
    },
    "include_auth": {
        "question": "Do you want authentication? (y/n)",
        "options": ["y", "n"],
        "default": "n",
    },
    "include_docker": {
        "question": "Do you want Docker support? (y/n)",
        "options": ["y", "n"],
        "default": "n",
    },
    "include_celery": {
        "question": "Do you want Celery for background tasks? (y/n)",
        "options": ["y", "n"],
        "default": "n",
    },
    "async_mode": {
        "question": "Do you want async or sync code?",
        "options": ["async", "sync"],
        "default": "async",
    },
    "include_loguru": {
        "question": "Do you want loguru configuration? (y/n)",
        "options": ["y", "n"],
        "default": "y",
    }
}

# Database type configurations
DATABASE_CONFIGS = {
    "postgresql": {
        "dependencies": ["sqlalchemy", "asyncpg", "psycopg2-binary"],
        "url_template": "postgresql://user:password@localhost:5432/{project_slug}"
    }
}

# Default versions for dependencies
DEFAULT_VERSIONS = {
    "fastapi": "0.104.1",
    "uvicorn": "0.24.0",
    "pydantic": "2.5.0",
    "pydantic-settings": "2.1.0",
    "sqlalchemy": "2.0.23",
    "alembic": "1.12.1",
    "pytest": "7.4.3",
    "python": "3.11"
}