from sage.experimental.sports_quant import (
    MarketSnapshot,
    PredictionRecord,
    calculate_clv,
    score_predictions,
    validate_oos_candidate,
)

BEFORE = "2026-08-30T18:00:00+00:00"
START = "2026-08-30T20:00:00+00:00"


def record(event_id: str, model: str, probability: float, market: float = 0.5) -> PredictionRecord:
    return PredictionRecord(
        f"{model}-{event_id}", "cycle", event_id, "moneyline", "home", model,
        probability, market, BEFORE, START,
    ).sign()


def test_clv_is_market_relative_and_does_not_execute_wagering():
    assert calculate_clv(0.62, 0.55) == 0.07
    r = record("e1", "shadow", 0.62, 0.55)
    assert not r.wagering_executed
    assert r.verify_lock()


def test_score_predictions_reports_clv_and_market_edge():
    result = score_predictions([record("e1", "shadow", 0.62, 0.55)], {"e1": 1})
    assert result.sample_count == 1
    assert result.clv_score == 0.07
    assert result.mean_market_edge == 0.07


def test_candidate_is_blocked_below_minimum_oos_sample():
    baseline = [record(f"e{i}", "baseline", 0.5) for i in range(2)]
    candidate = [record(f"e{i}", "candidate", 0.9 if i == 0 else 0.1) for i in range(2)]
    promoted, candidate_eval, baseline_eval = validate_oos_candidate(
        candidate, baseline, {"e0": 1, "e1": 0}, min_sample_size=3
    )
    assert not promoted
    assert candidate_eval.sample_count == baseline_eval.sample_count == 2


def test_candidate_requires_both_brier_and_clv_improvement():
    baseline = [record(f"e{i}", "baseline", 0.5, 0.5) for i in range(3)]
    candidate = [record("e0", "candidate", 0.9, 0.95), record("e1", "candidate", 0.1, 0.95), record("e2", "candidate", 0.9, 0.95)]
    promoted, _, _ = validate_oos_candidate(
        candidate, baseline, {"e0": 1, "e1": 0, "e2": 1}, min_sample_size=3
    )
    assert not promoted
