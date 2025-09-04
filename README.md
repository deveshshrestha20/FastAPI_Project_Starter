# FastAPI Project Starter

A powerful CLI tool for generating production-ready FastAPI projects with modern features and best practices.

[![PyPI version](https://img.shields.io/pypi/v/fastapi-project-starter.svg)](https://pypi.org/project/fastapi-project-starter/)
[![Python Support](https://img.shields.io/pypi/pyversions/fastapi-project-starter.svg)](https://pypi.org/project/fastapi-project-starter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **Database Support** - PostgreSQL + SQLAlchemy + Alembic migrations with async or sync support
- **Authentication** - JWT tokens + bcrypt + user management endpoints
- **Background Tasks** - Celery + Redis + task monitoring with Flower
- **Advanced Logging** - Loguru + structured logging + log rotation
- **Docker Ready** - Complete containerization with docker-compose setup
- **Modern Python** - Type hints, Pydantic v2, Python 3.8+ support

## Installation

```bash
  pip install fastapi-project-starter
```

## Quick Start

### Interactive Mode (Recommended)
```bash
  fastapi_generator new create my_test_app -i

```




## Usage

```bash
  fastapi_generator [COMMAND] [OPTIONS]

  Commands:
    new       Create a new FastAPI project
    version   Show current version

  Options:
    --help    Show help for the CLI or any subcommand

```



## After Generation

**Navigate and setup**:
   ```bash
      cd project_name
      make install
      make dev           # Build the docker containers
      make migrate       # Run initial migrations
   ```


**Access your API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Flower: http://localhost:5555
   - Mailpit: http://localhost:8025
   - Traefik Dashboard: http://localhost:8080

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

---

**FastAPI Project Starter** - From zero to production-ready FastAPI in seconds!