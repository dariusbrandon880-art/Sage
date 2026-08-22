"""Verify the Google Drive projection boundary without mutating canonical state."""
from __future__ import annotations

import argparse

from sage.integration import GoogleDriveProjectionSyncManager


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", default=".sage/credentials.json")
    parser.add_argument("--dir", default="SAGE")
    args = parser.parse_args()
    result = GoogleDriveProjectionSyncManager().sync_projection_to_drive(
        credentials_path=args.credentials,
        target_dir=args.dir,
    )
    handshake = result.get("stale_conflict_check", {})
    print({
        "mode": result.get("mode"),
        "status": result.get("status"),
        "handshake": handshake,
        "synced_files": len(result.get("synced_files", [])),
    })
    return 0 if result.get("status") in {"success", "validation_required"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
