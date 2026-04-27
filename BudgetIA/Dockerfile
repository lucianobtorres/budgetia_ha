# Stage 1: Frontend Build (PWA)
FROM node:20-alpine as frontend
WORKDIR /app/pwa
COPY pwa/package*.json ./
RUN npm install
COPY pwa/ ./
RUN npm run build

# Stage 2: Backend & Final Image
FROM python:3.12-slim

# Add-on Metadata
LABEL io.hass.version="1.0.66" \
      io.hass.type="addon" \
      io.hass.arch="armhf|aarch64|i386|amd64"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app/src \
    STATIC_DIR="/app/static"

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency definition and lock
COPY pyproject.toml poetry.lock ./

# Install Production Dependencies
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy Application Code
COPY src ./src
COPY run.sh .

# Copy built frontend assets from Stage 1
COPY --from=frontend /app/pwa/dist /app/static

# Prepare directories and permissions
RUN mkdir -p /app/data && chmod +x run.sh

# Expose API port
EXPOSE 8000

# Entrypoint handles services orchestration (API, Scheduler, Bot)
CMD ["./run.sh"]
