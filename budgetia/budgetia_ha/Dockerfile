# Stage 1: Build the React PWA (Cloning first)
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# Install git
RUN apk add --no-cache git

# Clone repository
RUN git clone https://github.com/lucianobtorres/BudgetIA.git .

WORKDIR /app/BudgetIA/pwa

# Install dependencies
RUN npm install

# Build PWA
RUN npm run build

# Stage 2: Python Backend & Runtime
FROM python:3.11-slim-bookworm

# Home Assistant Add-on Labels
# ... (labels remain same in original, but I must preserve lines or allow partial replace)
LABEL io.hass.version="1.0.0" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Clone Repository again (simplest way to get clean source without artifacts)
RUN git clone https://github.com/lucianobtorres/BudgetIA.git .

WORKDIR /app/BudgetIA

# Install Python dependencies
# Remove lock file to force resolution if needed, but repo has valid lock now.
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/BudgetIA/pwa/dist /app/static

# Copy launcher script (from the ADDON CONTEXT, not repo)
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose API port
EXPOSE 8000

# Volume for persistent data
VOLUME ["/data"]

CMD ["/run.sh"]
