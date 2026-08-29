"""Dedicated Unit Tests for Sports Quantitative Shadow Beta.

Verifies external signal separation, FanDuel market adapter, concurrent single/parlay workloads,
diagnostics (Brier, Log Loss, CLV, failure attribution, signal attribution), parlay leg decomposition learning,
and anti-short-term model promotion governance rules.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    ExternalSignalInput,
    SportsOutcomeRecord,
    SportsScoreRecord,
    SportsLearningRecord,
    SportsLongitudinalLedger,
    resolve_sports_prediction,
    calculate_brier_score,
    calculate_log_loss,
    calculate_clv,
    attribute_prediction_failures,
    attribute_signal_performance,
    evaluate_model_promotion_eligibility,
    ConcurrentSportsPredictionEngine
)
from sage.experimental.sports_rce import FanDuelMarketAdapter


def test_external_signal_input_separation():
    """Verifies that external signals are captured as separate intelligence inputs without mutating model decision."""
    obs = RealSportsEventObservation(
        event_id="mlb_test_001",
        sport="baseball", league="mlb",
        home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-30T19:00:00Z",
        observation_timestamp_utc="2026-08-30T18:00:00Z",
        source_name="Official MLB API",
        source_url="http://mlb.api",
        market_name="Moneyline",
        observed_odds={"home_implied_prob": 0.5200},
        event_status="Scheduled"
    )

    ext_sig = ExternalSignalInput(
        signal_id="sig_001",
        source_name="Public Consensus",
        event_id=obs.event_id,
        selection="BOS Moneyline", # External pick opposes SAGE model decision
        signal_type="PUBLIC_MONEY_SPLIT",
        confidence_or_odds="65% Money",
        timestamp_utc="2026-08-30T18:00:00Z"
    )

    pred = LockedResearchPrediction(
        prediction_id="pred_sage_001",
        cycle_id="c1",
        event_observation=obs,
        selected_prediction="NYY Moneyline", # SAGE independent decision
        odds_at_lock="-110",
        implied_probability=0.5200,
        model_predicted_probability=0.5800,
        lock_timestamp_utc="2026-08-30T18:00:00Z",
        model_state_rationale="SAGE Independent Rating Advantage",
        external_signals=[ext_sig.raw_payload or {"selection": ext_sig.selection, "source_name": ext_sig.source_name}]
    )
    pred_hash = pred.lock_and_sign()

    assert pred.selected_prediction == "NYY Moneyline"
    assert len(pred.external_signals) == 1
    assert pred.external_signals[0]["selection"] == "BOS Moneyline"
    assert pred_hash != ""


def test_fanduel_market_adapter():
    """Verifies American odds to implied probability conversion and FanDuel event structure parsing."""
    assert FanDuelMarketAdapter.american_to_implied_prob(-110) == pytest.approx(0.5238, abs=1e-3)
    assert FanDuelMarketAdapter.american_to_implied_prob(+150) == pytest.approx(0.4000, abs=1e-3)
    assert FanDuelMarketAdapter.american_to_implied_prob(0) == 0.5000

    fd_event = {
        "id": "12345",
        "home_team": "Los Angeles Dodgers",
        "away_team": "San Francisco Giants",
        "event_start_time_utc": "2026-08-30T22:00:00Z",
        "status": "Scheduled",
        "markets": {
            "moneyline": {"home": -150, "away": +130},
            "spread": {"line": -1.5},
            "totals": {"total": 8.0}
        }
    }

    parsed = FanDuelMarketAdapter.parse_fanduel_market_event(fd_event, "2026-08-30T21:00:00Z")
    assert parsed["event_id"] == "fd_game_12345"
    assert parsed["observed_odds"]["moneyline_home_american"] == -150
    assert parsed["observed_odds"]["home_implied_prob"] == pytest.approx(0.6000, abs=1e-3)


def test_concurrent_sports_prediction_engine():
    """Verifies parallel execution of single and parlay workloads."""
    obs1 = RealSportsEventObservation(
        event_id="e1", sport="baseball", league="mlb",
        home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Moneyline",
        observed_odds={"home_implied_prob": 0.5000}, event_status="Scheduled"
    )
    obs2 = RealSportsEventObservation(
        event_id="e2", sport="baseball", league="mlb",
        home_team="LAD", away_team="SF",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Moneyline",
        observed_odds={"home_implied_prob": 0.5000}, event_status="Scheduled"
    )

    def dummy_model(obs):
        return f"{obs.home_team} Moneyline", 0.6000, "Dummy rationale", "-110", 0.5238

    engine = ConcurrentSportsPredictionEngine(max_workers=2)
    res = engine.predict_singles_and_parlays_parallel([obs1, obs2], dummy_model)

    assert res["total_single_count"] == 2
    assert res["total_parlay_count"] == 1
    assert res["execution_mode"] == "CONCURRENT_PARALLEL_THREADPOOL"
    assert res["parlay_predictions"][0].is_parlay is True


def test_clv_and_log_loss_diagnostics():
    """Verifies CLV and Log Loss metric calculations."""
    clv_val = calculate_clv(0.5800, 0.5200)
    assert clv_val > 0.0  # Model prob higher than closing line prob indicates positive CLV

    preds = [
        {"outcome_status": "WIN", "model_predicted_probability": 0.60},
        {"outcome_status": "LOSS", "model_predicted_probability": 0.40}
    ]
    ll = calculate_log_loss(preds)
    assert ll is not None
    assert ll > 0.0


def test_parlay_leg_decomposition_learning():
    """Verifies that failed parlay legs decompose and produce granular learning records."""
    ledger = SportsLongitudinalLedger()

    obs_leg1 = RealSportsEventObservation(
        event_id="e_leg1", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Moneyline", observed_odds={}, event_status="Final"
    )
    obs_leg2 = RealSportsEventObservation(
        event_id="e_leg2", sport="baseball", league="mlb", home_team="LAD", away_team="SF",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Moneyline", observed_odds={}, event_status="Final"
    )

    pred_leg1 = LockedResearchPrediction(
        prediction_id="p_leg1", cycle_id="c1", event_observation=obs_leg1,
        selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.52,
        model_predicted_probability=0.58, lock_timestamp_utc="2026-08-30T19:00:00Z", model_state_rationale="Leg 1"
    )
    pred_leg2 = LockedResearchPrediction(
        prediction_id="p_leg2", cycle_id="c1", event_observation=obs_leg2,
        selected_prediction="LAD Moneyline", odds_at_lock="-110", implied_probability=0.52,
        model_predicted_probability=0.58, lock_timestamp_utc="2026-08-30T19:00:00Z", model_state_rationale="Leg 2"
    )

    obs_parlay = RealSportsEventObservation(
        event_id="e_parlay", sport="baseball", league="mlb", home_team="Multi", away_team="Multi",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Parlay", observed_odds={}, event_status="Final"
    )
    pred_parlay = LockedResearchPrediction(
        prediction_id="p_parlay", cycle_id="c1", event_observation=obs_parlay,
        selected_prediction="Parlay", odds_at_lock="+260", implied_probability=0.27,
        model_predicted_probability=0.33, lock_timestamp_utc="2026-08-30T19:00:00Z", model_state_rationale="Parlay",
        is_parlay=True, parlay_legs=[{"prediction_id": "p_leg1"}, {"prediction_id": "p_leg2"}]
    )

    ledger.add_prediction(pred_leg1)
    ledger.add_prediction(pred_leg2)
    ledger.add_prediction(pred_parlay)

    # Resolve leg 1 as WIN, leg 2 as LOSS
    out1, sc1, lrn1 = resolve_sports_prediction(pred_leg1, "API", "http", 5, 3, "NYY won", "WIN", "2026-08-30T23:00:00Z")
    out2, sc2, lrn2 = resolve_sports_prediction(pred_leg2, "API", "http", 1, 4, "SF won", "LOSS", "2026-08-30T23:00:00Z")

    ledger.add_outcome(out1); ledger.add_score(sc1); ledger.add_learning(lrn1)
    ledger.add_outcome(out2); ledger.add_score(sc2); ledger.add_learning(lrn2)

    # Resolve parlay
    p_out, p_sc, p_lrn = ledger.resolve_parlay_if_legs_complete("p_parlay", "API", "http", "2026-08-30T23:00:00Z")
    assert p_out.outcome_status == "LOSS"
    assert p_lrn.failure_classification == "PARLAY_MULTILEG_FAILURE"
    assert "p_leg2" in p_lrn.model_assumption_broken


def test_anti_short_term_batch_model_promotion_governance():
    """Verifies that a model cannot be promoted based merely on short-term win batches."""
    ledger = SportsLongitudinalLedger()

    obs = RealSportsEventObservation(
        event_id="e1", sport="baseball", league="mlb", home_team="NYY", away_team="BOS",
        event_start_time_utc="2026-08-30T20:00:00Z", observation_timestamp_utc="2026-08-30T19:00:00Z",
        source_name="API", source_url="http", market_name="Moneyline", observed_odds={}, event_status="Final"
    )

    # Only 2 resolved predictions (short-term batch)
    for i in range(2):
        pred = LockedResearchPrediction(
            prediction_id=f"p_short_{i}", cycle_id="c1", event_observation=obs,
            selected_prediction="NYY Moneyline", odds_at_lock="-110", implied_probability=0.52,
            model_predicted_probability=0.60, lock_timestamp_utc="2026-08-30T19:00:00Z", model_state_rationale="Short"
        )
        ledger.add_prediction(pred)
        out, sc, lrn = resolve_sports_prediction(pred, "API", "http", 5, 3, "NYY won", "WIN", "2026-08-30T23:00:00Z")
        ledger.add_outcome(out); ledger.add_score(sc); ledger.add_learning(lrn)

    eval_result = evaluate_model_promotion_eligibility(ledger, min_sample_size=10, max_brier_threshold=0.25)
    assert eval_result["promotion_eligible"] is False
    assert eval_result["governance_decision"] == "PROMOTION_DENIED_SHORT_TERM_OR_UNCALIBRATED"
    assert "INSUFFICIENT_SAMPLE_SIZE" in eval_result["reasons"][0]
