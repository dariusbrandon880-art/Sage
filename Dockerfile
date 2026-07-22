# SAGE Autonomous Continuity Runtime Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    PORT=8000 \
    HOST=0.0.0.0

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python packaging files
COPY pyproject.toml README.md ./

# Install python dependencies in a single step (with dev/optional dependencies for tools integration)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir google-api-python-client google-auth-oauthlib google-auth-httplib2

# Copy repository source code
COPY sage/ ./sage/
COPY docs/ ./docs/

# Create persistent state directory for SAGE
RUN mkdir -p .sage sage_data

# Expose API service port
EXPOSE 8000

# Health check to ensure service is active
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production server
CMD ["uvicorn", "sage.api:app", "--host", "0.0.0.0", "--port", "8000"]
