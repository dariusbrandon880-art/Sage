import pytest

from sage.core.evidence_sufficiency import (
    EvidenceAssessment,
    EvidenceSufficiencyEvaluation,
    EvidenceSufficiencyValidationError,
    SufficiencyStatus,
)


def assessment(ref="e1", **overrides):
    values = {"evidence_ref": ref, "supports": True}
    values.update(overrides)
    return EvidenceAssessment(**values)


def test_supported_is_context_and_intent_bound_and_deterministic():
    a = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx-a",
        intent_ref="intent-live",
        assessments=[assessment("e2", relevance=1.0, coverage=1.0), assessment("e1")],
    )
    b = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx-a",
        intent_ref="intent-live",
        assessments=[assessment("e1"), assessment("e2", relevance=1.0, coverage=1.0)],
    )
    assert a.status is SufficiencyStatus.SUPPORTED
    assert a.evaluation_digest == b.evaluation_digest


def test_context_or_intent_transposition_changes_digest():
    a = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1", context_id="simulation", intent_ref="benchmark", assessments=[assessment()]
    )
    b = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1", context_id="live", intent_ref="execution", assessments=[assessment()]
    )
    assert a.status is SufficiencyStatus.SUPPORTED
    assert b.status is SufficiencyStatus.SUPPORTED
    assert a.evaluation_digest != b.evaluation_digest


def test_partial_support_is_not_promoted_to_supported():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx",
        intent_ref="intent",
        assessments=[assessment(coverage=0.4)],
        minimum_coverage=0.8,
    )
    assert result.status is SufficiencyStatus.PARTIALLY_SUPPORTED


def test_contradiction_dominates_support():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx",
        intent_ref="intent",
        assessments=[assessment("support"), assessment("contra", supports=False, contradicts=True)],
    )
    assert result.status is SufficiencyStatus.CONTRADICTED


def test_independence_requirement_cannot_be_satisfied_by_self_attested_evidence():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx",
        intent_ref="intent",
        assessments=[assessment(coverage=1.0, independently_verified=False)],
        require_independent_witness=True,
    )
    assert result.status is SufficiencyStatus.PARTIALLY_SUPPORTED


def test_independent_witness_can_satisfy_full_burden():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx",
        intent_ref="intent",
        assessments=[assessment(coverage=1.0, independently_verified=True)],
        require_independent_witness=True,
    )
    assert result.status is SufficiencyStatus.SUPPORTED


def test_no_support_is_unverifiable():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1",
        context_id="ctx",
        intent_ref="intent",
        assessments=[assessment(supports=False)],
    )
    assert result.status is SufficiencyStatus.UNVERIFIABLE


def test_empty_assessments_fail_closed():
    with pytest.raises(EvidenceSufficiencyValidationError):
        EvidenceSufficiencyEvaluation.evaluate(
            claim_ref="claim-1", context_id="ctx", intent_ref="intent", assessments=[]
        )


def test_authority_firewall_is_permanent():
    result = EvidenceSufficiencyEvaluation.evaluate(
        claim_ref="claim-1", context_id="ctx", intent_ref="intent", assessments=[assessment()]
    )
    assert result.authority_granted is False
    assert result.to_dict()["authority_granted"] is False


def test_invalid_evidence_metrics_fail_closed():
    with pytest.raises(EvidenceSufficiencyValidationError):
        assessment(coverage=1.1)
