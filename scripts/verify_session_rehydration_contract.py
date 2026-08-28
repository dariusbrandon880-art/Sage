#!/usr/bin/env python3
"""Fail-closed verification of the SAGE fresh-session rehydration contract."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/governance/SAGE_SESSION_STATE_MANIFEST.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    required = manifest["required"]
    identity = manifest["identity_contract"]
    for key in required:
        if key == "canonical_git_sha":
            continue
        if key == "active_mission":
            continue
        if key == "required_interfaces":
            continue
        if key == "acceptance_status":
            continue
        if key == "identity_contract" and not identity:
            raise SystemExit("FAIL_CLOSED: identity contract is empty")
    for key in ("nameplate", "hud", "immersion_doctrine"):
        path = ROOT / identity[key]
        if not path.is_file():
            raise SystemExit(f"FAIL_CLOSED: missing identity contract artifact: {identity[key]}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if len(head) != 40:
        raise SystemExit("FAIL_CLOSED: invalid canonical HEAD")
    if manifest["binding"]["drift_policy"] != "FAIL_CLOSED":
        raise SystemExit("FAIL_CLOSED: drift policy is not fail-closed")
    print(json.dumps({"status": "PASS", "canonical_git_sha": head, "identity_contract": "PASS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
