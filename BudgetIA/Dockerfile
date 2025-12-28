# Stage 1: Frontend Build
FROM node:20-alpine as frontend
WORKDIR /app

# Copy PWA source code
COPY pwa /app/pwa

# Build PWA
WORKDIR /app/pwa
RUN npm install
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.12-slim

# Add-on Labels
LABEL io.hass.version="1.0.19" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app \
    STATIC_DIR="/app/static"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency definition
COPY pyproject.toml poetry.lock ./

# Install Backend Dependencies
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy Application Code
COPY src ./src
COPY planilha_mestra.xlsx .
COPY run.sh .

# Copy built frontend assets from Stage 1 into the static folder
COPY --from=frontend /app/pwa/dist /app/static

# Create data directory
RUN mkdir -p /app/data

# Make run script executable
RUN chmod +x run.sh

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["./run.sh"]
