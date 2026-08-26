"""Adversarial tests for governed promotion and atomic CAS semantics."""

import time

import pytest

from sage.c2.tree.promotion_engine import (
    EvidenceReceipt,
    PromotionCandidate,
    PromotionEngine,
    PromotionStatus,
    TargetDriftError,
)


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


class MockCASGitProvider:
    def __init__(self, current_head: str, descendants=None):
        self.current_head = current_head
        self.descendants = set(descendants or [])
        self.is_clean = True

    def integrate_cas(self, source_sha, expected_target_sha, target_branch):
        if self.current_head != expected_target_sha:
            raise TargetDriftError(
                f"expected {expected_target_sha}, got {self.current_head}"
            )
        if source_sha not in self.descendants:
            raise ValueError("source is not a descendant of expected target")
        self.current_head = source_sha
        return source_sha

    def verify_clean_status(self):
        return self.is_clean


def receipt(stage, sha=SHA_B, passed=True, receipt_id=None):
    return EvidenceReceipt(
        receipt_id or f"receipt-{stage}",
        "flight-1",
        stage,
        sha,
        passed,
        time.time(),
    )


def candidate(
    *receipts, source=SHA_B, target=SHA_A, gates=None, branch="feature/promotion"
):
    return PromotionCandidate(
        branch,
        source,
        target,
        list(gates or ["tests"]),
        list(receipts),
    )


def test_promotion_records_exact_gate_receipt():
    provider = MockCASGitProvider(SHA_A, descendants=[SHA_B])
    engine = PromotionEngine(provider)
    result = engine.execute_promotion(candidate(receipt("tests")))

    assert result["new_main_sha"] == SHA_B
    assert result["previous_main_sha"] == SHA_A
    assert result["verified_gates"]["tests"]["receipt_id"] == "receipt-tests"
    assert result["verified_gates"]["tests"]["commit_sha"] == SHA_B


def test_duplicate_evidence_stage_rejects_deterministically():
    engine = PromotionEngine(MockCASGitProvider(SHA_A, descendants=[SHA_B]))
    item = candidate(receipt("tests"), receipt("tests", receipt_id="receipt-tests-2"))

    assert engine.verify_candidate(item) == {}
    assert item.status == PromotionStatus.REJECTED


def test_failed_duplicate_evidence_stage_also_rejects():
    engine = PromotionEngine(MockCASGitProvider(SHA_A, descendants=[SHA_B]))
    item = candidate(
        receipt("tests", passed=False),
        receipt("tests", passed=True, receipt_id="receipt-tests-2"),
    )

    assert engine.verify_candidate(item) == {}
    assert item.status == PromotionStatus.REJECTED


def test_unbound_receipt_cannot_satisfy_gate():
    engine = PromotionEngine(MockCASGitProvider(SHA_A, descendants=[SHA_B]))
    item = candidate(receipt("tests", sha=SHA_C))

    assert engine.verify_candidate(item) == {}
    assert item.status == PromotionStatus.REJECTED


def test_required_gate_list_must_be_unique():
    engine = PromotionEngine(MockCASGitProvider(SHA_A, descendants=[SHA_B]))
    item = candidate(receipt("tests"), gates=["tests", "tests"])

    assert engine.verify_candidate(item) == {}
    assert item.status == PromotionStatus.REJECTED


def test_non_descendant_source_is_fail_closed():
    provider = MockCASGitProvider(SHA_A, descendants=[])
    engine = PromotionEngine(provider)

    with pytest.raises(RuntimeError, match="Git integration execution failed"):
        engine.execute_promotion(candidate(receipt("tests")))
    assert provider.current_head == SHA_A


def test_second_cas_attempt_fails_closed_without_mutating_main():
    provider = MockCASGitProvider(SHA_A, descendants=[SHA_B, SHA_C])
    engine = PromotionEngine(provider)
    first = candidate(receipt("tests", sha=SHA_B), source=SHA_B)
    second = candidate(receipt("tests", sha=SHA_C), source=SHA_C)

    engine.execute_promotion(first)
    with pytest.raises(TargetDriftError):
        engine.execute_promotion(second)

    assert second.status == PromotionStatus.REJECTED
    assert provider.current_head == SHA_B


def test_dirty_workspace_fails_after_integration():
    provider = MockCASGitProvider(SHA_A, descendants=[SHA_B])
    provider.is_clean = False
    engine = PromotionEngine(provider)

    with pytest.raises(RuntimeError, match="workspace is dirty"):
        engine.execute_promotion(candidate(receipt("tests")))
    assert provider.current_head == SHA_B


def test_invalid_branch_and_sha_are_rejected():
    engine = PromotionEngine(MockCASGitProvider(SHA_A, descendants=[SHA_B]))
    bad_sha = candidate(receipt("tests"), source="not-a-sha")
    bad_branch = candidate(receipt("tests"), branch="main")

    assert engine.verify_candidate(bad_sha) == {}
    assert bad_sha.status == PromotionStatus.REJECTED
    assert engine.verify_candidate(bad_branch) == {}
    assert bad_branch.status == PromotionStatus.REJECTED
