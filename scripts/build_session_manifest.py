#!/usr/bin/env python3
"""Materialize the current SAGE session manifest from live repository state."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / ".sage" / "session_manifest.json"
SHA_LEN = 40


def git_head() -> str:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if len(sha) != SHA_LEN or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise SystemExit("FAIL_CLOSED: unable to resolve a valid 40-character HEAD SHA")
    return sha


def active_branch() -> str:
    return subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip() or "detached"


def materialize(mission: str, interfaces: list[str], output: Path) -> dict:
    if not mission:
        raise SystemExit("FAIL_CLOSED: active mission is required")
    if not interfaces or len(set(interfaces)) != len(interfaces):
        raise SystemExit("FAIL_CLOSED: required interfaces must be non-empty and unique")

    sha = git_head()
    surfaces = {
        interface: {"verdict": "PENDING", "evidence_ref": None}
        for interface in interfaces
    }
    payload = {
        "schema_version": "1.0.0",
        "canonical_git_sha": sha,
        "active_mission": mission,
        "active_ref": active_branch(),
        "required_interfaces": interfaces,
        "surfaces": surfaces,
        "global_acceptance_state": "PENDING",
        "identity_contract": {
            "nameplate": "sage/experimental/airspace/nameplate.py",
            "hud": "sage/agent_hud_projection.py",
            "immersion_doctrine": "docs/SAGE-INVENTOR-AGENT-IMMERSION-DOCTRINE.md",
            "source_of_truth": "canonical_airspace_state",
        },
        "binding": {"sha_required": True, "drift_policy": "FAIL_CLOSED"},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="session_manifest.", suffix=".json", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, output)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", required=True)
    parser.add_argument("--required-interface", action="append", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    payload = materialize(args.mission, args.required_interface, args.output)
    print(json.dumps({"status": "PASS", "canonical_git_sha": payload["canonical_git_sha"], "manifest": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
