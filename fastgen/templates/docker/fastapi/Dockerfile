ARG PYTHON_VERSION=3.11.8
FROM python:${PYTHON_VERSION}-slim-bookworm

ARG APP_HOME=/app
ARG APP_USER=fastapi
ARG APP_GROUP=fastapi

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=${APP_HOME} \
    POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_VENV_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    C_FORCE_ROOT=1

WORKDIR ${APP_HOME}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    netcat-openbsd \
    gettext \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and install dependencies globally
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    rm -rf /tmp/poetry_cache \

# Create user and set permissions
RUN groupadd -r ${APP_GROUP} && \
    useradd -r -g ${APP_GROUP} -d ${APP_HOME} -m ${APP_USER}

RUN mkdir -p ${APP_HOME}/logs && \
    chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}/logs && \
    chmod 775 ${APP_HOME}/logs

# Copy main scripts
COPY --chown=${APP_USER}:${APP_GROUP} ./docker/fastapi/entrypoint.sh /entrypoint.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./docker/fastapi/start.sh /start.sh

# Copy Celery scripts and create directory structure
COPY --chown=${APP_USER}:${APP_GROUP} ./docker/fastapi/celery/ /docker/fastapi/celery/

# Make all scripts executable
RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh && \
    chmod +x /entrypoint.sh /start.sh && \
    find /docker/fastapi/celery/ -name "*.sh" -exec chmod +x {} \; && \
    find /docker/fastapi/celery/ -name "*.sh" -exec sed -i 's/\r$//g' {} \;

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

USER ${APP_USER}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/start.sh"]