# Stage 1: Frontend Build
FROM node:20-alpine as frontend
WORKDIR /app
RUN apk add --no-cache git
# CONFIGURATION: Cache Busting
# This instruction will INVALIDATE the cache if the main branch changes
ADD https://api.github.com/repos/lucianobtorres/BudgetIA/commits/main /tmp/git-hash
# Clone logic for Flat Structure
RUN git clone https://github.com/lucianobtorres/BudgetIA.git .
WORKDIR /app/pwa
RUN npm install
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.11-slim-bookworm

# Add-on Labels
LABEL io.hass.version="1.0.2" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

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
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# CACHE BUSTING for Backend
ADD https://api.github.com/repos/lucianobtorres/BudgetIA/commits/main /tmp/git-hash

# Clone the repository (Flat Structure)
RUN git clone https://github.com/lucianobtorres/BudgetIA.git .

# Install Dependencies (No lock file should exist in repo now, but we remove just in case)
RUN rm -f poetry.lock && poetry install --only main --no-interaction --no-ansi --no-root

# Copy built frontend assets from Stage 1
COPY --from=frontend /app/pwa/dist /app/static

# Ensure run script is executable (it's in budgetia/ so we might need to copy it or it comes from clone?)
# Since we moved run.sh to budgetia/ locally, but in the REPO it was at root?
# Check repo structure: current HEAD has run.sh at ROOT.
# Clone will bring run.sh to /app/run.sh.
# The `budgetia` folder in git is NEW (not pushed yet).
# So clone gets ROOT files.
# So run.sh is at /app/run.sh
RUN chmod +x run.sh

# Entrypoint
CMD ["./run.sh"]
