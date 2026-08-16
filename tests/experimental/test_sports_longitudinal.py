"""Unit tests for Sports Longitudinal & Real Observation Primitive."""

import pytest
from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    RealOutcomeVerification,
    calculate_brier_score,
    classify_prediction_failure,
    SportsLongitudinalLedger
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
        source_name="ESPN Public Scoreboard API",
        source_url="https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
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
        source_name="ESPN Public Scoreboard API",
        source_url="https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
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
        verification_source_name="ESPN Public Scoreboard API",
        verification_source_url="https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
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
