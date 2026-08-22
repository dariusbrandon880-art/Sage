import pytest

from sage.experimental.execution_claim_guard import ClaimEvidence, ClaimState, allowed_claim_state, assert_claim_state


def test_no_artifact_means_planned():
    assert allowed_claim_state(ClaimEvidence()) is ClaimState.PLANNED


def test_execution_requires_artifact_and_tests():
    evidence = ClaimEvidence(artifact_present=True, test_evidence_present=True)
    assert allowed_claim_state(evidence) is ClaimState.EXECUTED


def test_verification_requires_observation_and_independent_check():
    evidence = ClaimEvidence(True, True, True, True, False)
    assert allowed_claim_state(evidence) is ClaimState.VERIFIED


def test_completion_requires_receipt():
    evidence = ClaimEvidence(True, True, True, True, True)
    assert allowed_claim_state(evidence) is ClaimState.COMPLETE


def test_overclaim_is_rejected():
    with pytest.raises(ValueError):
        assert_claim_state(ClaimEvidence(artifact_present=True, test_evidence_present=True), ClaimState.VERIFIED)
