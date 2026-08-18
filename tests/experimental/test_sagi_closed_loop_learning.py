"""Unit tests for SAGI Closed-Loop Progression Learning Signal Bridge."""

import pytest
from pathlib import Path
from sage.experimental.progression import MissionProgressionController, MissionProgressionReceipt
from sage.experimental.sagi.cognitive_learning import (
    SAGICognitiveLearningEngine,
    SAGICognitiveLearningSignal,
)


def test_verified_receipt_generates_learning_signal(tmp_path):
    controller = MissionProgressionController()
    mission_data = {
        "mission_id": "m_learn_001",
        "objective": "Test closed-loop learning signal",
        "priority_score": 88.0,
        "assigned_agent": "agent_jules_sage",
    }
    controller.intake_mission(mission_data)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "valid_output"})
    controller.validate_evidence({"req_1": "present"})
    classified_rcpt = controller.classify_outcome("SUCCESS")

    test_file = tmp_path / "test_learning_signals.json"
    engine = SAGICognitiveLearningEngine(persistence_path=test_file)
    signal = engine.ingest_progression_receipt(classified_rcpt)

    assert signal.mission_id == "m_learn_001"
    assert signal.receipt_id == classified_rcpt.receipt_id
    assert signal.outcome_classification == "SUCCESS"
    assert len(signal.signal_hash) == 64
    assert test_file.exists()


def test_failure_classified_receipt_updates_generator_memory(tmp_path):
    controller = MissionProgressionController()
    mission_data = {
        "mission_id": "m_learn_fail_002",
        "objective": "Test failure learning signal",
        "priority_score": 88.0,
        "assigned_agent": "agent_jules_sage",
    }
    controller.intake_mission(mission_data)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "valid_output"})
    controller.validate_evidence({"req_1": "present"})
    classified_rcpt = controller.classify_outcome("FAILURE")

    test_file = tmp_path / "test_learning_signals_fail.json"
    engine = SAGICognitiveLearningEngine(persistence_path=test_file)
    signal = engine.ingest_progression_receipt(classified_rcpt)

    assert signal.outcome_classification == "FAILURE"
    assert len(engine.generator.failure_memory) == 1
    assert engine.generator.failure_memory[0]["mission_id"] == "m_learn_fail_002"


def test_unclassified_receipt_fails_closed(tmp_path):
    controller = MissionProgressionController()
    mission_data = {
        "mission_id": "m_learn_unclass_003",
        "objective": "Test unclassified receipt fail closed",
        "priority_score": 88.0,
        "assigned_agent": "agent_jules_sage",
    }
    intake_rcpt = controller.intake_mission(mission_data)

    engine = SAGICognitiveLearningEngine(persistence_path=tmp_path / "signals.json")
    with pytest.raises(ValueError, match="FAIL_CLOSED_NOT_CLASSIFIED"):
        engine.ingest_progression_receipt(intake_rcpt)


def test_unverified_receipt_fails_closed(tmp_path):
    unverified_rcpt = MissionProgressionReceipt(
        receipt_id="rcpt_bad_001",
        next_state="OUTCOME_CLASSIFIED",
        mission_id="m_bad_001",
        reason="Unverified receipt",
        validation_result={"status": "REJECTED"},
        provenance_reference="prov_bad",
        sequence_order=1,
        timestamp="2026-08-18T00:00:00Z",
        signature="sig_bad",
    )

    engine = SAGICognitiveLearningEngine(persistence_path=tmp_path / "signals.json")
    with pytest.raises(ValueError, match="FAIL_CLOSED_UNVERIFIED_RECEIPT"):
        engine.ingest_progression_receipt(unverified_rcpt)


def test_learning_signal_rehydration_across_restarts(tmp_path):
    test_file = tmp_path / "test_rehydration_signals.json"
    engine1 = SAGICognitiveLearningEngine(persistence_path=test_file)

    controller = MissionProgressionController()
    mission_data = {
        "mission_id": "m_rehydrate_004",
        "objective": "Test rehydration",
        "priority_score": 90.0,
        "assigned_agent": "agent_jules_sage",
    }
    controller.intake_mission(mission_data)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "valid_output"})
    controller.validate_evidence({"req_1": "present"})
    classified_rcpt = controller.classify_outcome("SUCCESS")

    engine1.ingest_progression_receipt(classified_rcpt)

    # Fresh process restart simulation
    engine2 = SAGICognitiveLearningEngine(persistence_path=test_file)
    loaded = engine2.load_signals()

    assert len(loaded) == 1
    assert loaded[0].mission_id == "m_rehydrate_004"
    assert loaded[0].signal_hash == engine1.learning_signals[0].signal_hash
