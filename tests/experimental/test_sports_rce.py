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


# =====================================================================
# RCE-003.1: TEMPORAL RESEARCH SNAPSHOT & LEAKAGE RECEIPT TESTS
# =====================================================================

from dataclasses import asdict
from sage.experimental.sports_rce import (
    HistoricalResearchSnapshot,
    ResearchIntegrityReceipt,
    HistoricalResearchReconstructionEngine,
)
from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    resolve_sports_prediction,
    SportsLongitudinalLedger,
)


def test_research_snapshot_creation():
    obs = [
        {
            "observation_id": "obs_001",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T12:00:00Z",
            "selection": "Team A",
            "observed_odds": "-110",
        }
    ]
    snapshot, receipt = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs,
        research_timestamp="2026-08-16T15:00:00Z",
    )
    assert isinstance(snapshot, HistoricalResearchSnapshot)
    assert isinstance(receipt, ResearchIntegrityReceipt)
    assert len(snapshot.included_observations) == 1
    assert snapshot.snapshot_hash != ""
    assert receipt.integrity_status == "RESEARCH_TIME_CLEAN"


def test_as_of_observation_selection():
    obs = [
        {
            "observation_id": "obs_v1",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T12:00:00Z",
            "selection": "Team A",
            "observed_odds": "-110",
        },
        {
            "observation_id": "obs_v2",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T14:00:00Z",
            "selection": "Team A",
            "observed_odds": "-115",
        },
    ]
    # As of 13:00, obs_v1 is latest available
    snap1, rcpt1 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T13:00:00Z"
    )
    assert len(snap1.included_observations) == 1
    assert snap1.included_observations[0]["observation_id"] == "obs_v1"

    # As of 15:00, obs_v2 is latest available
    snap2, rcpt2 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T15:00:00Z"
    )
    assert len(snap2.included_observations) == 1
    assert snap2.included_observations[0]["observation_id"] == "obs_v2"


def test_late_observation_excluded():
    obs = [
        {
            "observation_id": "obs_early",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T12:00:00Z",
        },
        {
            "observation_id": "obs_late",
            "event_id": "ev_1002",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T18:00:00Z",
        },
    ]
    snapshot, receipt = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T15:00:00Z"
    )
    assert len(snapshot.included_observations) == 1
    assert snapshot.included_observations[0]["observation_id"] == "obs_early"
    assert len(snapshot.excluded_post_t_observations) == 1
    assert snapshot.excluded_post_t_observations[0]["observation_id"] == "obs_late"


def test_post_timestamp_information_detected():
    obs = [
        {
            "observation_id": "obs_001",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T18:00:00Z",
        }
    ]
    snapshot, receipt = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T15:00:00Z"
    )
    assert receipt.integrity_status == "POST_TIMESTAMP_INFORMATION_DETECTED"
    assert receipt.excluded_count == 1


def test_correction_respects_availability_time():
    obs = [
        {
            "observation_id": "obs_orig",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T12:00:00Z",
            "odds": "-110",
        },
        {
            "observation_id": "obs_corr",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T16:00:00Z",
            "odds": "-120",
        },
    ]
    # As of T=14:00, correction at 16:00 is EXCLUDED
    snap_before, rcpt_before = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T14:00:00Z"
    )
    assert snap_before.included_observations[0]["observation_id"] == "obs_orig"
    assert rcpt_before.integrity_status == "POST_TIMESTAMP_INFORMATION_DETECTED"

    # As of T=17:00, correction at 16:00 is INCLUDED
    snap_after, rcpt_after = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T17:00:00Z"
    )
    assert snap_after.included_observations[0]["observation_id"] == "obs_corr"
    assert rcpt_after.integrity_status == "RESEARCH_TIME_CLEAN"


def test_provider_conflict_preserved():
    obs = [
        {
            "observation_id": "obs_p1",
            "event_id": "ev_1001",
            "provider": "provider_alpha",
            "availability_timestamp": "2026-08-16T12:00:00Z",
            "observed_odds": "-110",
        },
        {
            "observation_id": "obs_p2",
            "event_id": "ev_1001",
            "provider": "provider_beta",
            "availability_timestamp": "2026-08-16T12:00:00Z",
            "observed_odds": "+105",
        },
    ]
    snapshot, receipt = HistoricalResearchReconstructionEngine.reconstruct_snapshot(
        observations=obs, research_timestamp="2026-08-16T15:00:00Z"
    )
    assert len(snapshot.conflicts) == 1
    assert snapshot.conflicts[0]["event_id"] == "ev_1001"
    assert "provider_alpha" in snapshot.provider_states
    assert "provider_beta" in snapshot.provider_states


def test_missing_availability_fails_closed():
    obs = [{"observation_id": "obs_no_ts", "event_id": "ev_1001"}]
    with pytest.raises(ValueError, match="FAIL_CLOSED_MISSING_TIMESTAMP"):
        HistoricalResearchReconstructionEngine.reconstruct_snapshot(
            observations=obs, research_timestamp="2026-08-16T15:00:00Z"
        )


def test_ambiguous_timestamp_fails_closed():
    obs = [
        {
            "observation_id": "obs_bad_ts",
            "event_id": "ev_1001",
            "availability_timestamp": "INVALID_TIMESTAMP_STRING",
        }
    ]
    with pytest.raises(ValueError, match="FAIL_CLOSED_AMBIGUOUS_TIMING"):
        HistoricalResearchReconstructionEngine.reconstruct_snapshot(
            observations=obs, research_timestamp="2026-08-16T15:00:00Z"
        )


def test_snapshot_hash_deterministic():
    obs = [
        {
            "observation_id": "obs_001",
            "event_id": "ev_1001",
            "provider": "provider_a",
            "availability_timestamp": "2026-08-16T12:00:00Z",
        }
    ]
    s1, r1 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T15:00:00Z")
    s2, r2 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T15:00:00Z")
    assert s1.snapshot_hash == s2.snapshot_hash
    assert r1.integrity_hash == r2.integrity_hash


def test_repeated_snapshot_is_identical():
    obs = [
        {"observation_id": f"obs_{i}", "event_id": f"ev_{i}", "provider": "p", "availability_timestamp": f"2026-08-16T1{i}:00:00Z"}
        for i in range(5)
    ]
    s1, _ = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T14:30:00Z")
    s2, _ = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T14:30:00Z")
    assert s1 == s2


def test_restart_reconstructs_identical_snapshot():
    obs_json = json.dumps([
        {"observation_id": "obs_restart", "event_id": "ev_restart", "provider": "p1", "availability_timestamp": "2026-08-16T12:00:00Z"}
    ])
    # Rehydrate from JSON
    rehydrated_obs = json.loads(obs_json)
    s1, r1 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(rehydrated_obs, "2026-08-16T15:00:00Z")
    s2, r2 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(rehydrated_obs, "2026-08-16T15:00:00Z")
    assert s1.snapshot_hash == s2.snapshot_hash


def test_observation_history_immutable():
    obs = [
        {"observation_id": "obs_immut", "event_id": "ev_1001", "provider": "p1", "availability_timestamp": "2026-08-16T12:00:00Z"}
    ]
    obs_copy = json.loads(json.dumps(obs))
    HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T15:00:00Z")
    assert obs == obs_copy


def test_prediction_identity_unchanged():
    obs_event = RealSportsEventObservation(
        event_id="ev_pred_test",
        sport="baseball",
        league="mlb",
        home_team="Team A",
        away_team="Team B",
        event_start_time_utc="2026-08-16T20:00:00Z",
        observation_timestamp_utc="2026-08-16T18:00:00Z",
        source_name="Source A",
        source_url="http://example.com",
        market_name="Moneyline",
        observed_odds={"home": -110},
        event_status="SCHEDULED",
    )
    pred = LockedResearchPrediction(
        prediction_id="pred_identity_001",
        cycle_id="c1",
        event_observation=obs_event,
        selected_prediction="Team A Moneyline",
        odds_at_lock="-110",
        implied_probability=0.5238,
        model_predicted_probability=0.5800,
        lock_timestamp_utc="2026-08-16T18:05:00Z",
        model_state_rationale="Test rationale",
    )
    h_before = pred.lock_and_sign()

    # Reconstruct snapshot over prediction observation dictionary
    obs_dict = [asdict(obs_event)]
    obs_dict[0]["availability_timestamp"] = obs_dict[0]["observation_timestamp_utc"]
    HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs_dict, "2026-08-16T19:00:00Z")

    h_after = pred.compute_sha256_hash()
    assert h_before == h_after


def test_outcome_gate_unchanged():
    ledger = SportsLongitudinalLedger()
    summary = ledger.generate_summary_report()
    assert summary["resolved_outcomes"] == 0
    assert summary["unresolved_outcomes"] == 0


def test_score_gate_unchanged():
    ledger = SportsLongitudinalLedger()
    assert len(ledger.scores) == 0


def test_learning_gate_unchanged():
    ledger = SportsLongitudinalLedger()
    assert len(ledger.learnings) == 0


def test_leakage_receipt_is_replayable():
    obs = [
        {"observation_id": "obs_1", "event_id": "ev_1", "provider": "p", "availability_timestamp": "2026-08-16T12:00:00Z"},
        {"observation_id": "obs_2", "event_id": "ev_2", "provider": "p", "availability_timestamp": "2026-08-16T18:00:00Z"},
    ]
    s1, r1 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T15:00:00Z")
    s2, r2 = HistoricalResearchReconstructionEngine.reconstruct_snapshot(obs, "2026-08-16T15:00:00Z")
    assert r1.integrity_hash == r2.integrity_hash
    assert r1.included_reference_set == r2.included_reference_set
    assert r1.post_timestamp_reference_set == r2.post_timestamp_reference_set
