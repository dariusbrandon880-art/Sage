# SAGE Autonomous Continuity Runtime Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir google-api-python-client google-auth-oauthlib google-auth-httplib2

COPY sage/ ./sage/
COPY scripts/ ./scripts/
COPY docs/ ./docs/
COPY evidence_capture/ ./evidence_capture/

RUN mkdir -p .sage sage_data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python scripts/run_openai_runtime_activation.py && uvicorn sage.experimental.observatory.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
