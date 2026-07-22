# Multi-stage build for SAGE Runtime v1
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY sage/ ./sage

# Build wheel package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build && \
    python -m build --wheel

# Final production image
FROM python:3.12-slim

WORKDIR /app

# Non-root user for security
RUN groupadd -r sage && useradd -r -g sage sage

# Install curl for health checking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl ./

# Install the built package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir *.whl && \
    rm *.whl

# Setup directories for state persistence and ownership
RUN mkdir -p /app/.sage && chown -R sage:sage /app/.sage

USER sage

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Healthcheck to verify live REST API status
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "sage.api:app", "--host", "0.0.0.0", "--port", "8000"]
