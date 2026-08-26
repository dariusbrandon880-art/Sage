"""Fail-closed validation tests for the recovered 5x4 Big Jump Wave executor."""

from scripts.execute_big_jump_wave_20_cells import validate_20_cell_wave_payload


def _cell(flight, gate, sha, digest):
    return {
        "flight_id": flight,
        "lifecycle_gate": gate,
        "exact_head_sha": sha,
        "source_target": "sage/c2/adaptive_mission_selection.py",
        "verification_result": "PASS",
        "provenance_ref": f"ref-{flight}-{gate}",
        "cell_digest": digest,
    }


def test_rejects_wrong_cell_count():
    errors = validate_20_cell_wave_payload({}, "a" * 40)
    assert any("expected 20 cells" in error for error in errors)


def test_accepts_complete_unique_matrix():
    sha = "a" * 40
    cells = [_cell(f, g, sha, f"digest-{f}-{g}") for f in ("F1", "F2", "F3", "F4", "F5") for g in ("G1", "G2", "G3", "G4")]
    errors = validate_20_cell_wave_payload({"cells": cells}, sha)
    assert errors == []


def test_rejects_stale_sha_and_duplicate_digest():
    sha = "a" * 40
    cells = [_cell(f, g, sha, f"digest-{f}-{g}") for f in ("F1", "F2", "F3", "F4", "F5") for g in ("G1", "G2", "G3", "G4")]
    cells[0]["exact_head_sha"] = "b" * 40
    cells[1]["cell_digest"] = cells[0]["cell_digest"]
    errors = validate_20_cell_wave_payload({"cells": cells}, sha)
    assert any("stale HEAD SHA" in error for error in errors)
    assert any("duplicate cell digest" in error for error in errors)
