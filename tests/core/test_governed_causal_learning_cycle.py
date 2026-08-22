from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sage.core.effect_observation import EffectObservation, TransitionOutcome
from sage.core.governed_causal_learning_cycle import (
    GovernedCausalLearningCycle,
    GovernedCausalLearningCycleValidationError,
    GovernedCausalLearningCycleVerdict,
)
from sage.core.governed_learning_candidate import GovernedLearningCandidate
from sage.core.outcome_reconciliation import (
    OutcomeReconciliation,
    OutcomeReconciliationStatus,
)


def make_inputs(
    *,
    reconciliation_status: OutcomeReconciliationStatus = (
        OutcomeReconciliationStatus.RECONCILED
    ),
    outcome: TransitionOutcome = TransitionOutcome.CONFIRMED,
    observed_state_hash: str | None = "expected-hash",
):
    reconciliation = OutcomeReconciliation.reconcile(
        decision_id="decision-1",
        context_id="context-1",
        t0_claim_ref="claim-1",
        t1_observation_ref="observation-ref-1",
        reality_gap_assessment_ref="assessment-1",
        outcome_ref="execution-1",
        status=reconciliation_status,
        rationale="bounded causal review",
    )
    observation = EffectObservation.observe(
        execution_id="execution-1",
        target_boundary_id="capability-state:agent-1",
        expected_state_hash="expected-hash",
        observed_state_hash=observed_state_hash,
        outcome=outcome,
        observed_at="2026-08-22T03:30:00+00:00",
        telemetry_source="independent-probe-1",
    )
    candidate = GovernedLearningCandidate.propose(
        candidate_id="candidate-1",
        outcome_reconciliation_digest=reconciliation.reconciliation_digest,
        reality_gap_assessment_ref="assessment-1",
        scope="calibration-model-X",
        hypothesis="Repeated contradictions may justify recalibration of X.",
        proposed_change="Evaluate whether X should be adjusted.",
        evidence_refs=(observation.observation_id, "assessment-1"),
    )
    return reconciliation, observation, candidate


def test_confirmed_reconciled_cycle_is_ready_for_review():
    reconciliation, observation, candidate = make_inputs()

    cycle = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )

    assert cycle.verdict is GovernedCausalLearningCycleVerdict.READY_FOR_REVIEW
    assert cycle.authority_granted is False
    assert cycle.reviewer_authorization_required is True


def test_unknown_effect_forces_hold():
    reconciliation, observation, candidate = make_inputs(
        outcome=TransitionOutcome.UNKNOWN,
        observed_state_hash=None,
    )

    cycle = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )

    assert cycle.verdict is GovernedCausalLearningCycleVerdict.HOLD


def test_unresolved_reconciliation_forces_hold():
    reconciliation, observation, candidate = make_inputs(
        reconciliation_status=OutcomeReconciliationStatus.UNRESOLVED
    )

    cycle = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )

    assert cycle.verdict is GovernedCausalLearningCycleVerdict.HOLD


def test_failed_effect_forces_hold():
    reconciliation, observation, candidate = make_inputs(
        outcome=TransitionOutcome.FAILED,
        observed_state_hash="failed-state",
    )

    cycle = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )

    assert cycle.verdict is GovernedCausalLearningCycleVerdict.HOLD


def test_lineage_substitution_fails_closed():
    reconciliation, observation, candidate = make_inputs()
    tampered = GovernedLearningCandidate.propose(
        candidate_id="candidate-2",
        outcome_reconciliation_digest="wrong-reconciliation",
        reality_gap_assessment_ref="assessment-1",
        scope="calibration-model-X",
        hypothesis="hypothesis",
        proposed_change="proposal",
        evidence_refs=(observation.observation_id,),
    )

    with pytest.raises(GovernedCausalLearningCycleValidationError):
        GovernedCausalLearningCycle.compose(
            reconciliation=reconciliation,
            observation=observation,
            candidate=tampered,
        )


def test_observation_lineage_substitution_fails_closed():
    reconciliation, observation, candidate = make_inputs()
    wrong_observation = EffectObservation.observe(
        execution_id="wrong-execution",
        target_boundary_id="capability-state:agent-1",
        expected_state_hash="expected-hash",
        observed_state_hash="expected-hash",
        outcome=TransitionOutcome.CONFIRMED,
        observed_at="2026-08-22T03:30:00+00:00",
        telemetry_source="independent-probe-2",
    )

    with pytest.raises(GovernedCausalLearningCycleValidationError):
        GovernedCausalLearningCycle.compose(
            reconciliation=reconciliation,
            observation=wrong_observation,
            candidate=candidate,
        )


def test_missing_observation_evidence_fails_closed():
    reconciliation, observation, _ = make_inputs()
    candidate = GovernedLearningCandidate.propose(
        candidate_id="candidate-3",
        outcome_reconciliation_digest=reconciliation.reconciliation_digest,
        reality_gap_assessment_ref="assessment-1",
        scope="calibration-model-X",
        hypothesis="hypothesis",
        proposed_change="proposal",
        evidence_refs=("other-evidence",),
    )

    with pytest.raises(GovernedCausalLearningCycleValidationError):
        GovernedCausalLearningCycle.compose(
            reconciliation=reconciliation,
            observation=observation,
            candidate=candidate,
        )


def test_cycle_digest_is_deterministic_and_immutable():
    reconciliation, observation, candidate = make_inputs()
    first = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )
    second = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    )

    assert first.cycle_digest == second.cycle_digest
    assert len(first.cycle_digest) == 64
    with pytest.raises(FrozenInstanceError):
        first.verdict = GovernedCausalLearningCycleVerdict.HOLD


def test_public_projection_has_no_execution_or_promotion_controls():
    reconciliation, observation, candidate = make_inputs()
    projection = GovernedCausalLearningCycle.compose(
        reconciliation=reconciliation,
        observation=observation,
        candidate=candidate,
    ).to_dict()

    assert projection["authority_granted"] is False
    assert projection["reviewer_authorization_required"] is True
    assert "apply" not in projection
    assert "promote" not in projection
    assert "retry" not in projection
