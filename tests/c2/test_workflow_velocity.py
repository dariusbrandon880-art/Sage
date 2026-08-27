"""Unit and integration tests for SAGE Multi-Session Velocity Engine & Rolls-Royce Workflow Protocol."""

import json
import re
import subprocess
import pytest
from pathlib import Path

from sage.c2.workflow_velocity import (
    MultiSessionVelocityEngine,
    MultiSessionVelocityReceipt,
    SessionContext,
    SessionRole,
)


@pytest.fixture
def velocity_engine():
    return MultiSessionVelocityEngine()


@pytest.fixture
def valid_git_head():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


def test_session_registration_and_lookup(velocity_engine):
    c2_ctx = velocity_engine.register_session("c2-tower-1", SessionRole.C2_CONTROL_TOWER)
    jules_ctx = velocity_engine.register_session("jules-exec-1", SessionRole.JULES_EXECUTION_SESSION)
    assert c2_ctx.role == SessionRole.C2_CONTROL_TOWER
    assert jules_ctx.role == SessionRole.JULES_EXECUTION_SESSION
    retrieved = velocity_engine.get_session("c2-tower-1")
    assert retrieved is not None
    assert retrieved.session_id == "c2-tower-1"
    assert len(velocity_engine.list_active_sessions()) == 2


def test_anti_collision_lock_acquisition_and_release(velocity_engine):
    lock_1 = velocity_engine.acquire_flight_lock(
        session_id="session-alpha", flight_id="F1",
        target_files=["sage/c2/workflow_velocity.py"], target_namespaces=["sage.c2.velocity"],
    )
    assert lock_1.acquired is True
    lock_2 = velocity_engine.acquire_flight_lock(
        session_id="session-beta", flight_id="F2",
        target_files=["sage/c2/workflow_velocity.py"], target_namespaces=["sage.c2.velocity"],
    )
    assert lock_2.acquired is False
    assert lock_2.conflicting_session_id == "session-alpha"
    assert lock_2.conflicting_flight_id == "F1"
    assert velocity_engine.release_flight_lock("session-alpha", "F1") is True
    lock_3 = velocity_engine.acquire_flight_lock(
        session_id="session-beta", flight_id="F2",
        target_files=["sage/c2/workflow_velocity.py"], target_namespaces=["sage.c2.velocity"],
    )
    assert lock_3.acquired is True


def test_multi_session_velocity_wave_execution(velocity_engine, valid_git_head):
    flight_payloads = [
        {
            "flight_id": f"F{i}", "target": f"Frontier Path {i}",
            "classification": "ACTIVE", "execution_result": "PASS",
            "tests_passed": 10 + i, "target_files": [f"sage/module_{i}.py"],
            "target_namespaces": [f"sage.ns_{i}"],
        }
        for i in range(1, 6)
    ]
    receipt = velocity_engine.execute_velocity_wave(
        wave_id="test_wave_100", session_id="jules-session-1",
        flight_payloads=flight_payloads, exact_git_head=valid_git_head,
    )
    assert receipt.wave_id == "test_wave_100"
    assert receipt.exact_git_head == valid_git_head
    assert re.fullmatch(r"[0-9a-fA-F]{40}", receipt.exact_git_head)
    assert receipt.total_flights == 5
    assert receipt.successful_flights == 5
    assert len(receipt.advancement_matrix_20_cells) == 20
    assert all(receipt.advancement_matrix_20_cells.values())
    assert receipt.rolls_royce_quality_passed is True
    assert receipt.reconvergence_verdict == "PASS"
    assert len(receipt.receipt_hash) == 64


def test_invalid_sha_rejection(velocity_engine):
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        velocity_engine.execute_velocity_wave(
            wave_id="invalid_sha_wave", session_id="jules-session-1",
            flight_payloads=[{"flight_id": "F1", "target_files": [], "target_namespaces": []}],
            exact_git_head="shortsha123",
        )


def test_lock_collision_fails_closed(velocity_engine, valid_git_head):
    velocity_engine.acquire_flight_lock(
        session_id="external_blocking_session", flight_id="F_BLOCK",
        target_files=["sage/c2/workflow_velocity.py"], target_namespaces=["sage.c2.velocity"],
    )
    flight_payloads = [
        {"flight_id": "F1", "target": "Conflicting Core Path",
         "target_files": ["sage/c2/workflow_velocity.py"], "target_namespaces": ["sage.c2.velocity"]},
        *[
            {"flight_id": f"F{i}", "target_files": [f"file{i}.py"], "target_namespaces": [f"ns{i}"]}
            for i in range(2, 6)
        ],
    ]
    receipt = velocity_engine.execute_velocity_wave(
        wave_id="collision_wave_001", session_id="jules-blocked-session",
        flight_payloads=flight_payloads, exact_git_head=valid_git_head,
    )
    assert receipt.successful_flights < 5
    assert receipt.rolls_royce_quality_passed is False
    assert receipt.reconvergence_verdict == "FAIL_CLOSED"


def test_persisted_evidence_file_is_historical_not_live_gate():
    evidence_path = Path("evidence_capture/multi_session_velocity_wave_evidence.json")
    assert evidence_path.exists(), "Historical velocity evidence fixture must exist"
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert re.fullmatch(r"[0-9a-fA-F]{40}", data["exact_git_head"])
    assert re.fullmatch(r"[0-9a-fA-F]{40}", current_head)
    assert data["exact_git_head"] == current_head
    assert data["wave_id"] == "multi_session_velocity_wave_001"
    assert data["total_flights"] == 5
    assert data["successful_flights"] == 5
    assert len(data["advancement_matrix_20_cells"]) == 20
    assert data.get("gate_authority") != "live"
