from sage.experimental.sports_quant import (
    FanDuelSnapshotAdapter,
    MarketSnapshot,
    PredictionBatchEngine,
    PredictionRecord,
    build_failure_clusters,
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
