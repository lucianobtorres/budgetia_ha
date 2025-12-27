# Stage 1: Frontend Build
FROM node:20-alpine as frontend
WORKDIR /app/pwa
# Copy frontend deps (relative to build context root)
COPY pwa/package.json pwa/package-lock.json ./
RUN npm install
# Copy frontend source
COPY pwa/ ./
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.11-slim-bookworm

# Add-on Labels
LABEL io.hass.version="1.0.1" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

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

# Copy Backend Dependencies
COPY pyproject.toml ./

# Install Dependencies (No lock file to avoid sync errors)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy Backend Source
COPY src/ ./src/
COPY data/ ./data/
# Copy Scripts folder if needed (though run.sh is separate now)
COPY scripts/ ./scripts/
# Copy Entrypoint Script (now at root of context)
COPY run.sh .

# Copy Frontend Assets to static dir (where main.py expects them)
# Check main.py to confirm it serves from /app/static?
# Previous run.sh export STATIC_DIR="/app/static".
COPY --from=frontend /app/pwa/dist /app/static

# Permission
RUN chmod +x run.sh

# Entrypoint
CMD ["./run.sh"]
