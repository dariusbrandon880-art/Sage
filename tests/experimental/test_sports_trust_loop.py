from sage.experimental.sports_trust_loop import (
    EligibilityDecision,
    LockedInputProvenance,
    score_prediction,
    summarize,
    validate_locked_prediction,
)
import pytest


def _eligible():
    return EligibilityDecision("e1", "ELIGIBLE", "2026-08-25T10:00:00Z", "2026-08-25T11:00:00Z")


def _provenance():
    return LockedInputProvenance("official", "2026-08-25T09:59:00Z", "moneyline", "v1", "input-hash", "payload-hash")


def test_prelock_validation_binds_provenance():
    first = validate_locked_prediction(eligibility=_eligible(), lock_timestamp_utc="2026-08-25T10:30:00Z", provenance=_provenance())
    second = validate_locked_prediction(eligibility=_eligible(), lock_timestamp_utc="2026-08-25T10:30:00Z", provenance=_provenance())
    assert first == second
    assert len(first) == 64


def test_post_close_and_ineligible_predictions_fail_closed():
    with pytest.raises(ValueError, match="LOCK_AT_OR_AFTER_MARKET_CLOSE"):
        validate_locked_prediction(eligibility=_eligible(), lock_timestamp_utc="2026-08-25T11:00:00Z", provenance=_provenance())
    with pytest.raises(ValueError, match="PREDICTION_NOT_ELIGIBLE"):
        validate_locked_prediction(eligibility=EligibilityDecision("e1", "ABSTAIN", "2026-08-25T10:00:00Z", "2026-08-25T11:00:00Z"), lock_timestamp_utc="2026-08-25T10:30:00Z", provenance=_provenance())


def test_proper_scoring_and_explicit_non_scoring_states():
    assert score_prediction(0.8, "WIN")["brier"] == pytest.approx(0.04)
    assert score_prediction(0.8, "WIN")["log_loss"] > 0
    assert score_prediction(0.8, "ABSTAIN") is None
    assert score_prediction(0.8, "VOID") is None
    assert score_prediction(0.8, "UNRESOLVED") is None


def test_summary_preserves_coverage_and_abstentions():
    report = summarize([
        {"outcome_status": "WIN", **score_prediction(0.8, "WIN")},
        {"outcome_status": "ABSTAIN"},
        {"outcome_status": "DATA_UNAVAILABLE"},
    ])
    assert report["sample_size"] == 3
    assert report["scored_count"] == 1
    assert report["coverage"] == pytest.approx(1 / 3)
    assert report["abstentions"] == 1
    assert report["unavailable"] == 1
