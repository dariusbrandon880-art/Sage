#!/usr/bin/env bash
# SAGE Production Run Script
# Automates configuration checks, workspace verification, and boots the production uvicorn server.

echo "SAGE: Running configuration check..."
if [ ! -f .env ]; then
    echo "SAGE: [ERROR] '.env' configuration file is missing!"
    echo "SAGE: Copy '.env.example' to '.env' and populate your API credentials to start."
    exit 1
fi

echo "SAGE: Running workspace convergence checks..."
python scripts/verify_convergence.py
VERIFY_RESULT=$?

if [ $VERIFY_RESULT -ne 0 ]; then
    echo "SAGE: [ERROR] Convergence and integrity checks failed! Aborting startup."
    exit 1
fi

echo "SAGE: Workspace verified successfully. Booting production API server..."

# Read port and host from env, default if not specified
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

# Launch Uvicorn server in multi-worker production mode
python -m uvicorn sage.api:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers 4 \
    --log-config logging_config.json 2>/dev/null || \
python -m uvicorn sage.api:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers 4
