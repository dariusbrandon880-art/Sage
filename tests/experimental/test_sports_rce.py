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
