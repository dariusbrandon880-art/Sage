#!/usr/bin/env python3
"""Fail-closed verification of the materialized SAGE fresh-session contract."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/governance/SAGE_SESSION_STATE_MANIFEST.json"
MANIFEST = ROOT / ".sage" / "session_manifest.json"
SHA_LEN = 40


def head() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if len(value) != SHA_LEN or any(c not in "0123456789abcdef" for c in value.lower()):
        raise SystemExit("FAIL_CLOSED: invalid canonical HEAD")
    return value


def main() -> int:
    if not MANIFEST.is_file():
        raise SystemExit("FAIL_CLOSED: dynamic session manifest has not been materialized")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL_CLOSED: invalid session manifest: {exc}") from exc

    current_sha = head()
    if manifest.get("canonical_git_sha") != current_sha:
        raise SystemExit("FAIL_CLOSED: materialized manifest SHA does not match HEAD")
    if manifest.get("active_mission") in (None, ""):
        raise SystemExit("FAIL_CLOSED: active mission is empty")
    interfaces = manifest.get("required_interfaces")
    if not isinstance(interfaces, list) or not interfaces or len(set(interfaces)) != len(interfaces):
        raise SystemExit("FAIL_CLOSED: required interfaces are missing or duplicated")
    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(interfaces):
        raise SystemExit("FAIL_CLOSED: surface ledger does not match required interfaces")
    for interface in interfaces:
        data = surfaces[interface]
        if data.get("verdict") not in {"PASS", "FAIL", "PENDING"}:
            raise SystemExit(f"FAIL_CLOSED: invalid verdict for surface {interface}")
        if data.get("verdict") == "PASS" and not data.get("evidence_ref"):
            raise SystemExit(f"FAIL_CLOSED: surface {interface} passed without evidence")
    identity = manifest.get("identity_contract")
    if not identity:
        raise SystemExit("FAIL_CLOSED: identity contract is empty")
    for key in ("nameplate", "hud", "immersion_doctrine"):
        path = ROOT / identity.get(key, "")
        if not path.is_file():
            raise SystemExit(f"FAIL_CLOSED: missing identity contract artifact: {identity.get(key)}")
    if manifest.get("binding", {}).get("drift_policy") != "FAIL_CLOSED":
        raise SystemExit("FAIL_CLOSED: drift policy is not fail-closed")
    if schema.get("binding", {}).get("sha_required") is not True:
        raise SystemExit("FAIL_CLOSED: canonical schema does not require SHA binding")
    print(json.dumps({"status": "PASS", "canonical_git_sha": current_sha, "manifest": str(MANIFEST)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
