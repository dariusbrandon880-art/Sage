#!/usr/bin/env python3
"""Fail-closed verifier for the SAGE operator acceptance bootstrap contract."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

SHA_LEN = 40
STATE_DOC = Path("docs/governance/OPERATOR_ACCEPTANCE_STATE.md")
REQUIRED_MARKERS = (
    "main_goals",
    "side_goals",
    "active_flights",
    "deterministic_gate",
    "empirical_gate",
    "acceptance_status",
)

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.STDOUT).strip()

def main() -> int:
    try:
        head = git("rev-parse", "HEAD")
        branch = git("branch", "--show-current")
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":f"git state unavailable: {exc}"}))
        return 1
    if len(head) != SHA_LEN:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":"canonical HEAD is not a 40-character SHA"}))
        return 1
    if not STATE_DOC.exists():
        print(json.dumps({"status":"FAIL_CLOSED", "reason":"operator acceptance state contract missing"}))
        return 1
    text = STATE_DOC.read_text(encoding="utf-8")
    missing = [m for m in REQUIRED_MARKERS if m not in text]
    if missing:
        print(json.dumps({"status":"FAIL_CLOSED", "reason":"state contract incomplete", "missing":missing}))
        return 1
    print(json.dumps({"status":"PASS", "canonical_git_sha":head, "branch":branch, "contract":"OPERATOR_ACCEPTANCE_STATE"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
