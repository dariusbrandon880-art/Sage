"""Tests for Hardened 20-Cell 5x4 Big Jump Wave evidence and anti-drift validator."""

import json
from pathlib import Path
import pytest

from scripts.execute_big_jump_wave_20_cells import (
    main as run_20_cell_wave,
    validate_20_cell_wave_payload,
    get_commit_sha,
    EVIDENCE_PATH,
)


def test_execute_big_jump_wave_20_cells_evidence_success():
    ret = run_20_cell_wave()
    assert ret == 0
    assert EVIDENCE_PATH.exists()

    with open(EVIDENCE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_flights"] == 5
    assert data["total_lifecycle_gates"] == 4
    assert data["total_advancement_cells"] == 20
    assert data["reconvergence_verdict"] == "PASS"
    assert len(data["cells"]) == 20

    current_sha = get_commit_sha()
    errors = validate_20_cell_wave_payload(data, current_sha)
    assert errors == [], f"Validation errors found: {errors}"


def test_validator_rejects_non_20_cells():
    sha = get_commit_sha()
    data = {"cells": [{"flight_id": "F1", "lifecycle_gate": "G1"}]}
    errors = validate_20_cell_wave_payload(data, sha)
    assert any("Rule 1 Violation" in e for e in errors)


def test_validator_rejects_missing_gates():
    sha = get_commit_sha()
    # Build 20 cells but leave F5 missing G4 and duplicate F1 G1
    valid_cells = []
    flights = ["F1", "F2", "F3", "F4", "F5"]
    gates = ["G1", "G2", "G3", "G4"]

    for f in flights:
        for g in gates:
            valid_cells.append({
                "flight_id": f,
                "lifecycle_gate": g,
                "exact_head_sha": sha,
                "source_target": "sage/c2/adaptive_mission_selection.py",
                "verification_command": "test()",
                "verification_result": "PASS",
                "provenance_ref": f"ref-{f}-{g}",
                "cell_digest": f"digest-{f}-{g}",
            })

    # Tamper cell 19 to duplicate cell 0
    valid_cells[19] = dict(valid_cells[0])
    valid_cells[19]["cell_digest"] = "digest-dup"

    errors = validate_20_cell_wave_payload({"cells": valid_cells}, sha)
    assert any("Rule 2 Violation" in e or "Rule 3 Violation" in e for e in errors)


def test_validator_rejects_invalid_sha_and_stale_sha():
    sha = get_commit_sha()
    cells = [{
        "flight_id": f"F{i//4 + 1}",
        "lifecycle_gate": f"G{i%4 + 1}",
        "exact_head_sha": "invalid_short_sha",
        "source_target": "sage/c2/adaptive_mission_selection.py",
        "verification_command": "test()",
        "verification_result": "PASS",
        "provenance_ref": "ref-1",
        "cell_digest": f"digest-{i}",
    } for i in range(20)]

    errors = validate_20_cell_wave_payload({"cells": cells}, sha)
    assert any("Rule 4 Violation" in e for e in errors)


def test_validator_rejects_missing_source_path():
    sha = get_commit_sha()
    cells = [{
        "flight_id": f"F{i//4 + 1}",
        "lifecycle_gate": f"G{i%4 + 1}",
        "exact_head_sha": sha,
        "source_target": "non_existent_file_xyz.py",
        "verification_command": "test()",
        "verification_result": "PASS",
        "provenance_ref": "ref-1",
        "cell_digest": f"digest-{i}",
    } for i in range(20)]

    errors = validate_20_cell_wave_payload({"cells": cells}, sha)
    assert any("Rule 6 Violation" in e for e in errors)
