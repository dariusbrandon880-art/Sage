import pytest
from sage.experimental.sports_quant import (
    FanDuelPlayerPropAnalyzer,
    FanDuelSnapshotAdapter,
    MarketSnapshot,
    PlayerPropSnapshot,
    PredictionBatchEngine,
    PredictionRecord,
    PropEdgeResult,
    build_failure_clusters,
    calculate_ev,
    calculate_kelly_stake,
    evaluate_sgp_boost,
    score_predictions,
    validate_oos_candidate,
)


BEFORE = "2026-08-30T18:00:00+00:00"
START = "2026-08-30T20:00:00+00:00"


def snapshot(event_id: str, observed: str = BEFORE) -> MarketSnapshot:
    return MarketSnapshot(
        event_id=event_id,
        sport="basketball",
        league="TEST",
        event_start_utc=START,
        observed_at_utc=observed,
        market="moneyline",
        prices={"home": 2.0, "away": 2.0},
        source="FanDuel market reference",
    )


def test_fanduel_adapter_is_read_only_and_normalizes_prices():
    parsed = FanDuelSnapshotAdapter.from_mapping({
        "event": {"id": "e1", "sport": "basketball", "league": "TEST", "start_utc": START},
        "market": {"name": "moneyline", "prices": {"home": 2.0, "away": 2.0}},
        "observed_at_utc": BEFORE,
    })
    assert FanDuelSnapshotAdapter.normalized_probabilities(parsed) == {"home": 0.5, "away": 0.5}
    assert parsed.source == "FanDuel market reference"


def test_batch_engine_generates_500_independent_locked_predictions():
    records = PredictionBatchEngine(max_workers=8).generate(
        (snapshot(f"e{i}") for i in range(250)), "cycle-500"
    )
    assert len(records) == 500
    assert len({record.prediction_id for record in records}) == 500
    assert all(record.verify_lock() for record in records)
    assert all(not record.wagering_executed for record in records)


def test_parlay_preserves_parent_and_leg_lineage():
    legs = PredictionBatchEngine().generate([snapshot("e1")], "cycle-parlay")
    parlay = PredictionBatchEngine.build_parlay("parent-1", legs)
    assert parlay.is_parlay
    assert parlay.parent_prediction_id == "parent-1"
    assert set(parlay.legs) == {leg.prediction_id for leg in legs}
    assert parlay.verify_lock()


def test_scoring_and_failure_diagnostics_are_oos_only():
    records = PredictionBatchEngine().generate([snapshot("e1"), snapshot("e2")], "cycle-score")
    outcomes = {"e1": 1, "e2": 0}
    result = score_predictions(records, outcomes)
    assert result.sample_count == 4
    assert result.resolved_count == 4
    assert result.brier_score is not None
    assert result.log_loss is not None
    failures = build_failure_clusters(records, outcomes, error_threshold=0.1)
    assert failures


def test_candidate_requires_strict_oos_brier_and_clv_improvement_on_common_events():
    baseline = [
        PredictionRecord("b1", "c", "e1", "moneyline", "home", "baseline", 0.5, 0.5, BEFORE, START).sign(),
        PredictionRecord("b2", "c", "e2", "moneyline", "home", "baseline", 0.5, 0.5, BEFORE, START).sign(),
    ]
    candidate = [
        PredictionRecord("c1", "c", "e1", "moneyline", "home", "candidate", 0.8, 0.4, BEFORE, START).sign(),
        PredictionRecord("c2", "c", "e2", "moneyline", "home", "candidate", 0.2, 0.1, BEFORE, START).sign(),
    ]
    promoted, candidate_eval, baseline_eval = validate_oos_candidate(
        candidate, baseline, {"e1": 1, "e2": 0}, min_sample_size=2
    )
    assert promoted
    assert candidate_eval.brier_score < baseline_eval.brier_score
    assert candidate_eval.clv_score > baseline_eval.clv_score


def test_american_to_decimal_conversion():
    assert FanDuelSnapshotAdapter.american_to_decimal(100) == 2.0
    assert FanDuelSnapshotAdapter.american_to_decimal(250) == 3.5
    assert FanDuelSnapshotAdapter.american_to_decimal(-110) == 1.9091
    assert FanDuelSnapshotAdapter.american_to_decimal(-200) == 1.5
    with pytest.raises(ValueError, match="odds cannot be zero"):
        FanDuelSnapshotAdapter.american_to_decimal(0)


def test_player_prop_snapshot_parsing_and_validation():
    payload = {
        "event": {"id": "nfl_101", "sport": "football", "league": "NFL", "start_utc": START},
        "prop": {
            "player_name": "Derrick Henry",
            "category": "anytime_touchdown",
            "american_prices": {"yes": -150},
            "sharp_reference_price": 1.62,
        },
        "observed_at_utc": BEFORE,
    }
    prop = FanDuelSnapshotAdapter.parse_player_prop(payload)
    assert prop.player_name == "Derrick Henry"
    assert prop.prop_category == "anytime_touchdown"
    assert prop.prices["yes"] == 1.6667
    assert prop.sharp_reference_price == 1.62


def test_ev_and_kelly_staking_calculations():
    # Win prob 0.60 at 2.0 odds => EV = (0.60 * 2.0) - 1 = +0.20 (+20% EV)
    ev = calculate_ev(0.60, 2.0)
    assert pytest.approx(ev) == 0.20

    # Kelly stake calculation under zero-wagering bounds
    kelly = calculate_kelly_stake(0.60, 2.0, fraction=0.25)
    # Full kelly = (0.6 * 1 - 0.4) / 1 = 0.20. Quarter kelly = 0.05
    assert pytest.approx(kelly) == 0.05

    # Violating zero wagering execution fails closed
    with pytest.raises(ValueError, match="SHADOW_BOUNDARY_VIOLATION"):
        calculate_kelly_stake(0.60, 2.0, wagering_executed=True)


def test_fanduel_player_prop_analyzer_nfl_atd_and_sgp_evaluation():
    payload = {
        "event_id": "nfl_102",
        "sport": "football",
        "league": "NFL",
        "event_start_utc": START,
        "observed_at_utc": BEFORE,
        "player_name": "Travis Kelce",
        "prop_category": "anytime_touchdown",
        "threshold": 0.5,
        "prices": {"yes": 2.50},  # Implied prob = 40%
        "sharp_reference_price": 2.20,  # Sharp implied = 45.45%
    }
    snap = FanDuelSnapshotAdapter.parse_player_prop(payload)
    analyzer = FanDuelPlayerPropAnalyzer()
    res = analyzer.analyze_prop(
        snap,
        selection="yes",
        red_zone_touch_share=0.35,  # Strong RZ share
        game_script_bias=1.0,
    )
    assert res.is_positive_ev
    assert res.edge_score > 0
    assert res.confidence_score >= 0.85

    prediction_rec = analyzer.generate_prop_prediction(snap, res, "cycle_props_1")
    assert prediction_rec.verify_lock()
    assert not prediction_rec.wagering_executed
    assert "Travis Kelce" in prediction_rec.selection

    # Test SGP Boost Evaluation
    sgp_result = evaluate_sgp_boost([res], boosted_decimal_price=3.0)
    assert sgp_result["recommendation"] == "GRAVY"
    assert sgp_result["all_legs_positive_ev"] is True
