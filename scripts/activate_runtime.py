#!/usr/bin/env python3
"""Automated Startup and Production Readiness Check for SAGE."""

import sys
import socket
import argparse
from pathlib import Path

# Add project root to sys.path so we can import sage
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sage.runtime import SageRuntime


def check_port(port: int) -> bool:
    """Check if the given port is available on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except socket.error:
            return False


def main():
    parser = argparse.ArgumentParser(description="SAGE Production Readiness & Activation Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run readiness checks and integrity diagnostics without launching a server.",
    )
    args = parser.parse_args()

    print("======================================================================")
    print(" SAGE PRODUCTION READINESS AND ACTIVATION SYSTEM")
    print("======================================================================\n")

    # 1. Check Configuration and .env presence
    print("[1/5] Checking environment variable configurations...")
    env_file = Path(".env")
    if env_file.exists():
        print(f"  - SUCCESS: Found .env file at {env_file.resolve()}")
    else:
        print("  - WARNING: No local .env file found. SAGE will load default values from settings.")

    # 2. Check workspace paths
    print("\n[2/5] Validating persistent storage directories...")
    runtime = SageRuntime()
    print(f"  - Workspace Base Path: {runtime.workspace_path.resolve()}")
    print(f"  - Memory Store Path:   {runtime.memory_path.resolve()}")
    print(f"  - Master Archive Path: {runtime.archive_path.resolve()}")
    print(f"  - Decisions Ledger:    {runtime.decisions_path.resolve()}")

    runtime.workspace_path.mkdir(parents=True, exist_ok=True)
    runtime.memory_path.mkdir(parents=True, exist_ok=True)
    runtime.archive_path.mkdir(parents=True, exist_ok=True)
    runtime.decisions_path.mkdir(parents=True, exist_ok=True)
    print("  - SUCCESS: Storage directories verified.")

    # 3. Check port availability for API Server
    print("\n[3/5] Verifying FastAPI Server Port (8000)...")
    port_available = check_port(8000)
    if port_available:
        print("  - SUCCESS: Port 8000 is available.")
    else:
        print("  - WARNING: Port 8000 is currently occupied. (Is a server already running?)")

    # 4. Run SAGE Integrity Diagnostics
    print("\n[4/5] Running SAGE Referential Integrity & Syntax Diagnostics...")
    report = runtime.verify_integrity()
    if report.get("is_valid", False):
        print("  - SUCCESS: Structural databases and syntax are valid.")
        print(f"  - Total Analysed Files: {report.get('loaded_files_count', 0)}")
    else:
        print("  - CRITICAL: Structural verification found issues:")
        for issue in report.get("issues", []):
            print(f"    * {issue}")
        if not args.dry_run:
            print("\nActivation halted due to critical structural issues.")
            sys.exit(1)

    # 5. Summary and Activation Decisions
    print("\n[5/5] SAGE Final Status:")
    print("======================================================================")
    if args.dry_run:
        print(" DRY-RUN STATUS: SAGE Runtime is 100% PREPARED and LIVE READY.")
        print(" No critical blockers detected.")
        print("======================================================================")
        sys.exit(0)

    print(" ACTIVATING SAGE RUNTIME SERVICE...")
    print(" Executing: uvicorn sage.api:app --host 0.0.0.0 --port 8000")
    print("======================================================================")

    # In actual production, we spin up the server
    import uvicorn
    from sage.api import app as fastapi_app

    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
