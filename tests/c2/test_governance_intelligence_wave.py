"""Tests for Wave B Governance Intelligence & Adversarial Proof Attack Substrate."""
import pytest
from sage.c2.governance_intelligence import (
    AdversarialRegressionSuite,
    AntiDriftVerificationEngine,
    AttackVectorType,
    GovernanceProofAttackAuditor,
    GovernanceProvenanceValidator,
)

EXACT_HEAD_SHA = "bf2560ede2899adfe73fe2e2cfb4accd0b8885e2"


def test_stale_evidence_sha_rejection():
    auditor = GovernanceProofAttackAuditor()

    # Legacy stale 39411847 SHA must be rejected as proof for current head
    res = auditor.audit_stale_evidence_attack("39411847", EXACT_HEAD_SHA)
    assert res.neutralized is True
    assert res.vector_type == AttackVectorType.STALE_EVIDENCE_REUSE

    # Mismatched SHA must also be rejected
    assert auditor.verify_evidence_sha("1111111111111111111111111111111111111111", EXACT_HEAD_SHA) is False

    # Exact matching active HEAD SHA is accepted
    assert auditor.verify_evidence_sha(EXACT_HEAD_SHA, EXACT_HEAD_SHA) is True


def test_station_identity_provenance_validation():
    validator = GovernanceProvenanceValidator()

    # Canonical station tags
    assert validator.validate_station_tag("[SAGE::C2::CHATGPT]") is True
    assert validator.validate_station_tag("[SAGE::ENGINEER::JULES]") is True
    assert validator.validate_station_tag("[SAGE::INTEL::GEMINI]") is True
    assert validator.validate_station_tag("[SAGE::DIRECTOR]") is True

    # Malformed / spoofed station tags
    assert validator.validate_station_tag("[C2::GPT]") is False
    assert validator.validate_station_tag("[CHATGPT]") is False
    assert validator.validate_station_tag("[SAGE::UNAUTHORIZED]") is False

    res = validator.audit_station_spoof_attack("[C2::GPT]")
    assert res.neutralized is True
    assert res.vector_type == AttackVectorType.STATION_IDENTITY_SPOOF


def test_anti_drift_repo_truth_reconciliation():
    engine = AntiDriftVerificationEngine()

    assert engine.reconcile_repo_truth(EXACT_HEAD_SHA, EXACT_HEAD_SHA) is True
    assert engine.reconcile_repo_truth(EXACT_HEAD_SHA, "b" * 40) is False
    assert engine.reconcile_repo_truth("invalid_sha", EXACT_HEAD_SHA) is False


def test_adversarial_regression_suite_execution():
    suite = AdversarialRegressionSuite()
    receipt = suite.execute_governance_intelligence_wave(
        wave_id="wave_gov_test",
        exact_git_head=EXACT_HEAD_SHA,
    )

    assert receipt.exact_git_head == EXACT_HEAD_SHA
    assert receipt.total_attack_vectors_tested >= 5
    assert receipt.attack_vectors_neutralized == receipt.total_attack_vectors_tested
    assert receipt.anti_drift_reconciled is True
    assert receipt.identity_provenance_verified is True
    assert receipt.fail_closed_verdict == "PASS"
    assert receipt.receipt_hash == receipt.compute_hash()
