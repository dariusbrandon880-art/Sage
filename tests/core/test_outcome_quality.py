"""Unit tests for the Governed Outcome Quality Contract and Metacognitive integration."""

import pytest

from sage.core.outcome_reconciliation import (
    OutcomeReconciliation,
    OutcomeReconciliationStatus,
)
from sage.core.outcome_quality import (
    OutcomeQualityContract,
    OutcomeQualityValidationError,
    apply_outcome_to_metacognitive_state,
    evaluate_outcome_quality,
)
from sage.experimental.sagi.metacognition import (
    MetacognitiveEngine,
    MetacognitiveState,
)


def _make_sample_reconciliation(
    status: OutcomeReconciliationStatus = OutcomeReconciliationStatus.RECONCILED,
) -> OutcomeReconciliation:
    return OutcomeReconciliation.reconcile(
        decision_id="dec_test_1001",
        context_id="ctx_test_2002",
        t0_claim_ref="claim_t0_3003",
        t1_observation_ref="obs_t1_4004",
        reality_gap_assessment_ref="gap_5005",
        outcome_ref="out_6006",
        status=status,
        rationale="Lineage verified against canonical observation ledger.",
    )


def test_fail_closed_on_reconciliation_status_alone():
    """Verify that lineage reconciliation status alone without utility or confirmed_outcome fails closed."""
    rec = _make_sample_reconciliation(OutcomeReconciliationStatus.RECONCILED)

    with pytest.raises(OutcomeQualityValidationError, match="lineage reconciliation status alone does not imply outcome quality"):
        evaluate_outcome_quality(rec)


def test_evaluate_outcome_quality_utility_ratio():
    """Verify that utility realization ratio computes normalized quality bounded to [0.0, 1.0]."""
    rec = _make_sample_reconciliation(OutcomeReconciliationStatus.RECONCILED)
    quality = evaluate_outcome_quality(rec, actual_utility=0.8, expected_utility=1.0)

    assert isinstance(quality, OutcomeQualityContract)
    assert quality.decision_id == "dec_test_1001"
    assert quality.actual_quality == 0.8
    assert quality.quality_basis == "REALIZED_UTILITY_RATIO"
    assert len(quality.quality_digest) == 64
    assert quality.to_dict()["quality_digest"] == quality.quality_digest

    # Utility ratio exceeding 1.0 caps at 1.0
    quality_capped = evaluate_outcome_quality(rec, actual_utility=1.5, expected_utility=1.0)
    assert quality_capped.actual_quality == 1.0


def test_evaluate_outcome_quality_confirmed_outcome():
    """Verify explicit confirmed outcome boolean evaluation."""
    rec = _make_sample_reconciliation(OutcomeReconciliationStatus.OBSERVED)

    q_pass = evaluate_outcome_quality(rec, confirmed_outcome=True)
    assert q_pass.actual_quality == 1.0
    assert q_pass.quality_basis == "CONFIRMED_OUTCOME_INDICATOR"

    q_fail = evaluate_outcome_quality(rec, confirmed_outcome=False)
    assert q_fail.actual_quality == 0.0
    assert q_fail.quality_basis == "CONFIRMED_OUTCOME_INDICATOR"


def test_fail_closed_on_unresolved_and_indeterminate():
    """Verify fail-closed rejection on UNRESOLVED and INDETERMINATE reconciliations."""
    rec_unresolved = _make_sample_reconciliation(OutcomeReconciliationStatus.UNRESOLVED)
    rec_indeterminate = _make_sample_reconciliation(OutcomeReconciliationStatus.INDETERMINATE)

    with pytest.raises(OutcomeQualityValidationError, match="unresolved or indeterminate"):
        evaluate_outcome_quality(rec_unresolved)

    with pytest.raises(OutcomeQualityValidationError, match="unresolved or indeterminate"):
        evaluate_outcome_quality(rec_indeterminate)


def test_fail_closed_on_invalid_inputs():
    """Verify fail-closed validation on invalid utility inputs."""
    rec = _make_sample_reconciliation(OutcomeReconciliationStatus.RECONCILED)

    # Missing expected_utility
    with pytest.raises(OutcomeQualityValidationError, match="Both actual_utility and expected_utility"):
        evaluate_outcome_quality(rec, actual_utility=0.8)

    # Negative utility
    with pytest.raises(OutcomeQualityValidationError, match="Utility values cannot be negative"):
        evaluate_outcome_quality(rec, actual_utility=-0.5, expected_utility=1.0)

    # Boolean utility
    with pytest.raises(OutcomeQualityValidationError, match="Utility values cannot be booleans"):
        evaluate_outcome_quality(rec, actual_utility=True, expected_utility=1.0)


def test_end_to_end_metacognitive_state_transition():
    """Verify the complete behavioral chain:

    OutcomeReconciliation -> evaluate_outcome_quality() -> apply_outcome_to_metacognitive_state()
    -> MetacognitiveState.with_outcome() -> MetacognitiveEngine.assess().
    """
    rec = _make_sample_reconciliation(OutcomeReconciliationStatus.RECONCILED)

    # 1. Evaluate Outcome Quality (0.8 quality score)
    quality_contract = evaluate_outcome_quality(rec, actual_utility=0.8, expected_utility=1.0)
    assert quality_contract.actual_quality == 0.8

    # 2. Initial MetacognitiveState with decision_confidence 0.9
    initial_state = MetacognitiveState(
        knowledge_confidence=0.9,
        inference_confidence=0.85,
        decision_confidence=0.9,
        outcome_confidence=0.0,
        risk_tolerance=0.8,
        risk_score=0.2,
    )
    assert initial_state.calibration_error == 0.0
    assert initial_state.outcome_confidence == 0.0

    # 3. Apply Outcome Quality to MetacognitiveState
    updated_state = apply_outcome_to_metacognitive_state(quality_contract, initial_state)

    # Verify state transition: outcome_confidence updated to 0.8, calibration_error = |0.9 - 0.8| = 0.1
    assert updated_state.outcome_confidence == 0.8
    assert round(updated_state.calibration_error, 4) == 0.1
    assert updated_state is not initial_state  # Immutable transition

    # 4. Assess updated MetacognitiveState with MetacognitiveEngine
    engine = MetacognitiveEngine()
    assessment = engine.assess(updated_state)

    assert assessment.state.outcome_confidence == 0.8
    assert assessment.action_allowed is True
    assert assessment.review_required is False
