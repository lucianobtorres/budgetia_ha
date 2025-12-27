# Stage 1: Build the React PWA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/pwa

# Install dependencies (caching layer)
COPY pwa/package.json pwa/package-lock.json ./
RUN npm ci

# Copy source and build
COPY pwa/ ./
# Build the PWA (Output usually in dist/)
RUN npm run build

# Stage 2: Python Backend & Runtime
FROM python:3.11-slim-bookworm

# Home Assistant Add-on Labels (Optional but good practice)
LABEL io.hass.version="1.0.0" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies (curl for healthcheck/poetry, git if needed, libmagic1 for python-magic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
# Remove lock file to force resolution (fixing dependency mismatch/ABI issues)
RUN rm poetry.lock && poetry install --only main --no-interaction --no-ansi --no-root

# Copy Backend Source
COPY src/ ./src/
COPY data/ ./data/
# Copy built frontend assets from Stage 1 to a serve directory
COPY --from=frontend-builder /app/pwa/dist /app/static

# Create entrypoint script
COPY scripts/run_addon.sh /run.sh
RUN chmod +x /run.sh

# Expose API port
EXPOSE 8000

# Volume for persistent data
VOLUME ["/data"]

CMD ["/run.sh"]
