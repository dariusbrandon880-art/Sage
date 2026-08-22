import pytest

from sage.core.governed_learning_candidate import (
    GovernedLearningCandidate,
    GovernedLearningCandidateStatus,
    GovernedLearningCandidateValidationError,
)


def make_candidate(**overrides):
    values = {
        "candidate_id": "candidate-001",
        "outcome_reconciliation_digest": "reconciliation-sha-001",
        "reality_gap_assessment_ref": "assessment-sha-001",
        "scope": "calibration-model-X",
        "hypothesis": "Repeated contradictions may justify recalibration of X.",
        "proposed_change": "Evaluate whether the calibration weight for X should decrease.",
        "evidence_refs": ("observation-sha-001", "assessment-sha-001"),
    }
    values.update(overrides)
    return GovernedLearningCandidate.propose(**values)


def test_candidate_is_proposed_and_non_authoritative():
    candidate = make_candidate()
    assert candidate.status is GovernedLearningCandidateStatus.CANDIDATE_PROPOSED
    assert candidate.authority_granted is False


def test_candidate_digest_is_deterministic():
    assert make_candidate().candidate_digest == make_candidate().candidate_digest


@pytest.mark.parametrize(
    "field",
    [
        "candidate_id",
        "outcome_reconciliation_digest",
        "reality_gap_assessment_ref",
        "scope",
        "hypothesis",
        "proposed_change",
    ],
)
def test_required_fields_fail_closed(field):
    with pytest.raises(GovernedLearningCandidateValidationError):
        make_candidate(**{field: ""})


def test_empty_evidence_fails_closed():
    with pytest.raises(GovernedLearningCandidateValidationError):
        make_candidate(evidence_refs=())


def test_blank_evidence_reference_fails_closed():
    with pytest.raises(GovernedLearningCandidateValidationError):
        make_candidate(evidence_refs=("",))


@pytest.mark.parametrize("field", [
    "outcome_reconciliation_digest",
    "reality_gap_assessment_ref",
    "hypothesis",
    "proposed_change",
    "scope",
])
def test_consequential_substitution_changes_digest(field):
    base = make_candidate().candidate_digest
    changed = make_candidate(**{field: "substituted-value"}).candidate_digest
    assert changed != base


def test_evidence_substitution_changes_digest():
    assert make_candidate().candidate_digest != make_candidate(
        evidence_refs=("different-evidence",)
    ).candidate_digest


def test_candidate_is_immutable():
    candidate = make_candidate()
    with pytest.raises((AttributeError, TypeError)):
        candidate.hypothesis = "mutated"


def test_authority_cannot_be_enabled():
    candidate = make_candidate()
    with pytest.raises((AttributeError, TypeError)):
        candidate.authority_granted = True
    assert candidate.authority_granted is False


def test_public_projection_is_complete_and_non_authoritative():
    projection = make_candidate().to_dict()
    assert projection["status"] == "CANDIDATE_PROPOSED"
    assert projection["candidate_digest"]
    assert projection["authority_granted"] is False
    assert projection["evidence_refs"] == ["observation-sha-001", "assessment-sha-001"]


def test_proposed_change_is_descriptive_text_not_an_execution_api():
    candidate = make_candidate(proposed_change="Evaluate whether X should be adjusted.")
    assert isinstance(candidate.proposed_change, str)
    assert not hasattr(candidate, "apply")
    assert not hasattr(candidate, "promote")


def test_no_additional_lifecycle_status_is_accepted():
    with pytest.raises(TypeError):
        GovernedLearningCandidate(
            candidate_id="candidate-001",
            outcome_reconciliation_digest="reconciliation-sha-001",
            reality_gap_assessment_ref="assessment-sha-001",
            scope="scope",
            hypothesis="hypothesis",
            proposed_change="proposal",
            evidence_refs=("evidence",),
            status=GovernedLearningCandidateStatus.CANDIDATE_PROPOSED,
        )
