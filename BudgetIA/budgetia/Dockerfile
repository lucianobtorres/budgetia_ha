# Stage 1: Frontend Build
FROM node:20-alpine as frontend
WORKDIR /app

# Copy PWA source code
COPY pwa /app/pwa

WORKDIR /app/pwa
RUN npm install
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.11-slim-bookworm

# Add-on Labels
LABEL io.hass.version="1.0.0" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy Backend Source Code (Using .dockerignore to exclude unnecessary files if needed)
# Since we are in the 'budgetia' context, we COPY . . which includes src, pwa(built), etc.
COPY . /app

# Install Dependencies
# We use the local poetry.lock/pyproject.toml found in /app
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy built frontend assets from Stage 1 into the static folder
COPY --from=frontend /app/pwa/dist /app/static

# Ensure run.sh is executable
RUN chmod +x /app/run.sh

# Entrypoint
CMD ["/app/run.sh"]
