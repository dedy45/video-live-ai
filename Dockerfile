# syntax=docker/dockerfile:1
# AI Live Commerce Platform — GPU Docker Image
FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock* ./
RUN uv sync --extra gpu --no-dev --frozen 2>/dev/null || uv sync --extra gpu --no-dev

# Copy application code
COPY config/ config/
COPY src/ src/
COPY scripts/ scripts/
COPY data/schema.sql data/schema.sql
COPY .env.example .env.example

# Create data directories
RUN mkdir -p data/logs data/cache data/audio_cache

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/diagnostic/health || exit 1

EXPOSE 8001

# Default: production mode
ENV MOCK_MODE=false
CMD ["uv", "run", "python", "-m", "src.main"]
