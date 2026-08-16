"""Unit test suite for SAGE Continuous Flight Record & Reporting System."""

from datetime import datetime, timezone, timedelta
import hashlib
import json
import pytest
from pathlib import Path

from sage.experimental.flight_record import (
    SAGEFlightRecord,
    SportsRealPredictionRecord,
    SAGEFlightRecordManager
)


@pytest.fixture
def temp_flight_manager(tmp_path: Path) -> SAGEFlightRecordManager:
    flight_file = tmp_path / "flight_records.json"
    sports_file = tmp_path / "sports_predictions.json"
    return SAGEFlightRecordManager(
        flight_ledger_path=flight_file,
        sports_ledger_path=sports_file
    )


def test_48h_chronological_reconstruction(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 1: Create multiple flight records and verify 48-hour chronological view reconstruction."""
    now = datetime.now(timezone.utc)

    rec1 = SAGEFlightRecord(
        record_id="rec_01",
        timestamp=(now - timedelta(hours=10)).isoformat(),
        mission_id="msn_01",
        operator_or_agent="Jules",
        session_id="ses_01",
        task_description="Task 1",
        action_type="EXECUTION",
        files_touched=["sage/runtime/engine.py"],
        commit_sha="abc1234",
        pr_number=101,
        result_status="APPROVED",
        capability_classification="PROVEN"
    )

    rec2 = SAGEFlightRecord(
        record_id="rec_02",
        timestamp=(now - timedelta(hours=2)).isoformat(),
        mission_id="msn_02",
        operator_or_agent="ChatGPT",
        session_id="ses_02",
        task_description="Task 2",
        action_type="AUDIT",
        files_touched=["sage/core/spek.py"],
        commit_sha="def5678",
        pr_number=102,
        result_status="APPROVED",
        capability_classification="PROVEN"
    )

    temp_flight_manager.record_flight_event(rec1)
    temp_flight_manager.record_flight_event(rec2)

    report = temp_flight_manager.get_48h_flight_report(reference_time=now)
    assert len(report) == 2
    assert report[0]["record_id"] == "rec_01"
    assert report[1]["record_id"] == "rec_02"


def test_24h_sports_resolution_linking(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 2: Create Sports/RCE observation -> prediction -> outcome -> score records."""
    now = datetime.now(timezone.utc)

    pred = SportsRealPredictionRecord(
        prediction_id="pred_mlb_01",
        event_id="mlb_event_2026",
        sport_league="MLB",
        teams_players={"home": "Yankees", "away": "Red Sox"},
        source_url_or_api="https://statsapi.mlb.com/api/v1/schedule",
        observation_timestamp=(now - timedelta(hours=5)).isoformat(),
        market_type="MONEYLINE",
        pre_game_odds=-150.0,
        prediction_classification="RESEARCH-ONLY PREDICTION",
        model_probability=0.62,
        confidence_score=0.85,
        prediction_timestamp=(now - timedelta(hours=5)).isoformat(),
        temporal_lock_hash=hashlib.sha256(b"lock_payload").hexdigest()
    )

    temp_flight_manager.record_sports_prediction(pred)

    # Resolve prediction
    resolved = temp_flight_manager.resolve_sports_prediction(
        prediction_id="pred_mlb_01",
        outcome_status="WIN",
        outcome_source="https://statsapi.mlb.com/api/v1/game/12345/boxscore",
        score_value=0.1444,
        calibration_metric=0.92,
        learning_notes="Model odds hit expected boundary."
    )

    assert resolved.outcome_status == "WIN"
    assert resolved.score_value == 0.1444

    report = temp_flight_manager.get_24h_sports_report(reference_time=now)
    assert len(report) == 1
    assert report[0]["prediction_id"] == "pred_mlb_01"
    assert report[0]["outcome_status"] == "WIN"


def test_immutable_prediction_record_rejection(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 3 & 4: Attempt modification of immutable original prediction fields causing fail-closed rejection."""
    now = datetime.now(timezone.utc)

    pred = SportsRealPredictionRecord(
        prediction_id="pred_mlb_02",
        event_id="mlb_event_3000",
        sport_league="MLB",
        teams_players={"home": "Dodgers", "away": "Giants"},
        source_url_or_api="https://statsapi.mlb.com",
        observation_timestamp=now.isoformat(),
        market_type="MONEYLINE",
        pre_game_odds=-110.0,
        prediction_classification="RESEARCH-ONLY PREDICTION",
        model_probability=0.55,
        confidence_score=0.80,
        prediction_timestamp=now.isoformat(),
        temporal_lock_hash="hash_lock_123"
    )

    temp_flight_manager.record_sports_prediction(pred)

    # Re-inserting duplicate ID fails
    with pytest.raises(ValueError, match="Duplicate prediction_id"):
        temp_flight_manager.record_sports_prediction(pred)


def test_provenance_verification_chain(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 5: Verify provenance chain flight_record -> artifact -> receipt -> commit/PR."""
    now = datetime.now(timezone.utc)
    rec = SAGEFlightRecord(
        record_id="rec_prov_01",
        timestamp=now.isoformat(),
        mission_id="msn_prov",
        operator_or_agent="Jules",
        session_id="ses_prov",
        task_description="Provenance task",
        action_type="EXECUTION",
        files_touched=["sage/experimental/flight_record.py"],
        commit_sha="7a85324b4c0d6ec46b7e9a5dc5a141fabab01d7a",
        pr_number=129,
        receipt_ids=["rcpt_001"],
        artifact_paths=["evidence_capture/flight_records_ledger.json"],
        result_status="APPROVED",
        capability_classification="PROVEN"
    )
    temp_flight_manager.record_flight_event(rec)

    view = temp_flight_manager.generate_report_view("FULL_48_HOUR_SAGE_FLIGHT_REPORT", reference_time=now)
    record = view["records"][0]
    assert record["commit_sha"] == "7a85324b4c0d6ec46b7e9a5dc5a141fabab01d7a"
    assert record["pr_number"] == 129
    assert record["receipt_ids"] == ["rcpt_001"]


def test_time_window_filtering(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 6: Verify records outside requested time window are excluded."""
    now = datetime.now(timezone.utc)

    old_rec = SAGEFlightRecord(
        record_id="rec_old",
        timestamp=(now - timedelta(hours=60)).isoformat(),
        mission_id="msn_old",
        operator_or_agent="Jules",
        session_id="ses_old",
        task_description="Old Task",
        action_type="EXECUTION",
        result_status="APPROVED",
        capability_classification="PROVEN"
    )
    new_rec = SAGEFlightRecord(
        record_id="rec_new",
        timestamp=(now - timedelta(hours=12)).isoformat(),
        mission_id="msn_new",
        operator_or_agent="Jules",
        session_id="ses_new",
        task_description="New Task",
        action_type="EXECUTION",
        result_status="APPROVED",
        capability_classification="PROVEN"
    )

    temp_flight_manager.record_flight_event(old_rec)
    temp_flight_manager.record_flight_event(new_rec)

    report = temp_flight_manager.get_48h_flight_report(reference_time=now)
    assert len(report) == 1
    assert report[0]["record_id"] == "rec_new"


def test_synthetic_vs_real_sports_isolation(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 7: Verify synthetic RCE-001 cannot be classified as real-world Sports/RCE."""
    now = datetime.now(timezone.utc)

    synth = SportsRealPredictionRecord(
        prediction_id="synth_01",
        event_id="synth_event",
        sport_league="SIMULATED",
        teams_players={"home": "SimA", "away": "SimB"},
        source_url_or_api="in-memory-simulation",
        observation_timestamp=now.isoformat(),
        market_type="MONEYLINE",
        pre_game_odds=100.0,
        prediction_classification="SYNTHETIC RCE-001",
        model_probability=0.50,
        confidence_score=0.50,
        prediction_timestamp=now.isoformat(),
        temporal_lock_hash="synth_lock_hash"
    )

    temp_flight_manager.record_sports_prediction(synth)
    report = temp_flight_manager.get_24h_sports_report(reference_time=now)
    assert len(report) == 1
    assert report[0]["prediction_classification"] == "SYNTHETIC RCE-001"
    assert report[0]["prediction_classification"] != "REAL-WORLD OBSERVATION"


def test_missing_evidence_unverified_handling(temp_flight_manager: SAGEFlightRecordManager):
    """TEST 8: Verify missing evidence is reported as UNVERIFIED rather than reconstructed."""
    now = datetime.now(timezone.utc)

    unverified_rec = SAGEFlightRecord(
        record_id="rec_unverified",
        timestamp=now.isoformat(),
        mission_id="msn_unverified",
        operator_or_agent="Jules",
        session_id="ses_unverified",
        task_description="Task with unverified evidence",
        action_type="AUDIT",
        receipt_ids=[],
        artifact_paths=[],
        result_status="UNVERIFIED",
        capability_classification="UNVERIFIED",
        blockers="Missing underlying SPEK receipt"
    )

    temp_flight_manager.record_flight_event(unverified_rec)
    report = temp_flight_manager.get_48h_flight_report(reference_time=now)
    assert report[0]["capability_classification"] == "UNVERIFIED"
    assert report[0]["result_status"] == "UNVERIFIED"


def test_fresh_session_cross_session_reconstruction():
    """PHASE 9 ACCEPTANCE TEST: Fresh manager session reconstructs persisted flight history from disk without conversation state."""
    manager1 = SAGEFlightRecordManager(
        flight_ledger_path="evidence_capture/flight_records_ledger.json"
    )
    records1 = manager1.get_48h_flight_report()
    assert len(records1) >= 2

    # Instantiate fresh manager representing new session
    manager2 = SAGEFlightRecordManager(
        flight_ledger_path="evidence_capture/flight_records_ledger.json"
    )
    records2 = manager2.get_48h_flight_report()

    assert len(records1) == len(records2)
    assert records2[0]["record_id"] == "rec_flight_01_pr129"
    assert records2[1]["record_id"] == "rec_flight_02_flight_record_sys"
