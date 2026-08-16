"""Unit tests for Sports Longitudinal & Real Observation Primitive."""

import pytest
from pathlib import Path
from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    RealOutcomeVerification,
    calculate_brier_score,
    classify_prediction_failure,
    SportsLongitudinalLedger,
    persist_flight_artifact
)

def test_locked_research_prediction_sha256_signing():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_nyy_bos",
        sport="baseball",
        league="mlb",
        home_team="Boston Red Sox",
        away_team="New York Yankees",
        event_start_time_utc="2026-08-16T23:10:00Z",
        observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API (statsapi.mlb.com)",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": -110, "away": -110},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_001",
        cycle_id="cycle_real_20260816_01",
        event_observation=obs,
        selected_prediction="New York Yankees Moneyline",
        odds_at_lock="-110",
        implied_probability=0.5238,
        model_predicted_probability=0.5850,
        lock_timestamp_utc="2026-08-16T20:05:00Z",
        model_state_rationale="Yankees starting pitcher recent ERA advantage."
    )

    h1 = pred.lock_and_sign()
    assert len(h1) == 64
    assert pred.sha256_receipt_hash == h1

    # Recomputing SHA-256 matches
    assert pred.compute_sha256_hash() == h1

def test_temporal_lock_violation_rejection():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_nyy_bos",
        sport="baseball",
        league="mlb",
        home_team="Boston Red Sox",
        away_team="New York Yankees",
        event_start_time_utc="2026-08-16T20:00:00Z",
        observation_timestamp_utc="2026-08-16T20:05:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": -110, "away": -110},
        event_status="STATUS_IN_PROGRESS"
    )

    # Attempt lock after event start -> expect ValueError
    with pytest.raises(ValueError, match="TEMPORAL_LOCK_VIOLATION"):
        LockedResearchPrediction(
            prediction_id="pred_real_post_start",
            cycle_id="cycle_real_20260816_01",
            event_observation=obs,
            selected_prediction="New York Yankees Moneyline",
            odds_at_lock="-110",
            implied_probability=0.5238,
            model_predicted_probability=0.5850,
            lock_timestamp_utc="2026-08-16T20:05:00Z", # Post-start!
            model_state_rationale="Invalid post-start attempt."
        )

def test_temporal_lock_exact_start_time_rejection():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_nyy_bos",
        sport="baseball",
        league="mlb",
        home_team="Boston Red Sox",
        away_team="New York Yankees",
        event_start_time_utc="2026-08-16T20:00:00Z",
        observation_timestamp_utc="2026-08-16T20:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": -110, "away": -110},
        event_status="STATUS_IN_PROGRESS"
    )

    # Lock timestamp EXACTLY at event start time MUST BE rejected
    with pytest.raises(ValueError, match="TEMPORAL_LOCK_VIOLATION"):
        LockedResearchPrediction(
            prediction_id="pred_real_exact_start",
            cycle_id="cycle_real_20260816_01",
            event_observation=obs,
            selected_prediction="New York Yankees Moneyline",
            odds_at_lock="-110",
            implied_probability=0.5238,
            model_predicted_probability=0.5850,
            lock_timestamp_utc="2026-08-16T20:00:00Z", # Exact start!
            model_state_rationale="Exact start time attempt."
        )

def test_duplicate_prediction_id_rejection():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_lad_sdp",
        sport="baseball",
        league="mlb",
        home_team="San Diego Padres",
        away_team="Los Angeles Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_dup_001",
        cycle_id="cycle_real_20260816_01",
        event_observation=obs,
        selected_prediction="Los Angeles Dodgers Moneyline",
        odds_at_lock="-125",
        implied_probability=0.5556,
        model_predicted_probability=0.6200,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Dodgers offensive run rate model advantage."
    )
    pred.lock_and_sign()

    outcome = RealOutcomeVerification(
        outcome_id="out_dup_001",
        prediction_id="pred_dup_001",
        verification_timestamp_utc="2026-08-17T01:30:00Z",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=3,
        actual_away_score=5,
        actual_result_text="Los Angeles Dodgers defeated San Diego Padres 5-3",
        outcome_status="WIN"
    )
    outcome.sign()

    ledger = SportsLongitudinalLedger()
    ledger.add_entry(pred, outcome)

    # Adding second entry with duplicate prediction_id fails closed
    with pytest.raises(ValueError, match="DUPLICATE_PREDICTION_ID"):
        ledger.add_entry(pred, outcome)

def test_pending_outcome_remains_unresolved():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_future_game",
        sport="baseball",
        league="mlb",
        home_team="Team A",
        away_team="Team B",
        event_start_time_utc="2026-08-16T22:00:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"status": "ODDS_UNAVAILABLE"},
        event_status="Scheduled"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_pending_001",
        cycle_id="cycle_real_20260816_01",
        event_observation=obs,
        selected_prediction="Team A Moneyline",
        odds_at_lock="ODDS_UNAVAILABLE",
        implied_probability=0.5000,
        model_predicted_probability=0.5500,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Model baseline."
    )
    pred.lock_and_sign()

    outcome_pending = RealOutcomeVerification(
        outcome_id="out_pending_001",
        prediction_id="pred_pending_001",
        verification_timestamp_utc="2026-08-16T21:10:00Z",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=None,
        actual_away_score=None,
        actual_result_text="Game not yet started.",
        outcome_status="PENDING"
    )

    ledger = SportsLongitudinalLedger()
    ledger.add_entry(pred, outcome_pending)

    summary = ledger.generate_summary_report()
    assert summary["pending_outcomes"] == 1
    assert summary["resolved_outcomes"] == 0
    assert summary["brier_score"] is None

def test_independent_outcome_resolution_transition():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_transition_game",
        sport="baseball",
        league="mlb",
        home_team="Team A",
        away_team="Team B",
        event_start_time_utc="2026-08-16T22:00:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"status": "ODDS_UNAVAILABLE"},
        event_status="Scheduled"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_trans_001",
        cycle_id="cycle_real_20260816_01",
        event_observation=obs,
        selected_prediction="Team A Moneyline",
        odds_at_lock="ODDS_UNAVAILABLE",
        implied_probability=0.5000,
        model_predicted_probability=0.6000,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Model baseline."
    )
    pred.lock_and_sign()

    # Step 1: Initial state is pending
    outcome_pending = RealOutcomeVerification(
        outcome_id="out_trans_001_p",
        prediction_id="pred_trans_001",
        verification_timestamp_utc="2026-08-16T21:10:00Z",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=None,
        actual_away_score=None,
        actual_result_text="Game not started.",
        outcome_status="PENDING"
    )

    ledger_p = SportsLongitudinalLedger()
    ledger_p.add_entry(pred, outcome_pending)
    assert ledger_p.generate_summary_report()["pending_outcomes"] == 1

    # Step 2: Independent outcome resolution after game completion
    outcome_completed = RealOutcomeVerification(
        outcome_id="out_trans_001_c",
        prediction_id="pred_trans_001",
        verification_timestamp_utc="2026-08-17T02:00:00Z",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=5,
        actual_away_score=2,
        actual_result_text="Team A defeated Team B 5-2",
        outcome_status="WIN"
    )

    ledger_c = SportsLongitudinalLedger()
    ledger_c.add_entry(pred, outcome_completed)
    summary_c = ledger_c.generate_summary_report()

    assert summary_c["pending_outcomes"] == 0
    assert summary_c["resolved_outcomes"] == 1
    assert summary_c["wins"] == 1
    assert summary_c["brier_score"] == pytest.approx((0.60 - 1.0) ** 2, abs=1e-4)

def test_persist_flight_artifact_idempotent_protection(tmp_path):
    flight_data = {
        "flight_record": {
            "prediction_id": "pred_test_persist_001"
        }
    }
    artifact_path = tmp_path / "sports_real_flight_001.json"

    # First write
    p1 = persist_flight_artifact(flight_data, artifact_path)
    assert p1.exists()

    # Second write with same prediction_id is safely idempotent
    p2 = persist_flight_artifact(flight_data, artifact_path)
    assert p2 == p1

def test_brier_score_calculation():
    predictions = [
        {"outcome_status": "WIN", "model_predicted_probability": 0.8},  # (0.8 - 1.0)^2 = 0.04
        {"outcome_status": "LOSS", "model_predicted_probability": 0.3}, # (0.3 - 0.0)^2 = 0.09
        {"outcome_status": "PENDING", "model_predicted_probability": 0.5} # Excluded
    ]

    brier = calculate_brier_score(predictions)
    assert brier == pytest.approx((0.04 + 0.09) / 2.0, abs=1e-4)

def test_sports_longitudinal_ledger():
    obs = RealSportsEventObservation(
        event_id="mlb_20260816_lad_sdp",
        sport="baseball",
        league="mlb",
        home_team="San Diego Padres",
        away_team="Los Angeles Dodgers",
        event_start_time_utc="2026-08-16T22:10:00Z",
        observation_timestamp_utc="2026-08-16T21:00:00Z",
        source_name="Official MLB Stats API",
        source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        market_name="Moneyline",
        observed_odds={"home": "+105", "away": "-125"},
        event_status="STATUS_SCHEDULED"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_real_002",
        cycle_id="cycle_real_20260816_01",
        event_observation=obs,
        selected_prediction="Los Angeles Dodgers Moneyline",
        odds_at_lock="-125",
        implied_probability=0.5556,
        model_predicted_probability=0.6200,
        lock_timestamp_utc="2026-08-16T21:05:00Z",
        model_state_rationale="Dodgers offensive run rate model advantage."
    )
    pred.lock_and_sign()

    outcome = RealOutcomeVerification(
        outcome_id="out_real_002",
        prediction_id="pred_real_002",
        verification_timestamp_utc="2026-08-17T01:30:00Z",
        verification_source_name="Official MLB Stats API",
        verification_source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",
        actual_home_score=3,
        actual_away_score=5,
        actual_result_text="Los Angeles Dodgers defeated San Diego Padres 5-3",
        outcome_status="WIN"
    )
    outcome.sign()

    ledger = SportsLongitudinalLedger()
    entry = ledger.add_entry(pred, outcome)

    assert entry["classification"] == "REAL-WORLD OBSERVATION / REAL-WORLD RESEARCH PREDICTION"
    assert entry["prediction_id"] == "pred_real_002"

    summary = ledger.generate_summary_report()
    assert summary["total_records"] == 1
    assert summary["wins"] == 1
    assert summary["win_rate"] == 1.0
    assert summary["brier_score"] == pytest.approx((0.62 - 1.0) ** 2, abs=1e-4)
