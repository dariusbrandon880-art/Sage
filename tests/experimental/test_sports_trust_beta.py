"""Tests for SAGE Sports Trust Beta — Shadow Prediction Trust Flight Substrate."""

import pytest
from pathlib import Path
import tempfile

from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    SportsLongitudinalLedger,
    SportsOutcomeRecord,
    SportsScoreRecord,
)
from sage.experimental.sports_trust_beta import (
    SportsTrustShadowPrediction,
    SportsTrustBetaFlightEngine,
    SportsTrustResolution,
    devig_two_way_odds,
    compute_log_loss,
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
        market_close_timestamp_utc="2026-09-01T19:55:00Z",
    )
    receipt_hash = pred.lock_and_sign()
    assert receipt_hash is not None
    assert len(receipt_hash) == 64
    assert pred.compute_sha256_hash() == receipt_hash
    assert pred.model_procedure_fingerprint != ""
    assert pred.input_data_fingerprint != ""


def test_market_close_temporal_lock_rejection():
    obs = create_sample_observation(start_time="2026-09-01T20:00:00Z")
    with pytest.raises(ValueError, match="MARKET_CLOSE_TEMPORAL_LOCK_VIOLATION"):
        SportsTrustShadowPrediction(
            prediction_id="pred_trust_mkt_close_bad",
            cycle_id="cycle_001",
            event_observation=obs,
            selected_prediction="home",
            odds_at_lock="2.10",
            implied_probability=0.476,
            model_predicted_probability=0.55,
            lock_timestamp_utc="2026-09-01T19:56:00Z",
            market_close_timestamp_utc="2026-09-01T19:55:00Z",  # Lock is AFTER market close!
            model_state_rationale="Late lock attempt",
        )


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
            lock_timestamp_utc="2026-09-01T20:01:00Z",
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


def test_first_class_outcome_states_end_to_end():
    engine = SportsTrustBetaFlightEngine()
    valid_statuses = [
        "WIN",
        "LOSS",
        "PUSH",
        "VOID",
        "UNRESOLVED",
        "ABSTAIN",
        "DATA_UNAVAILABLE",
        "INVALID_POST_LOCK",
        "SOURCE_UNAVAILABLE",
    ]

    for idx, status in enumerate(valid_statuses):
        pred_id = f"pred_state_{idx}"
        obs = create_sample_observation(event_id=f"evt_state_{idx}")
        engine.create_shadow_prediction(
            prediction_id=pred_id,
            cycle_id="cycle_001",
            event_observation=obs,
            selected_prediction="home" if status != "ABSTAIN" else "ABSTAIN",
            odds_at_lock="2.00",
            implied_probability=0.50,
            model_predicted_probability=0.60 if status != "ABSTAIN" else None,
            lock_timestamp_utc="2026-09-01T19:00:00Z",
            model_state_rationale=f"Testing status {status}",
            is_abstention=(status == "ABSTAIN"),
        )

        res, out, score, learn = engine.resolve_shadow_prediction(
            prediction_id=pred_id,
            verification_source_name="Official Scoreboard",
            verification_source_url="https://api.test/scores",
            actual_home_score=1 if status in ["WIN", "LOSS", "PUSH"] else None,
            actual_away_score=0 if status in ["WIN", "LOSS", "PUSH"] else None,
            actual_result_text=f"Status: {status}",
            outcome_status=status,
            verification_timestamp_utc="2026-09-01T22:00:00Z",
        )
        assert res.outcome_status == status
        assert out.outcome_status == status


def test_devig_and_clv_benchmark_metrics():
    # Devig calculations: 1.90 (0.5263) and 1.90 (0.5263) -> sum 1.0526 -> normalized 0.50, 0.50
    devig_a, devig_b = devig_two_way_odds(0.5263, 0.5263)
    assert pytest.approx(devig_a, 1e-3) == 0.50
    assert pytest.approx(devig_b, 1e-3) == 0.50

    # Test Log loss computation
    loss = compute_log_loss([0.8, 0.2], [1.0, 0.0])
    assert loss is not None
    assert loss < 0.3  # Well-calibrated predictions have low log loss


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
            devig_closing_probability=0.52,
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
            devig_closing_probability=0.35,
        )

        metrics = engine.calculate_trust_metrics()
        assert metrics.total_predictions == 2
        assert metrics.resolved_count == 2
        assert metrics.wins == 1
        assert metrics.losses == 1
        assert metrics.hit_rate == 0.5

        assert metrics.brier_score is not None
        assert metrics.baseline_brier_score is not None
        assert metrics.log_loss is not None
        assert metrics.baseline_log_loss is not None
        assert metrics.mean_clv_beat_margin is not None

        summary = engine.generate_flight_summary()
        assert summary["flight_type"] == "SPORTS TRUST BETA — SHADOW PREDICTION FLIGHT"
        assert summary["governance_compliance"]["shadow_boundary_enforced"] is True
        assert summary["falsification_audit"]["is_clean"] is True


def test_durable_ledger_restart_and_replay_determinism():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir) / "durable_trust_ledger.json"

        # Session 1: Create prediction & outcome
        ledger1 = SportsLongitudinalLedger(storage_path=ledger_path)
        engine1 = SportsTrustBetaFlightEngine(ledger=ledger1)

        obs = create_sample_observation(event_id="evt_restart_001")
        pred1 = engine1.create_shadow_prediction(
            prediction_id="pred_restart_001",
            cycle_id="cycle_001",
            event_observation=obs,
            selected_prediction="home",
            odds_at_lock="2.00",
            implied_probability=0.50,
            model_predicted_probability=0.65,
            lock_timestamp_utc="2026-09-01T19:00:00Z",
            model_state_rationale="Restart test rationale",
        )

        res1, out1, score1, learn1 = engine1.resolve_shadow_prediction(
            prediction_id="pred_restart_001",
            verification_source_name="Scoreboard",
            verification_source_url="https://test/scores/restart",
            actual_home_score=3,
            actual_away_score=1,
            actual_result_text="Arsenal 3-1 Chelsea",
            outcome_status="WIN",
            verification_timestamp_utc="2026-09-01T22:00:00Z",
        )

        # Session 2: Reload ledger from disk in fresh process memory
        ledger2 = SportsLongitudinalLedger(storage_path=ledger_path)
        assert len(ledger2.predictions) == 1
        assert len(ledger2.outcomes) == 1
        assert len(ledger2.scores) == 1
        assert len(ledger2.learnings) == 1

        reloaded_pred = ledger2.predictions[0]
        reloaded_out = ledger2.outcomes[0]

        assert reloaded_pred.prediction_id == "pred_restart_001"
        assert reloaded_pred.sha256_receipt_hash == pred1.sha256_receipt_hash
        assert reloaded_out.outcome_receipt_hash == out1.outcome_receipt_hash


def test_extended_falsification_matrix():
    engine = SportsTrustBetaFlightEngine()
    obs = create_sample_observation()
    pred = engine.create_shadow_prediction(
        prediction_id="pred_falsify_001",
        cycle_id="cycle_001",
        event_observation=obs,
        selected_prediction="home",
        odds_at_lock="2.00",
        implied_probability=0.50,
        model_predicted_probability=0.60,
        lock_timestamp_utc="2026-09-01T19:00:00Z",
        model_state_rationale="Clean rationale",
    )

    # 1. Duplicate resolution attempt fails closed
    engine.resolve_shadow_prediction(
        prediction_id="pred_falsify_001",
        verification_source_name="Scoreboard",
        verification_source_url="https://test/scores/1",
        actual_home_score=1,
        actual_away_score=0,
        actual_result_text="Arsenal 1-0 Chelsea",
        outcome_status="WIN",
        verification_timestamp_utc="2026-09-01T22:00:00Z",
    )

    with pytest.raises(ValueError, match="DUPLICATE_RESOLUTION_ATTEMPT"):
        out_dup = SportsOutcomeRecord(
            outcome_id="out_dup_001",
            prediction_id="pred_falsify_001",
            prediction_hash=pred.sha256_receipt_hash,
            verification_timestamp_utc="2026-09-01T22:05:00Z",
            verification_source_name="Duplicate Source",
            verification_source_url="https://test/scores/dup",
            actual_home_score=1,
            actual_away_score=0,
            actual_result_text="Arsenal 1-0 Chelsea",
            outcome_status="WIN",
        )
        engine.ledger.add_outcome(out_dup)

    # 2. Orphan scoring attempt without verified outcome fails closed
    with pytest.raises(ValueError, match="SCORE_WITHOUT_OUTCOME_FAIL"):
        orphan_score = SportsScoreRecord(
            score_id="score_orphan_001",
            prediction_id="non_existent_pred",
            prediction_hash="0" * 64,
            outcome_id="non_existent_out",
            score_timestamp_utc="2026-09-01T22:10:00Z",
            model_predicted_probability=0.5,
            outcome_status="WIN",
            brier_score_contribution=0.25,
        )
        engine.ledger.add_score(orphan_score)
