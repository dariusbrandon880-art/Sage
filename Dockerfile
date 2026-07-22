# SAGE Production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first to leverage Docker cache
COPY pyproject.toml /app/

# Install the package and its production dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . /app/

# Expose port
EXPOSE 8000

# Run API server
CMD ["uvicorn", "sage.api:app", "--host", "0.0.0.0", "--port", "8000"]
