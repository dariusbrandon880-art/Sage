"""Tests for Wave B Governance Intelligence & Adversarial Proof Attack Substrate."""
import subprocess

from sage.c2.governance_intelligence import (
    AdversarialRegressionSuite,
    AntiDriftVerificationEngine,
    AttackVectorType,
    GovernanceProofAttackAuditor,
    GovernanceProvenanceValidator,
)


def current_git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_stale_evidence_sha_rejection():
    auditor = GovernanceProofAttackAuditor()
    exact_head_sha = current_git_head()
    res = auditor.audit_stale_evidence_attack("39411847", exact_head_sha)
    assert res.neutralized is True
    assert res.vector_type == AttackVectorType.STALE_EVIDENCE_REUSE
    assert auditor.verify_evidence_sha("1111111111111111111111111111111111111111", exact_head_sha) is False
    assert auditor.verify_evidence_sha(exact_head_sha, exact_head_sha) is True


def test_station_identity_provenance_validation():
    validator = GovernanceProvenanceValidator()
    assert validator.validate_station_tag("[SAGE::C2::CHATGPT]") is True
    assert validator.validate_station_tag("[SAGE::ENGINEER::JULES]") is True
    assert validator.validate_station_tag("[SAGE::INTEL::GEMINI]") is True
    assert validator.validate_station_tag("[SAGE::DIRECTOR]") is True
    assert validator.validate_station_tag("[C2::GPT]") is False
    assert validator.validate_station_tag("[CHATGPT]") is False
    assert validator.validate_station_tag("[SAGE::UNAUTHORIZED]") is False
    res = validator.audit_station_spoof_attack("[C2::GPT]")
    assert res.neutralized is True
    assert res.vector_type == AttackVectorType.STATION_IDENTITY_SPOOF


def test_anti_drift_repo_truth_reconciliation():
    engine = AntiDriftVerificationEngine()
    exact_head_sha = current_git_head()
    assert engine.reconcile_repo_truth(exact_head_sha, exact_head_sha) is True
    assert engine.reconcile_repo_truth(exact_head_sha, "b" * 40) is False
    assert engine.reconcile_repo_truth("invalid_sha", exact_head_sha) is False


def test_adversarial_regression_suite_execution():
    suite = AdversarialRegressionSuite()
    exact_head_sha = current_git_head()
    receipt = suite.execute_governance_intelligence_wave(wave_id="wave_gov_test", exact_git_head=exact_head_sha)
    assert receipt.exact_git_head == exact_head_sha
    assert receipt.total_attack_vectors_tested >= 5
    assert receipt.attack_vectors_neutralized == receipt.total_attack_vectors_tested
    assert receipt.anti_drift_reconciled is True
    assert receipt.identity_provenance_verified is True
    assert receipt.fail_closed_verdict == "PASS"
    assert receipt.receipt_hash == receipt.compute_hash()
