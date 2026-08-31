"""Unit tests for SAGE Sports Quantitative Shadow Beta execution and promotion gates."""

import pytest

from sage.experimental.sports_quant import (
    FanDuelSnapshotAdapter,
    MarketSnapshot,
    PredictionBatchEngine,
    PredictionRecord,
    build_failure_clusters,
    score_predictions,
    validate_oos_candidate,
)
from sage.experimental.sports_quant.evaluation import calculate_ev
from sage.experimental.sports_quant.learning import StakeRecommendation, calculate_kelly_stake

BEFORE = "2026-08-30T18:00:00+00:00"
START = "2026-08-30T20:00:00+00:00"


def make_snapshot(event_id: str) -> MarketSnapshot:
    return MarketSnapshot(
        event_id=event_id,
        sport="baseball",
        league="MLB",
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market="moneyline",
        prices={"home": 1.90, "away": 1.95},
        source="FanDuel market reference",
    )


def test_sports_shadow_beta_clv_ev_and_brier_scoring():
    snapshot = make_snapshot("e100")
    engine = PredictionBatchEngine()
    records = engine.generate([snapshot], "cycle-test")

    outcomes = {"e100": 1}
    closing_prices = {"e100": 0.52}
    decimal_odds_map = {"e100": 1.90}

    res = score_predictions(records, outcomes, closing_prices, decimal_odds_map)
    assert res.sample_count == 2
    assert res.brier_score is not None
    assert res.clv_score is not None
    assert res.expected_value_ev is not None


def test_sports_shadow_beta_kelly_stake_calculation():
    # 55% win probability at 2.00 decimal odds
    stake_pct = calculate_kelly_stake(0.55, 2.00, fractional_kelly=0.25, max_exposure_pct=0.05)
    assert stake_pct > 0.0
    assert stake_pct <= 0.05

    # Wager execution attempt on StakeRecommendation raises ValueError
    with pytest.raises(ValueError, match="SHADOW_BOUNDARY_VIOLATION"):
        StakeRecommendation(
            prediction_id="p1",
            event_id="e1",
            selection="home",
            predicted_probability=0.55,
            decimal_odds=2.00,
            fractional_kelly=0.25,
            recommended_stake_pct=stake_pct,
            wagering_executed=True,  # Prohibited!
        )


def test_sports_shadow_beta_candidate_promotion_gate_rejects_equal_or_worse_brier():
    snapshot1 = make_snapshot("e101")
    snapshot2 = make_snapshot("e102")

    engine = PredictionBatchEngine()
    baseline = engine.generate([snapshot1, snapshot2], "cycle-base")

    # Construct identical candidate predictions
    candidate = engine.generate([snapshot1, snapshot2], "cycle-cand")

    outcomes = {"e101": 1, "e102": 0}

    # Equal Brier score -> Candidate MUST NOT be promoted
    promoted, cand_eval, base_eval = validate_oos_candidate(candidate, baseline, outcomes)
    assert promoted is False
