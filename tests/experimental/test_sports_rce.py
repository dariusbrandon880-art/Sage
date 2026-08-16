"""Unit tests for SAGE Sports/RCE Real-World Observation & Temporal Locking Substrate."""

import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sage.experimental.sports_rce import SportsRCEResearchEngine, compute_prediction_hash


@pytest.fixture
def temp_capture_dir(tmp_path):
    return tmp_path / "evidence_capture"


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
    assert record["evidence_status"]["real_observation_proven"] is True
    assert record["evidence_status"]["model_input_type"] == "STATIC_RESEARCH_MODEL"
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


def test_sports_rce_missing_timestamp_raises_value_error(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)

    raw_event_no_ts = {
        "idEvent": "999004",
        "strEvent": "Team X vs Team Y",
        "strSport": "Soccer",
    }

    with pytest.raises(ValueError, match="Event source data missing required 'strTimestamp' field"):
        engine.create_pre_game_prediction(
            event_raw=raw_event_no_ts,
            selection="Team X",
            predicted_probability=0.50,
            reasoning="Missing timestamp",
        )


def test_sports_rce_hash_recomputation_match(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)
    future_dt = datetime.now(timezone.utc) + timedelta(hours=12)
    raw_event = {
        "idEvent": "999005",
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
        reasoning="Hash recomputation test",
    )

    recomputed_hash = compute_prediction_hash(record)
    assert record["prediction_hash"] == recomputed_hash


def test_sports_rce_reject_overwrite_conflicting_locked_artifact(temp_capture_dir):
    engine = SportsRCEResearchEngine(capture_dir=temp_capture_dir)
    future_dt = datetime.now(timezone.utc) + timedelta(hours=12)
    raw_event = {
        "idEvent": "999006",
        "strEvent": "Team Epsilon vs Team Zeta",
        "strSport": "Soccer",
        "strLeague": "Test League",
        "strHomeTeam": "Team Epsilon",
        "strAwayTeam": "Team Zeta",
        "strTimestamp": future_dt.isoformat(),
        "dateEvent": future_dt.strftime("%Y-%m-%d"),
    }

    record1 = engine.create_pre_game_prediction(
        event_raw=raw_event,
        selection="Team Epsilon",
        predicted_probability=0.55,
        reasoning="Original prediction",
    )

    file_path = engine.persist_prediction_artifact(record1, filename="test_lock_overwrite.json")
    assert file_path.exists()

    record2 = dict(record1)
    record2["selection"] = "Team Zeta"  # Conflicting selection
    record2["prediction_hash"] = compute_prediction_hash(record2)

    with pytest.raises(ValueError, match="Immutability Violation: Cannot overwrite existing locked artifact"):
        engine.persist_prediction_artifact(record2, filename="test_lock_overwrite.json")
