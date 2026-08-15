#!/usr/bin/env python
"""Local launch utility for SAGE Observatory read-only interface.

Executes standalone uvicorn local web server to display forensic state in browser.
"""

import sys
import uvicorn
from pathlib import Path

# Setup sys.path to resolve root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def launch():
    print("[*] Launching SAGE Observatory read-only forensic server...")
    print("[*] Opening local dashboard interface on http://localhost:8080")
    uvicorn.run("sage.experimental.observatory.server:app", host="127.0.0.1", port=8080, log_level="info")


if __name__ == "__main__":
    launch()
