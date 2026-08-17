"""Unit tests for SAGE Sports/RCE Real-World Observation, Temporal Locking & RCE-002.4 Evidence Drift Monitor."""

import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sage.experimental.sports_rce import (
    SportsRCEResearchEngine,
    ObservationEvidenceSnapshot,
    ObservationDriftClassification,
    ObservationDriftRecord,
    ObservationDriftMonitor,
)
from sage.experimental.airspace.sports_adapter import SportsRCEAirspaceAdapter


@pytest.fixture
def temp_capture_dir(tmp_path):
    return tmp_path / "evidence_capture"


@pytest.fixture
def temp_drift_ledger(tmp_path):
    return tmp_path / "sports_drift_ledger.json"


# ---------------------------------------------------------
# Existing Substrate Tests
# ---------------------------------------------------------

def test_sports_rce_pre_game_temporal_lock_valid(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    future_dt = datetime.now(timezone.utc) + timedelta(hours=24)
    raw_event = {
        "idEvent": "999001",
        "strEvent": "Team Alpha vs Team Beta",
        "strSport": "Soccer",
        "strLeague": "Test League",
        "strHomeTeam": "Team Alpha",
        "strAwayTeam": "Team Beta",
        "strTimestamp": future_dt.isoformat(),
        "dateEvent": future_dt.strftime("%Y-%m-%d"),
    }

    record = engine.create_pre_game_prediction(
        event_raw=raw_event,
        selection="Team Alpha",
        predicted_probability=0.60,
        reasoning="Test model prediction",
    )

    assert record["prediction_id"] == "pred_rce_999001"
    assert record["prediction_state"] == "LOCKED"
    assert record["status"] == "PENDING"
    assert record["odds_at_lock"] == "ODDS_UNAVAILABLE"
    assert record["wagering_executed"] is False
    assert len(record["prediction_hash"]) == 64


def test_sports_rce_temporal_lock_failure_if_post_start(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    past_dt = datetime.now(timezone.utc) - timedelta(hours=2)
    raw_event = {
        "idEvent": "999002",
        "strEvent": "Past Team A vs Past Team B",
        "strSport": "Soccer",
        "strLeague": "Past League",
        "strHomeTeam": "Past Team A",
        "strAwayTeam": "Past Team B",
        "strTimestamp": past_dt.isoformat(),
    }

    with pytest.raises(ValueError, match="Temporal locking invariant failure"):
        engine.create_pre_game_prediction(
            event_raw=raw_event,
            selection="Past Team A",
            predicted_probability=0.50,
            reasoning="Attempting past lock",
        )


def test_sports_rce_persistence_and_hash_integrity(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)
    future_dt = datetime.now(timezone.utc) + timedelta(hours=12)
    raw_event = {
        "idEvent": "999003",
        "strEvent": "Team Gamma vs Team Delta",
        "strSport": "Soccer",
        "strLeague": "Test League",
        "strHomeTeam": "Team Gamma",
        "strAwayTeam": "Team Delta",
        "strTimestamp": future_dt.isoformat(),
        "dateEvent": future_dt.strftime("%Y-%m-%d"),
    }

    record = engine.create_pre_game_prediction(
        event_raw=raw_event,
        selection="Team Gamma",
        predicted_probability=0.55,
        reasoning="Persistence test",
    )

    file_path = engine.persist_prediction_artifact(record, filename="test_prediction_001.json")
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["prediction_id"] == record["prediction_id"]
    assert saved_data["prediction_hash"] == record["prediction_hash"]
    assert SportsRCEResearchEngine.verify_prediction_hash(saved_data) is True


def test_sports_rce_missing_source_data_fails_closed(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    with pytest.raises(ValueError, match="Invalid event data"):
        engine.create_pre_game_prediction({}, "Team Alpha", 0.50, "Reason")

    with pytest.raises(ValueError, match="missing 'idEvent'"):
        engine.create_pre_game_prediction({"strEvent": "E", "strTimestamp": "2026-08-17T12:00:00Z"}, "Team Alpha", 0.50, "Reason")


def test_sports_rce_missing_timestamp_fails_closed(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    raw_event = {
        "idEvent": "999004",
        "strEvent": "No Timestamp Team vs Other Team",
    }
    with pytest.raises(ValueError, match="missing 'strTimestamp'"):
        engine.create_pre_game_prediction(raw_event, "Team", 0.50, "Reason")


def test_sports_rce_flight_001_and_002_coexistence_and_preservation():
    capture_dir = Path("evidence_capture")
    flight_001_path = capture_dir / "sports_real_flight_001.json"
    flight_002_path = capture_dir / "sports_real_flight_002.json"

    assert flight_001_path.exists(), "Flight 001 artifact missing"
    assert flight_002_path.exists(), "Flight 002 artifact missing"

    with open(flight_001_path, "r", encoding="utf-8") as f:
        f1 = json.load(f)

    with open(flight_002_path, "r", encoding="utf-8") as f:
        f2 = json.load(f)

    assert f1["prediction_id"] == "pred_rce_2398016"
    assert f1["prediction_hash"] == "f9316d083b57789fd53442c6242abb3f6425921ac18f0ba294cf3ef1ef235e58"
    assert SportsRCEResearchEngine.verify_prediction_hash(f1) is True

    assert f2["prediction_id"] == "pred_rce_2398018"
    assert f2["prediction_id"] != f1["prediction_id"]
    assert f2["event_id"] != f1["event_id"]
    assert f2["prediction_hash"] != f1["prediction_hash"]
    assert SportsRCEResearchEngine.verify_prediction_hash(f2) is True


# ---------------------------------------------------------
# RCE-002.4 Evidence Drift Monitor Tests
# ---------------------------------------------------------

def test_observation_snapshot_identity(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}
    snap = monitor.create_snapshot(
        observation_id="pred_rce_2398018",
        provider="TheSportsDB",
        external_event_id="2398018",
        observed_timestamp="2026-08-17T12:00:00Z",
        retrieval_timestamp="2026-08-17T12:00:00Z",
        raw_payload=raw,
        source_observation_reference="obs_ref_001",
        evidence_reference="evidence_capture/sports_real_flight_002.json",
    )
    assert snap.snapshot_id.startswith("snap_")
    assert snap.observation_id == "pred_rce_2398018"
    assert snap.payload_hash != ""


def test_identical_observation_is_stable(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}

    snap1 = monitor.create_snapshot(
        observation_id="pred_rce_2398018",
        provider="TheSportsDB",
        external_event_id="2398018",
        observed_timestamp="2026-08-17T12:00:00Z",
        retrieval_timestamp="2026-08-17T12:00:00Z",
        raw_payload=raw,
        source_observation_reference="obs_ref_001",
        evidence_reference="ev_001",
    )
    snap2 = monitor.create_snapshot(
        observation_id="pred_rce_2398018",
        provider="TheSportsDB",
        external_event_id="2398018",
        observed_timestamp="2026-08-17T12:00:00Z",
        retrieval_timestamp="2026-08-17T12:05:00Z",
        raw_payload=raw,
        source_observation_reference="obs_ref_001",
        evidence_reference="ev_001",
    )

    drift = monitor.compare_snapshots(snap1, snap2)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_NONE
    assert drift.meaningful_semantic_change is False


def test_metadata_only_drift(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw1 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS", "non_semantic_meta": "v1"}
    raw2 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS", "non_semantic_meta": "v2"}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw1, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:10:00Z", raw2, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap1, snap2)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_METADATA_ONLY
    assert drift.meaningful_semantic_change is False


def test_status_drift_detection(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw1 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}
    raw2 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "Postponed"}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw1, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T13:00:00Z", raw2, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap1, snap2)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_STATUS_CHANGE
    assert drift.meaningful_semantic_change is True


def test_finality_drift_detection(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw1 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}
    raw2 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT", "intHomeScore": 2, "intAwayScore": 1}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw1, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T15:00:00Z", raw2, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap1, snap2)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_FINALITY_CHANGE
    assert drift.meaningful_semantic_change is True


def test_stat_correction_detection(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw1 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT", "intHomeScore": 1, "intAwayScore": 1}
    raw2 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT", "intHomeScore": 2, "intAwayScore": 1}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T15:00:00Z", raw1, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T16:00:00Z", raw2, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap1, snap2)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_STAT_CORRECTION
    assert drift.meaningful_semantic_change is True


def test_provider_conflict_detection(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT", "intHomeScore": 2, "intAwayScore": 1}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T15:00:00Z", raw, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "SportsDataIO", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T15:00:00Z", raw, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap1, snap2, provider_conflict=True)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_CONFLICT
    assert drift.meaningful_semantic_change is True


def test_duplicate_drift_not_double_counted(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}

    snap1 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw, "obs1", "ev1")
    snap2 = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:05:00Z", raw, "obs1", "ev1")

    drift1 = monitor.compare_snapshots(snap1, snap2)
    drift2 = monitor.compare_snapshots(snap1, snap2)

    assert drift1.drift_record_id == drift2.drift_record_id
    records = monitor._load_ledger()
    assert len(records) == 1  # De-duplicated!


def test_restart_reconstructs_drift_history(temp_drift_ledger):
    monitor1 = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw1 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}
    raw2 = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT", "intHomeScore": 1, "intAwayScore": 0}

    snap1 = monitor1.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw1, "obs1", "ev1")
    snap2 = monitor1.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T15:00:00Z", raw2, "obs1", "ev1")

    monitor1.compare_snapshots(snap1, snap2)

    # Re-instantiate monitor simulating process restart
    monitor2 = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    history = monitor2._load_ledger()

    assert len(history) == 1
    assert history[0]["drift_classification"] == ObservationDriftClassification.DRIFT_FINALITY_CHANGE.value


def test_original_observation_remains_immutable():
    capture_dir = Path("evidence_capture")
    flight_001_path = capture_dir / "sports_real_flight_001.json"
    with open(flight_001_path, "r", encoding="utf-8") as f:
        f1_before = json.load(f)

    # Perform drift monitor operation
    monitor = ObservationDriftMonitor()
    snap = monitor.create_snapshot("pred_rce_2398016", "TheSportsDB", "2398016", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", f1_before, "obs1", "ev1")
    _drift = monitor.compare_snapshots(snap, snap)

    with open(flight_001_path, "r", encoding="utf-8") as f:
        f1_after = json.load(f)

    assert f1_before == f1_after
    assert SportsRCEResearchEngine.verify_prediction_hash(f1_after) is True


def test_prediction_identity_unchanged():
    engine = SportsRCEResearchEngine()
    future_dt = datetime.now(timezone.utc) + timedelta(hours=24)
    raw_event = {
        "idEvent": "999005",
        "strEvent": "Team Identity A vs Team Identity B",
        "strTimestamp": future_dt.isoformat(),
    }
    pred = engine.create_pre_game_prediction(raw_event, "Team Identity A", 0.55, "Identity test")
    pid_before = pred["prediction_id"]

    # Run drift check
    monitor = ObservationDriftMonitor()
    snap = monitor.create_snapshot(pid_before, "TheSportsDB", "999005", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw_event, "obs1", "ev1")
    _drift = monitor.compare_snapshots(snap, snap)

    assert pred["prediction_id"] == pid_before


def test_score_gate_unchanged():
    # Verify drift monitor does NOT alter Brier score / calibration gates
    monitor = ObservationDriftMonitor()
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT"}
    snap = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw, "obs1", "ev1")
    assert not hasattr(snap, "brier_score")
    assert not hasattr(snap, "calibration_score")


def test_learning_gate_unchanged():
    # Verify drift monitor does NOT grant execution permissions or modify cognitive learning gates
    monitor = ObservationDriftMonitor()
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "FT"}
    snap = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw, "obs1", "ev1")
    assert not hasattr(snap, "cognitive_permission")


def test_missing_provenance_blocks_drift_claim(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    with pytest.raises(ValueError, match="Missing provenance"):
        monitor.compare_snapshots(None, None)


def test_unavailable_source_fails_closed(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    raw = {"idEvent": "2398018", "strEvent": "Lanus vs Independiente", "strStatus": "NS"}
    snap = monitor.create_snapshot("pred_rce_2398018", "TheSportsDB", "2398018", "2026-08-17T12:00:00Z", "2026-08-17T12:00:00Z", raw, "obs1", "ev1")

    drift = monitor.compare_snapshots(snap, None)
    assert drift.drift_classification == ObservationDriftClassification.DRIFT_UNAVAILABLE
    assert drift.meaningful_semantic_change is True


def test_cross_system_projection_is_read_only(temp_drift_ledger):
    monitor = ObservationDriftMonitor(storage_path=temp_drift_ledger)
    adapter = SportsRCEAirspaceAdapter(drift_monitor=monitor)
    summary = adapter.get_sports_theater_summary()

    assert "evidence_drift_status" in summary
    assert summary["evidence_drift_status"] == "OBSERVATION_STABLE"
