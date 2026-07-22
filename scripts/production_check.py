#!/usr/bin/env python3
"""SAGE Production Readiness & Safety Checker.

Runs a series of automated health and configuration checks to ensure SAGE Runtime is
fully prepared for secure, high-availability public internet hosting.
"""

import sys
import os
from pathlib import Path

# Print styling helpers
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_success(msg: str):
    print(f"{GREEN}[✓] {msg}{RESET}")


def print_warn(msg: str):
    print(f"{YELLOW}[!] {msg}{RESET}")


def print_error(msg: str):
    print(f"{RED}[✗] {msg}{RESET}")


def run_checks() -> bool:
    print("=" * 60)
    print(" SAGE PRODUCTION READINESS & HEALTH VERIFICATION")
    print("=" * 60)

    has_warnings = False
    has_errors = False

    # 1. Python Environment Check
    print("\n--- 1. Runtime Environment ---")
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    if py_major == 3 and py_minor >= 10:
        print_success(f"Python version is compatible: {sys.version.split()[0]}")
    else:
        print_error(f"Incompatible Python version: {sys.version.split()[0]}. Python 3.10+ required.")
        has_errors = True

    # 2. Check Package Dependencies
    try:
        import fastapi
        import pydantic
        import pydantic_settings
        print_success(f"FastAPI ({fastapi.__version__}) and Pydantic ({pydantic.__version__}) installed.")
    except ImportError as e:
        print_error(f"Missing core runtime dependency: {str(e)}")
        has_errors = True

    # Check Google API optional integrations
    try:
        import googleapiclient
        import google_auth_oauthlib
        print_success("Google Workspace API clients successfully verified.")
    except ImportError:
        print_warn("Google Workspace API packages are missing. Google Sync will use dry-run mode.")
        has_warnings = True

    # 3. Security & Authentication Boundaries
    print("\n--- 2. Security & Authentication ---")
    require_auth = os.getenv("SAGE_REQUIRE_AUTH", "false").lower() == "true"
    api_keys = os.getenv("SAGE_API_KEYS", "sage-default-key-2026")

    if not require_auth:
        print_warn("SAGE_REQUIRE_AUTH is set to 'false'. API endpoints are open without authentication.")
        has_warnings = True
    else:
        print_success("SAGE_REQUIRE_AUTH is enabled. Strict global API key verification active.")

    if api_keys == "sage-default-key-2026":
        print_error("SAGE_API_KEYS is using the default development key. Overwrite this in production!")
        has_errors = True
    elif len(api_keys.split(",")) >= 1 and api_keys.strip() != "":
        print_success("Custom SAGE_API_KEYS are securely configured.")
    else:
        print_error("SAGE_API_KEYS environment variable is empty or invalid.")
        has_errors = True

    # Check GitHub webhook secret security
    gh_webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not gh_webhook_secret:
        print_warn("GITHUB_WEBHOOK_SECRET is not set. GitHub webhooks will bypass signature verification.")
        has_warnings = True
    else:
        print_success("GITHUB_WEBHOOK_SECRET configured. HMAC-SHA256 payload signature validation active.")

    # 4. Storage & Directory Structure
    print("\n--- 3. File System & Persistent Directories ---")
    required_dirs = [
        Path("sage_data"),
        Path("sage_data/memory"),
        Path("sage_data/archive"),
        Path("sage_data/decisions"),
        Path(".sage"),
    ]

    for d in required_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = d / ".write_test"
            test_file.touch()
            test_file.unlink()
            print_success(f"Directory check: '{d}' is writeable and valid.")
        except Exception as e:
            print_error(f"Directory error on '{d}': {str(e)}")
            has_errors = True

    # Check for credentials file
    creds_path = Path(".sage/credentials.json")
    if creds_path.exists():
        print_success("Google Workspace credentials found at '.sage/credentials.json'.")
    else:
        print_warn("Google Workspace credentials missing at '.sage/credentials.json'. Only dry-run sync is possible.")
        has_warnings = True

    # 5. Final Decision
    print("\n" + "=" * 60)
    if has_errors:
        print_error("SAGE STATUS: NOT READY FOR PRODUCTION DUE TO CORE CONFIGURATION ERRORS.")
        print("Please correct the errors above and run again.")
        print("=" * 60)
        return False
    elif has_warnings:
        print_warn("SAGE STATUS: READY WITH WARNINGS.")
        print("SAGE is functional, but review warnings for optimal production security/integration.")
        print("=" * 60)
        return True
    else:
        print_success("SAGE STATUS: FULLY PROVISIONED AND READY FOR SECURE PRODUCTION DEPLOYMENT!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
