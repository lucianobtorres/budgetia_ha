# Builder and Runtime in one (Simplificando como sugerido)
FROM python:3.12-slim

# Add-on Labels
LABEL io.hass.version="1.0.18" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (sem pinagem estrita de versao, pois usaremos 'install', nao 'export')
RUN pip install poetry

# Copy dependency definition
COPY pyproject.toml poetry.lock ./

# Install Dependencies directly (Global)
# --only main: apenas deps de prod
# --no-root: não instala o próprio pacote budgetia (pois copiamos src manualmente)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy Application Code
COPY src ./src
COPY pwa ./pwa
COPY planilha_mestra.xlsx .
COPY run.sh .

# Create data directory
RUN mkdir -p /app/data

# Make run script executable
RUN chmod +x run.sh

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["./run.sh"]
