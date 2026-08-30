from dataclasses import FrozenInstanceError

import pytest

from sage.core.technique_learning import (
    TechniqueCandidate,
    TechniqueLearningValidationError,
    TechniqueValidation,
    TechniqueValidationVerdict,
)


def candidate() -> TechniqueCandidate:
    return TechniqueCandidate(
        technique_id="technique-c2-marathon-001",
        mission_class="governed-repository-repair",
        preconditions=("authorized-directive", "reality-lock"),
        execution_technique="full-frame then compound independent repairs before closure",
        expected_mechanism="less idle time and fewer planning-loop stops",
        observed_result="independent work advanced while blocked branch remained gated",
        evidence_refs=("receipt-1", "receipt-2"),
        failure_modes=("overreach", "stale-state-claim"),
        cost_risk_notes="requires exact-head reconciliation before closure",
    )


def test_candidate_is_immutable_and_digest_is_deterministic():
    first = candidate()
    second = candidate()
    assert first.technique_digest == second.technique_digest
    assert len(first.technique_digest) == 64
    with pytest.raises(FrozenInstanceError):
        first.observed_result = "tampered"


def test_candidate_requires_evidence():
    with pytest.raises(TechniqueLearningValidationError, match="evidence_refs"):
        TechniqueCandidate(
            technique_id="t",
            mission_class="m",
            preconditions=(),
            execution_technique="e",
            expected_mechanism="x",
            observed_result="o",
            evidence_refs=(),
            failure_modes=(),
            cost_risk_notes="c",
        )


def test_positive_replicated_technique_is_ready_for_review_only():
    validation = TechniqueValidation(
        technique_digest=candidate().technique_digest,
        metric_definition="verified outcomes per campaign hour; higher is better",
        baseline_score=0.50,
        technique_score=0.75,
        replication_count=4,
        independent_evidence_refs=("obs-a", "obs-b"),
    )
    assert validation.verdict is TechniqueValidationVerdict.READY_FOR_REVIEW
    assert validation.delta == pytest.approx(0.25)
    assert validation.authority_granted is False
    assert validation.reviewer_authorization_required is True


def test_counterexample_forces_hold_even_with_positive_delta():
    validation = TechniqueValidation(
        technique_digest=candidate().technique_digest,
        metric_definition="higher is better",
        baseline_score=1.0,
        technique_score=2.0,
        replication_count=5,
        independent_evidence_refs=("obs-a", "obs-b"),
        counterexample_count=1,
    )
    assert validation.verdict is TechniqueValidationVerdict.HOLD


def test_insufficient_replication_fails_closed():
    with pytest.raises(TechniqueLearningValidationError, match="replication_count"):
        TechniqueValidation(
            technique_digest=candidate().technique_digest,
            metric_definition="higher is better",
            baseline_score=1.0,
            technique_score=2.0,
            replication_count=1,
            independent_evidence_refs=("obs-a",),
        )


def test_non_improvement_holds():
    validation = TechniqueValidation(
        technique_digest=candidate().technique_digest,
        metric_definition="higher is better",
        baseline_score=2.0,
        technique_score=2.0,
        replication_count=3,
        independent_evidence_refs=("obs-a", "obs-b"),
    )
    assert validation.verdict is TechniqueValidationVerdict.HOLD


def test_validation_digest_is_stable_and_projection_has_no_promotion_control():
    validation = TechniqueValidation(
        technique_digest=candidate().technique_digest,
        metric_definition="higher is better",
        baseline_score=2.0,
        technique_score=3.0,
        replication_count=3,
        independent_evidence_refs=("obs-a", "obs-b"),
    )
    projection = validation.to_dict()
    assert len(validation.validation_digest) == 64
    assert projection["authority_granted"] is False
    assert projection["reviewer_authorization_required"] is True
    assert "promote" not in projection
    assert "apply" not in projection
