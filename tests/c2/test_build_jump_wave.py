"""Unit and integration tests for SAGE C2 Build Jump Wave Dispatch Engine."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from sage.c2.build_jump_wave import (
    BUILD_JUMP_FLIGHT_MISSIONS,
    BuildJumpFlightMission,
    BuildJumpWaveEngine,
)


def test_build_jump_wave_dispatch_all_flights_pass() -> None:
    engine = BuildJumpWaveEngine(commit_sha="test_commit_sha_12345")
    receipt = engine.dispatch_wave()

    assert receipt.commit_sha == "test_commit_sha_12345"
    assert len(receipt.flight_receipts) == 5
    assert receipt.collision_count == 0
    assert receipt.collisions_detected == []
    assert receipt.wave_verdict == "PASS"

    flight_ids = [f.flight_id for f in receipt.flight_receipts]
    assert flight_ids == ["Flight 1", "Flight 2", "Flight 3", "Flight 4", "Flight 5"]

    receipt_types = [f.receipt_type for f in receipt.flight_receipts]
    expected_types = [
        "Continuity Validation Receipt",
        "Governed Execution Evidence Receipt",
        "Scientific Robustness Receipt",
        "Evidence Lifecycle Receipt",
        "Cognitive Integration Receipt",
    ]
    assert receipt_types == expected_types

    for flight in receipt.flight_receipts:
        assert flight.status == "PASS"
        assert flight.commit_sha == "test_commit_sha_12345"
        assert len(flight.receipt_hash) == 64


def test_build_jump_wave_isolation_and_no_collisions() -> None:
    engine = BuildJumpWaveEngine(commit_sha="test_sha_abc")
    receipt = engine.dispatch_wave()

    scopes = set()
    missions = set()
    for f in receipt.flight_receipts:
        assert f.boundary_scope not in scopes
        scopes.add(f.boundary_scope)

        assert f.mission_id not in missions
        missions.add(f.mission_id)

    assert len(scopes) == 5
    assert len(missions) == 5


def test_build_jump_wave_runner_script_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.execute_build_jump_wave import main

    monkeypatch.setattr("scripts.execute_build_jump_wave.REPO_ROOT", tmp_path)

    main()

    evidence_file = tmp_path / "evidence_capture" / "build_jump_wave_evidence.json"
    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["wave_verdict"] == "PASS"
    assert len(data["flight_receipts"]) == 5
    assert data["collision_count"] == 0
