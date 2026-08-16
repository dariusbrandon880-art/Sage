"""Unit tests for SAGE Sports/RCE Real-World Observation & Temporal Locking Substrate."""

import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sage.experimental.sports_rce import SportsRCEResearchEngine


@pytest.fixture
def temp_capture_dir(tmp_path):
    return tmp_path / "evidence_capture"


def test_sports_rce_pre_game_temporal_lock_valid(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    # Event scheduled in future
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

    # Event in past
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

    # 1. Flight 001 preservation & validity
    assert f1["prediction_id"] == "pred_rce_2398016"
    assert f1["prediction_hash"] == "f9316d083b57789fd53442c6242abb3f6425921ac18f0ba294cf3ef1ef235e58"
    assert SportsRCEResearchEngine.verify_prediction_hash(f1) is True

    # 2. Flight 002 uniqueness
    assert f2["prediction_id"] == "pred_rce_2398018"
    assert f2["prediction_id"] != f1["prediction_id"]
    assert f2["event_id"] != f1["event_id"]
    assert f2["prediction_hash"] != f1["prediction_hash"]
    assert SportsRCEResearchEngine.verify_prediction_hash(f2) is True

    # 3. Temporal ordering
    obs1_dt = datetime.fromisoformat(f1["observation_timestamp"])
    start1_dt = datetime.fromisoformat(f1["event_start"])
    assert obs1_dt < start1_dt

    obs2_dt = datetime.fromisoformat(f2["observation_timestamp"])
    start2_dt = datetime.fromisoformat(f2["event_start"])
    assert obs2_dt < start2_dt

    # 4. Classification & Wagering
    for rec in (f1, f2):
        assert rec["classification"] == "REAL-WORLD RESEARCH PREDICTION"
        assert rec["wagering_executed"] is False
        assert rec["status"] == "PENDING"
        assert rec["prediction_state"] == "LOCKED"
        assert rec["odds_at_lock"] == "ODDS_UNAVAILABLE"
        assert "receipt_id" in rec
        assert "source" in rec
        assert "source_url" in rec
