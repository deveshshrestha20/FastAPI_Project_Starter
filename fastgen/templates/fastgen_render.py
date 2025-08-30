from jinja2 import Environment, FileSystemLoader
from pathlib import Path


# Project configuration / context
context = {
    "include_database": True,
    "database_type": "postgresql",
    "include_auth": True,
    "include_celery": True,
    "include_loguru": True
}


# Versions dictionary
versions = {
    "fastapi": "0.111.0",
    "uvicorn": "0.25.0",
    "pydantic": "2.5.1",
    "sqlalchemy": "2.1.1",
    "alembic": "2.0.2",
    "asyncpg": "0.27.0",
    "aiomysql": "0.0.22",
    "aiosqlite": "0.18.0",
    "passlib": "1.7.4",
    "python_jose": "3.3.0",
    "email_validator": "2.1.1",
    "celery": "5.5.0",
    "redis": "5.3.0",
    "loguru": "0.7.0"
}
TEMPLATE_DIR = Path("templates")  # Parent directory
TEMPLATE_FILE = "base/requirements.txt.jinja"
OUTPUT_FILE = Path("requirements.txt")


# Create Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Load and render template
template = env.get_template(TEMPLATE_FILE)
rendered_output = template.render(versions=versions, **context)

# Write output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(rendered_output)

print(f"Generated {OUTPUT_FILE} successfully!")
