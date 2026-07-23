#!/usr/bin/env bash
# SAGE Production Activation and Startup Script

# Styling helpers
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

echo -e "${GREEN}=== SAGE AUTOMATED PRODUCTION ACTIVATION ===${RESET}"

# 1. Environment file setup
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] .env file not found. Copying .env.example to .env...${RESET}"
    cp .env.example .env
    echo -e "${YELLOW}[!] Copy complete. Review and update secret API keys in .env before live hosting.${RESET}"
fi

# 2. Load environment variables
echo -e "[*] Sourcing environment configuration..."
set -a
source .env
set +a

# 3. Execute Production Readiness Checker
echo -e "[*] Running comprehensive system and security checks..."
python3 scripts/production_check.py
CHECK_STATUS=$?

if [ $CHECK_STATUS -ne 0 ]; then
    echo -e "${RED}[✗] SAGE production checks failed. Startup aborted.${RESET}"
    exit 1
fi

echo -e "${GREEN}[✓] SAGE production readiness verified successfully.${RESET}"

# 4. Prompt / Run server launch command
echo -e "${GREEN}SAGE is ready for live activation!${RESET}"
echo -e "Launch command: ${YELLOW}uvicorn sage.api:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}${RESET}"
echo -e "Press Ctrl+C to stop the process once launched."
echo -e "============================================"
