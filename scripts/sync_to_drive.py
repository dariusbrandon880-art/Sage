#!/usr/bin/env python3
"""SAGE Google Drive Projection Synchronizer.

Syncs the local 8 canonical SAGE projection files to Google Drive,
exposing detailed diagnostics and stale/conflict checks.
"""

import argparse
import json
import sys
from pathlib import Path

# Adjust path to import sage modules correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sage.integration import GoogleDriveProjectionSyncManager


def main():
    parser = argparse.ArgumentParser(description="SAGE Google Drive Projection Synchronizer")
    parser.add_argument(
        "--credentials",
        "-c",
        type=str,
        default=".sage/credentials.json",
        help="Path to the Google credentials JSON file."
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default="SAGE",
        help="Path to local projection directory (default: SAGE)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force execution in dry-run mode."
    )

    args = parser.parse_args()

    print("============================================================")
    print(" SAGE GOOGLE DRIVE CONTINUITY PROJECTION SYNC")
    print("============================================================")

    sync_mgr = GoogleDriveProjectionSyncManager()

    if args.dry_run:
        # To force dry run, we can pass a dummy non-existent credentials path
        print("[!] Forcing dry-run mode via argument.")
        creds_path = "non_existent_dry_run_forced.json"
    else:
        creds_path = args.credentials

    # Execute sync pipeline
    result = sync_mgr.sync_projection_to_drive(
        credentials_path=creds_path,
        target_dir=args.dir
    )

    mode = result.get("mode", "unknown")
    status = result.get("status", "unknown")
    reason = result.get("reason", "N/A")

    print(f"\n--- Execution Mode: {mode.upper()} ---")
    print(f"Status: {status.upper()}")
    print(f"Reason: {reason}")

    # Display conflict / stale checks
    conflict_info = result.get("stale_conflict_check", {})
    print("\n--- Projection Integrity Handshake ---")
    print(f"Local HEAD SHA:  {conflict_info.get('local_head_sha')}")
    print(f"Remote HEAD SHA: {conflict_info.get('remote_head_sha')}")
    print(f"Handshake Status: {conflict_info.get('status')}")

    # If dry-run, output instructions and setup needs
    if mode == "dry-run":
        print("\n--- Setup & Dependency Diagnostics ---")
        requirements = result.get("setup_requirements", {})
        print(f"Required Scopes: {result.get('required_scopes')}")
        print("Required Packages:")
        for pkg in requirements.get("packages_to_install", []):
            print(f"  - {pkg}")
        print(f"How to Install:   {requirements.get('how_to_install')}")
        print(f"Credentials Setup: {requirements.get('oauth_credentials_json')}")

    # Print files status map
    print("\n--- Projection Files Map ---")
    if mode == "dry-run":
        files_list = result.get("synced_files", [])
        for f in files_list:
            status_char = "✓" if f.get("exists_locally") else "✗"
            print(f"  [{status_char}] {f.get('filename'):<30} (Size: {f.get('character_count'):>5} chars, SHA-256: {f.get('local_sha256')[:12]}...)")
    else:
        # Live sync
        live_files = result.get("synced_files", [])
        for f in live_files:
            print(f"  [✓] {f.get('filename'):<30} (Drive ID: {f.get('file_id')}, Action: {f.get('action')})")

    print("\n============================================================")
    if status == "success":
        print(" SAGE STATUS: SUCCESS - PROJECTION SYNCHRONIZED")
        sys.exit(0)
    elif status == "validation_required" or "validation_required" in reason.lower():
        print(" SAGE STATUS: VALIDATION_REQUIRED - LIVE BOUNDARY PENDING AUTHORIZATION")
        sys.exit(0)
    else:
        print(" SAGE STATUS: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
