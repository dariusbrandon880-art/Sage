"""Tests for SAGE Sports Trust Beta — Shadow Prediction Trust Flight Substrate."""

import pytest
from pathlib import Path
import tempfile

from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    SportsLongitudinalLedger,
)
from sage.experimental.sports_trust_beta import (
    SportsTrustShadowPrediction,
    SportsTrustBetaFlightEngine,
    SportsTrustResolution,
)


def create_sample_observation(
    event_id: str = "evt_001",
    start_time: str = "2026-09-01T20:00:00Z",
    obs_time: str = "2026-09-01T18:00:00Z",
) -> RealSportsEventObservation:
    return RealSportsEventObservation(
        event_id=event_id,
        sport="soccer",
        league="EPL",
        home_team="Arsenal",
        away_team="Chelsea",
        event_start_time_utc=start_time,
        observation_timestamp_utc=obs_time,
        source_name="Test API",
        source_url="https://api.test/events",
        market_name="match_winner",
        observed_odds={"home": 2.10, "away": 3.40, "draw": 3.20},
        event_status="NS",
    )


def test_shadow_prediction_temporal_lock_valid():
    obs = create_sample_observation()
    pred = SportsTrustShadowPrediction(
        prediction_id="pred_trust_001",
        cycle_id="cycle_001",
        event_observation=obs,
        selected_prediction="home",
        odds_at_lock="2.10",
        implied_probability=0.476,
        model_predicted_probability=0.55,
        lock_timestamp_utc="2026-09-01T19:00:00Z",
        model_state_rationale="Strong home form",
    )
    receipt_hash = pred.lock_and_sign()
    assert receipt_hash is not None
    assert len(receipt_hash) == 64
    assert pred.compute_sha256_hash() == receipt_hash


def test_shadow_prediction_post_start_lock_fails():
    obs = create_sample_observation(start_time="2026-09-01T20:00:00Z")
    with pytest.raises(ValueError, match="TEMPORAL_LOCK_VIOLATION"):
        SportsTrustShadowPrediction(
            prediction_id="pred_trust_bad",
            cycle_id="cycle_001",
            event_observation=obs,
            selected_prediction="home",
            odds_at_lock="2.10",
            implied_probability=0.476,
            model_predicted_probability=0.55,
            lock_timestamp_utc="2026-09-01T20:01:00Z",  # After start!
            model_state_rationale="Hindsight prediction",
        )


def test_real_money_wagering_rejected():
    obs = create_sample_observation()
    with pytest.raises(ValueError, match="SHADOW_BOUNDARY_VIOLATION"):
        SportsTrustShadowPrediction(
            prediction_id="pred_trust_real_money",
            cycle_id="cycle_001",
            event_observation=obs,
            selected_prediction="home",
            odds_at_lock="2.10",
            implied_probability=0.476,
            model_predicted_probability=0.55,
            lock_timestamp_utc="2026-09-01T19:00:00Z",
            model_state_rationale="Attempting real money",
            wagering_allowed=True,
        )

    with pytest.raises(ValueError, match="SHADOW_BOUNDARY_VIOLATION"):
        SportsTrustBetaFlightEngine(allow_real_wagering=True)


def test_explicit_abstention_handling():
    obs = create_sample_observation()
    engine = SportsTrustBetaFlightEngine()
    pred = engine.create_shadow_prediction(
        prediction_id="pred_abstain_001",
        cycle_id="cycle_001",
        event_observation=obs,
        selected_prediction="ABSTAIN",
        odds_at_lock="ODDS_UNAVAILABLE",
        implied_probability="ODDS_UNAVAILABLE",
        model_predicted_probability=None,
        lock_timestamp_utc="2026-09-01T19:00:00Z",
        model_state_rationale="High variance and missing key player data.",
        is_abstention=True,
        abstention_reason="HIGH_UNCERTAINTY",
    )
    assert pred.is_abstention is True
    assert pred.model_predicted_probability is None

    # Resolve abstention event
    res, out, score, learn = engine.resolve_shadow_prediction(
        prediction_id="pred_abstain_001",
        verification_source_name="Official Scoreboard",
        verification_source_url="https://api.test/scores",
        actual_home_score=1,
        actual_away_score=0,
        actual_result_text="Arsenal 1-0 Chelsea",
        outcome_status="WIN",
        verification_timestamp_utc="2026-09-01T22:00:00Z",
    )
    assert res.outcome_status == "WIN"
    assert score is None  # No Brier score penalty for abstentions
    assert learn is None

    metrics = engine.calculate_trust_metrics()
    assert metrics.abstentions == 1
    assert metrics.total_predictions == 1


def test_full_trust_flight_cycle_resolution_and_calibration():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir) / "trust_ledger.json"
        ledger = SportsLongitudinalLedger(storage_path=ledger_path)
        engine = SportsTrustBetaFlightEngine(ledger=ledger)

        # Pred 1: Win
        obs1 = create_sample_observation(event_id="evt_001")
        engine.create_shadow_prediction(
            prediction_id="pred_001",
            cycle_id="cycle_001",
            event_observation=obs1,
            selected_prediction="home",
            odds_at_lock="2.00",
            implied_probability=0.50,
            model_predicted_probability=0.60,
            lock_timestamp_utc="2026-09-01T19:00:00Z",
            model_state_rationale="Home advantage",
        )

        # Pred 2: Loss
        obs2 = create_sample_observation(event_id="evt_002")
        engine.create_shadow_prediction(
            prediction_id="pred_002",
            cycle_id="cycle_001",
            event_observation=obs2,
            selected_prediction="away",
            odds_at_lock="3.00",
            implied_probability=0.33,
            model_predicted_probability=0.40,
            lock_timestamp_utc="2026-09-01T19:00:00Z",
            model_state_rationale="Away underdog pick",
        )

        # Resolve Pred 1 -> WIN
        engine.resolve_shadow_prediction(
            prediction_id="pred_001",
            verification_source_name="Scoreboard",
            verification_source_url="https://test/scores/1",
            actual_home_score=2,
            actual_away_score=1,
            actual_result_text="Arsenal 2-1 Chelsea",
            outcome_status="WIN",
            verification_timestamp_utc="2026-09-01T22:00:00Z",
        )

        # Resolve Pred 2 -> LOSS
        engine.resolve_shadow_prediction(
            prediction_id="pred_002",
            verification_source_name="Scoreboard",
            verification_source_url="https://test/scores/2",
            actual_home_score=2,
            actual_away_score=0,
            actual_result_text="Arsenal 2-0 Chelsea",
            outcome_status="LOSS",
            verification_timestamp_utc="2026-09-01T22:00:00Z",
        )

        metrics = engine.calculate_trust_metrics()
        assert metrics.total_predictions == 2
        assert metrics.resolved_count == 2
        assert metrics.wins == 1
        assert metrics.losses == 1
        assert metrics.hit_rate == 0.5

        # Brier calculations:
        # Pred 1: (0.60 - 1.0)^2 = 0.16
        # Pred 2: (0.40 - 0.0)^2 = 0.16
        # Mean Brier = (0.16 + 0.16) / 2 = 0.16
        assert pytest.approx(metrics.brier_score, 1e-4) == 0.16
        assert pytest.approx(metrics.mean_absolute_calibration_error, 1e-4) == 0.40

        # Verify summary artifact generation
        summary = engine.generate_flight_summary()
        assert summary["flight_type"] == "SPORTS TRUST BETA — SHADOW PREDICTION FLIGHT"
        assert summary["governance_compliance"]["shadow_boundary_enforced"] is True
        assert summary["falsification_audit"]["is_clean"] is True


def test_falsification_of_contaminated_evidence():
    engine = SportsTrustBetaFlightEngine()
    obs = create_sample_observation()
    pred = engine.create_shadow_prediction(
        prediction_id="pred_tamper_001",
        cycle_id="cycle_001",
        event_observation=obs,
        selected_prediction="home",
        odds_at_lock="2.00",
        implied_probability=0.50,
        model_predicted_probability=0.60,
        lock_timestamp_utc="2026-09-01T19:00:00Z",
        model_state_rationale="Clean rationale",
    )

    # Confirm clean before tampering
    falsification_before = engine.falsify_if_contaminated()
    assert falsification_before["is_clean"] is True

    # Tamper prediction rationale without updating receipt hash
    pred.model_state_rationale = "Tampered rationale post lock!"

    falsification_after = engine.falsify_if_contaminated()
    assert falsification_after["is_clean"] is False
    assert falsification_after["verdict"] == "FALSIFIED_CONTAMINATED_EVIDENCE"
    assert falsification_after["violations_count"] == 1
