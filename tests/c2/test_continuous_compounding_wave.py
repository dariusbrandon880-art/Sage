"""Unit tests for Continuous Compounding Wave Runner & Evidence Suite."""

import json
from pathlib import Path

from scripts.execute_continuous_compounding_wave import (
    EXACT_HEAD_SHA,
    run_continuous_compounding_wave,
)


def test_continuous_compounding_wave_runner():
    res = run_continuous_compounding_wave()

    assert res["wave_id"] == "continuous_compounding_wave_001"
    assert res["exact_git_head"] == EXACT_HEAD_SHA
    assert res["total_flights"] == 5
    assert res["successful_flights"] == 5
    assert res["blocked_flights"] == 0
    assert res["first_pass_verification_rate"] == 100.0
    assert res["reconvergence_verdict"] == "PASS"
    assert len(res["advancement_matrix_20_cells"]) == 20
    assert all(res["advancement_matrix_20_cells"].values())
    assert len(res["package_hash"]) == 64

    # Verify persisted evidence file
    evidence_path = Path("evidence_capture/continuous_compounding_wave_evidence.json")
    assert evidence_path.exists()
    with open(evidence_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["package_hash"] == res["package_hash"]
