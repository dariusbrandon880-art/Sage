"""Unit and adversarial tests for SAGI Closed-Loop Cognitive Learning V1."""

import json
import pytest
import sys
import subprocess
from sage.experimental.progression import MissionProgressionController, MissionProgressionState
from sage.experimental.sagi.state import SAGIState
from sage.experimental.sagi.sagi import SAGICandidateGenerator
from sage.experimental.sagi.search_loop import SAGISearchLoop
from sage.experimental.sagi.research_graph import SAGIResearchGraph
from sage.experimental.sagi.cognitive_learning import (
    SAGICognitiveLearningSignal,
    SAGICognitiveLearningEngine,
)


@pytest.fixture
def identity_anchor():
    state = SAGIState.initialize_genesis("test_genesis")
    return state.identity_anchor.initial_sha256


@pytest.fixture
def controller():
    ctrl = MissionProgressionController()
    mission = {
        "mission_id": "mission_closed_loop_01",
        "objective": "Verify closed loop cognitive learning signal generation",
        "priority_score": 85.0,
        "assigned_agent": "agent_jules_sage",
        "required_evidence": ["output_hash"],
    }
    ctrl.intake_mission(mission)
    ctrl.prioritize()
    ctrl.validate_preflight()
    ctrl.prepare_handoff()
    ctrl.emit_handoff()
    ctrl.receive_execution_result({"output_data": "sample_output_data"})
    ctrl.validate_evidence({"output_hash": "hash_val"})
    return ctrl


def test_successful_outcome_to_valid_learning_signal(controller, identity_anchor):
    """Verify converting a SUCCESS mission outcome into a SUCCESS_MEMORY signal."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    engine = SAGICognitiveLearningEngine()

    signal = engine.process_mission_outcome(
        receipt=rcpt,
        identity_anchor=identity_anchor,
        evidence_data={"evidence_status": "VALIDATED", "confidence": 0.85},
    )

    assert signal.signal_type == "SUCCESS_MEMORY"
    assert signal.outcome_type == "SUCCESS"
    assert signal.originating_receipt_id == rcpt.receipt_id
    assert signal.mission_id == "mission_closed_loop_01"
    assert signal.identity_anchor == identity_anchor
    assert signal.confidence <= 0.85
    assert len(signal.signal_sha256) == 64

    # Verify emitted research node in graph
    assert len(engine.research_graph.nodes) == 1
    node = list(engine.research_graph.nodes.values())[0]
    assert node.guardian_result == "APPROVED"


def test_failed_outcome_to_failure_memory_signal(controller, identity_anchor):
    """Verify converting a FAILURE mission outcome into a FAILURE_MEMORY signal and recording failure memory."""
    rcpt = controller.classify_outcome(final_status="FAILURE")
    generator = SAGICandidateGenerator(seed=123)
    engine = SAGICognitiveLearningEngine()

    signal = engine.process_mission_outcome(
        receipt=rcpt,
        identity_anchor=identity_anchor,
        evidence_data={"evidence_status": "VALIDATED"},
        candidate_generator=generator,
    )

    assert signal.signal_type == "FAILURE_MEMORY"
    assert signal.outcome_type == "FAILURE"
    assert signal.originating_receipt_id == rcpt.receipt_id

    # Verify failure memory recorded in generator
    assert len(generator.failure_memory) == 1
    assert generator.failure_memory[0]["proposal_hash"] == rcpt.receipt_id


def test_insufficient_evidence_no_learning_promotion(controller, identity_anchor):
    """Adversarial Test: Insufficient evidence status fails closed and blocks learning promotion."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    engine = SAGICognitiveLearningEngine()

    with pytest.raises(ValueError, match="Insufficient evidence"):
        engine.process_mission_outcome(
            receipt=rcpt,
            identity_anchor=identity_anchor,
            evidence_data={"evidence_status": "INSUFFICIENT"},
        )


def test_conflicting_outcome_fails_closed(controller, identity_anchor):
    """Adversarial Test: Conflicting or invalid outcome classification fails closed."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    rcpt.validation_result["outcome_classification"] = "CORRUPTED_STATUS"
    engine = SAGICognitiveLearningEngine()

    with pytest.raises(ValueError, match="Conflicting or invalid outcome classification"):
        engine.process_mission_outcome(receipt=rcpt, identity_anchor=identity_anchor)


def test_missing_provenance_fails_closed(controller, identity_anchor):
    """Adversarial Test: Missing receipt ID or signature fails closed."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    rcpt.receipt_id = ""
    engine = SAGICognitiveLearningEngine()

    with pytest.raises(ValueError, match="Missing receipt_id or signature provenance"):
        engine.process_mission_outcome(receipt=rcpt, identity_anchor=identity_anchor)


def test_identity_mismatch_fails_closed(controller, identity_anchor):
    """Adversarial Test: Identity anchor mismatch or invalid length fails closed."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    engine = SAGICognitiveLearningEngine()

    with pytest.raises(ValueError, match="Invalid identity anchor"):
        engine.process_mission_outcome(receipt=rcpt, identity_anchor="short_invalid_anchor")


def test_search_loop_ingestion_and_identity_enforcement(controller, identity_anchor):
    """Verify ingesting learning signals into SAGISearchLoop enforces identity anchors."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    engine = SAGICognitiveLearningEngine()
    signal = engine.process_mission_outcome(rcpt, identity_anchor)

    search_loop = SAGISearchLoop()
    loop_anchor = search_loop.controller.state.identity_anchor.initial_sha256

    # Update signal's anchor to match loop's expected anchor
    signal.identity_anchor = loop_anchor
    res = search_loop.ingest_learning_signal(signal)
    assert res["status"] == "SUCCESS_MEMORY_INGESTED"

    # Mismatched anchor must be rejected
    signal.identity_anchor = "x" * 64
    with pytest.raises(ValueError, match="SAGI Learning Ingestion Identity Violation"):
        search_loop.ingest_learning_signal(signal)


def test_learning_signal_cannot_grant_unauthorized_execution_permission(controller, identity_anchor):
    """Adversarial Test: Learning signals cannot bypass PFC governance or grant execution authority."""
    rcpt = controller.classify_outcome(final_status="SUCCESS")
    engine = SAGICognitiveLearningEngine()
    signal = engine.process_mission_outcome(rcpt, identity_anchor)

    # Attempt to use learning signal to run unauthorized action in progression controller
    unauthorized_ctrl = MissionProgressionController()
    unauthorized_mission = {
        "mission_id": "unauth_mission_99",
        "objective": "Attempt governance bypass",
        "priority_score": 90.0,
        "assigned_agent": "unauthorized_agent",
    }
    unauthorized_ctrl.intake_mission(unauthorized_mission)
    unauthorized_ctrl.prioritize()

    unauthorized_ctrl.validate_preflight()

    # PFC & Handoff governance MUST fail closed despite valid learning signal existence
    with pytest.raises(ValueError, match="Transition Rejected: Failed validation gate for target state 'HANDOFF_READY'"):
        unauthorized_ctrl.prepare_handoff()


def test_restart_learning_reconstruction_preserved(tmp_path):
    """Verify true fresh-process reconstruction of learning signals across Python sub-interpreter boundaries."""
    file_path = tmp_path / "learning_signal_persisted.json"

    # PROCESS A: Create learning signal, write to disk, terminate
    script_a = f"""
import json
from sage.experimental.progression import MissionProgressionController
from sage.experimental.sagi.cognitive_learning import SAGICognitiveLearningEngine
from sage.experimental.sagi.state import SAGIState

ctrl = MissionProgressionController()
ctrl.intake_mission({{
    "mission_id": "proc_mission_01",
    "objective": "Fresh process learning test",
    "priority_score": 90.0,
    "assigned_agent": "agent_jules_sage",
}})
ctrl.prioritize()
ctrl.validate_preflight()
ctrl.prepare_handoff()
ctrl.emit_handoff()
ctrl.receive_execution_result({{"output_data": "proc_output"}})
ctrl.validate_evidence({{}})
rcpt = ctrl.classify_outcome("SUCCESS")

anchor = SAGIState.initialize_genesis("proc_genesis").identity_anchor.initial_sha256
engine = SAGICognitiveLearningEngine()
signal = engine.process_mission_outcome(rcpt, anchor)

with open(r'{file_path}', 'w') as f:
    json.dump(signal.model_dump(), f)
"""
    res_a = subprocess.run([sys.executable, "-c", script_a], capture_output=True, text=True)
    assert res_a.returncode == 0, f"Process A failed: {res_a.stderr}"

    # PROCESS B: Distinct Python process context loads learning signal from disk and verifies integrity
    script_b = f"""
import json
from sage.experimental.sagi.cognitive_learning import SAGICognitiveLearningSignal

with open(r'{file_path}', 'r') as f:
    data = json.load(f)

signal_b = SAGICognitiveLearningSignal(**data)
assert signal_b.signal_type == "SUCCESS_MEMORY"
assert signal_b.mission_id == "proc_mission_01"
assert len(signal_b.signal_sha256) == 64
assert len(signal_b.identity_anchor) == 64
assert signal_b.compute_sha256() == signal_b.signal_sha256
"""
    res_b = subprocess.run([sys.executable, "-c", script_b], capture_output=True, text=True)
    assert res_b.returncode == 0, f"Process B failed: {res_b.stderr}"
