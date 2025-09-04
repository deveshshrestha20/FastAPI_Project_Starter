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



TEMPLATE_DIR = Path("templates")
TEMPLATE_FILE = "base/pyproject.toml.jinja"



# Target folder for new project
PROJECT_FOLDER = Path("my_test_app")
PROJECT_FOLDER.mkdir(parents=True, exist_ok=True)  # create folder if missing

# Output file path inside the new project folder
OUTPUT_FILE = PROJECT_FOLDER / "pyproject.toml"

# Create Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True)

# Load and render template
template = env.get_template(TEMPLATE_FILE)
rendered_output = template.render(**context)

# Write the output file inside my_test_app
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(rendered_output)

print(f"Generated {OUTPUT_FILE} successfully!")