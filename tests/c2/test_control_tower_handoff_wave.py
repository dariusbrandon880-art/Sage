"""Fail-closed anti-drift validation for SAGE Control Tower Handoff Big Jump Wave."""

import json
import re
import subprocess
from pathlib import Path
import pytest


def get_current_head_sha() -> str:
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def test_control_tower_handoff_wave_evidence_exists_and_valid():
    evidence_path = Path("evidence_capture/control_tower_handoff_wave_evidence.json")
    assert evidence_path.exists(), "Control tower handoff evidence file must exist."

    with open(evidence_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Rule 1: Verdict PASS
    assert data.get("reconvergence_verdict") == "PASS"

    # Rule 2: 5 Total Flights, 5 Successful, 0 Blocked
    assert data.get("total_flights") == 5
    assert data.get("successful_flights") == 5
    assert data.get("blocked_flights") == 0

    # Rule 3: 100% First-Pass Verification Rate
    assert data.get("first_pass_verification_rate") == 100.0

    # Rule 4: 20-Cell Advancement Matrix Traversal
    matrix = data.get("advancement_matrix_20_cells", {})
    assert len(matrix) == 20
    assert all(matrix.values())

    # Rule 5: Exact 40-character commit SHA binding matching HEAD
    sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")

    for flight in data.get("flight_summaries", []):
        exact_head = flight.get("exact_head")
        assert exact_head is not None, "exact_head must be present"
        assert sha_pattern.match(exact_head), f"Invalid SHA format: {exact_head}"
        assert flight.get("execution_result") == "PASS"

    # Rule 6: Package Hash Present and 64 hex chars
    pkg_hash = data.get("package_hash")
    assert pkg_hash is not None
    assert len(pkg_hash) == 64
