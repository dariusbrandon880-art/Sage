"""Tests for 20-Cell Big Jump Wave execution evidence."""

import json
from pathlib import Path
import pytest

from scripts.execute_big_jump_wave_20_cells import main as run_20_cell_wave, EVIDENCE_PATH


def test_execute_big_jump_wave_20_cells_evidence():
    ret = run_20_cell_wave()
    assert ret == 0
    assert EVIDENCE_PATH.exists()

    with open(EVIDENCE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_flights"] == 5
    assert data["total_lifecycle_stages"] == 4
    assert data["total_advancement_cells"] == 20
    assert data["reconvergence_verdict"] == "PASS"
    assert len(data["cells"]) == 20

    # Verify each cell is unique, verified, and signed with a 64-char SHA-256 digest
    digests = set()
    for cell in data["cells"]:
        assert cell["status"] == "VERIFIED"
        assert len(cell["cell_digest"]) == 64
        digests.add(cell["cell_digest"])

    assert len(digests) == 20
