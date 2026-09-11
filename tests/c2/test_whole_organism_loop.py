"""Tests for Whole-Organism Behavioral Loop & Comprehensive Receipt Engine."""

import json
import re
import subprocess
from pathlib import Path

import pytest

from sage.c2.whole_organism_loop import WholeOrganismFlightReceipt, WholeOrganismLoopEngine


@pytest.fixture
def valid_head_sha():
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def _valid_flight_payloads():
    return [
        {
            "flight_id": f"F{i}",
            "target": f"Target Subsystem {i}",
            "classification": "ACTIVE",
            "target_files": [f"sage/target_{i}.py"],
            "target_namespaces": [f"sage.target_{i}"],
            "pr_or_change": f"PR #{300 + i}",
            "executor": lambda i=i: {"execution_result": "PASS", "tests_passed": 10 + i},
        }
        for i in range(1, 6)
    ]


def test_whole_organism_loop_execution_and_receipt_verification(valid_head_sha):
    engine = WholeOrganismLoopEngine()
    receipt = engine.execute_whole_organism_loop(
        mission_id="test_whole_organism_001",
        session_id="jules_test_session",
        flight_payloads=_valid_flight_payloads(),
        exact_git_head=valid_head_sha,
    )

    assert receipt.mission_id == "test_whole_organism_001"
    assert receipt.exact_git_head == valid_head_sha
    assert len(receipt.flight_receipts) == 5
    assert len(receipt.evidence_hashes) == 5
    assert receipt.jigsaw_gates_passed > 0
    assert receipt.outcome_quality_score == 1.0
    assert receipt.all_stages_completed is True
    assert receipt.verify() is True
    assert len(receipt.receipt_hash) == 64

    # Check evidence persistence
    evidence_file = Path("evidence_capture/whole_organism_flight_receipt.json")
    assert evidence_file.exists()
    data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert data["mission_id"] == "test_whole_organism_001"
    assert data["receipt_hash"] == receipt.receipt_hash


def test_invalid_flight_count_rejection(valid_head_sha):
    engine = WholeOrganismLoopEngine()
    invalid_payloads = _valid_flight_payloads()[:3]
    with pytest.raises(ValueError, match="Whole-organism loop requires exactly 5 flight payloads"):
        engine.execute_whole_organism_loop(
            mission_id="invalid_count_mission",
            session_id="jules_session",
            flight_payloads=invalid_payloads,
            exact_git_head=valid_head_sha,
        )


def test_unexecuted_flight_fails_closed_in_whole_organism_loop(valid_head_sha):
    engine = WholeOrganismLoopEngine()
    payloads = _valid_flight_payloads()
    # Remove executor from flight F1
    del payloads[0]["executor"]

    with pytest.raises(RuntimeError, match="Reconvergence failed with verdict: FAIL_CLOSED"):
        engine.execute_whole_organism_loop(
            mission_id="unexecuted_mission",
            session_id="jules_session",
            flight_payloads=payloads,
            exact_git_head=valid_head_sha,
        )


def test_invalid_sha_rejection():
    engine = WholeOrganismLoopEngine()
    with pytest.raises(ValueError, match="Invalid git HEAD commit SHA"):
        engine.execute_whole_organism_loop(
            mission_id="bad_sha_mission",
            session_id="jules_session",
            flight_payloads=_valid_flight_payloads(),
            exact_git_head="badsha123",
        )
