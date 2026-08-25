"""Unit tests for Flight B: Reality Gate & Source Receipt Verification."""

import time
from sage.c2.live_operation_receipt import LiveOperationReceipt, execute_live_capability
from sage.c2.reality_gate import (
    OperationalClaim,
    RealityGate,
    SourceReceipt,
)


class DummyCap:
    capability_id = "pr_merge"

    def __init__(self, success: bool = True):
        self._success = success

    def invoke(self, *, operation: str, task: str):
        return {
            "target_resource": "pr:250",
            "success": self._success,
            "result": {"status": "ok"},
        }


def test_is_live_state_claim_detection():
    assert RealityGate.is_live_state_claim("GitHub currently reports main at 70d1e7.") is True
    assert RealityGate.is_live_state_claim("The repo is clean.") is True
    assert RealityGate.is_live_state_claim("We should consider adding directive fidelity.") is False


def test_reality_gate_blocks_unreceipted_live_claim():
    claims = [
        OperationalClaim(claim_id="c1", statement="We will build a reality gate."),
        OperationalClaim(claim_id="c2", statement="The repo is clean."),
    ]
    receipts = []  # No receipts available

    eval_res = RealityGate.evaluate_claims(claims, receipts)
    assert eval_res.is_permitted is False
    assert len(eval_res.permitted_claims) == 1
    assert eval_res.permitted_claims[0].claim_id == "c1"
    assert len(eval_res.blocked_claims) == 1
    assert eval_res.blocked_claims[0].claim_id == "c2"
    assert any("missing explicit target resource/fingerprint receipt match" in v for v in eval_res.violations)


def test_reality_gate_blocks_generic_source_claim_without_resource():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub repo is completely clean.",
            required_source_type="github",
            # target_resource missing!
        )
    ]
    receipts = [
        SourceReceipt(
            source_type="github",
            resource_id="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
            sha256_digest="70d1e798d5deee425a138e12ec070c8b10af2793",
            timestamp_utc=time.time(),
        )
    ]

    eval_res = RealityGate.evaluate_claims(claims, receipts)
    assert eval_res.is_permitted is False
    assert len(eval_res.blocked_claims) == 1
    assert any("missing explicit target resource/fingerprint receipt match" in v for v in eval_res.violations)


def test_reality_gate_permits_exact_resource_receipted_live_claim():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub currently reports main at 70d1e7.",
            required_source_type="github",
            target_resource="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        )
    ]
    receipts = [
        SourceReceipt(
            source_type="github",
            resource_id="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
            sha256_digest="70d1e798d5deee425a138e12ec070c8b10af2793",
            timestamp_utc=time.time(),
        )
    ]

    eval_res = RealityGate.evaluate_claims(claims, receipts)
    assert eval_res.is_permitted is True
    assert len(eval_res.permitted_claims) == 1
    assert len(eval_res.blocked_claims) == 0


def test_reality_gate_adversarial_matrix_checks():
    claims = [
        OperationalClaim(
            claim_id="c1",
            statement="GitHub repo is merged.",
            required_source_type="pr_merge",
            target_resource="pr:250",
            required_capability="pr_merge",
        )
    ]

    # 1. Failed operation -> BLOCKED
    failed_receipt = LiveOperationReceipt(
        operation="pr_merge",
        capability="pr_merge",
        target_resource="pr:250",
        timestamp=str(time.time()),
        success=False,
        result_digest="a" * 64,
        receipt_hash="b" * 64,
        source_id="sage-c2-operation-boundary",
        source_signature="invalid",
    )
    res_failed = RealityGate.evaluate_claims(claims, [failed_receipt])
    assert res_failed.is_permitted is False

    # 2. Fake hash -> BLOCKED
    bad_hash_receipt = LiveOperationReceipt(
        operation="pr_merge",
        capability="pr_merge",
        target_resource="pr:250",
        timestamp=str(time.time()),
        success=True,
        result_digest="a" * 64,
        receipt_hash="fake_hash_12345",
        source_id="sage-c2-operation-boundary",
        source_signature="fake_sig",
    )
    res_bad_hash = RealityGate.evaluate_claims(claims, [bad_hash_receipt])
    assert res_bad_hash.is_permitted is False

    # 3. Wrong execution identity -> BLOCKED
    valid_receipt = execute_live_capability(DummyCap(), operation="pr_merge", task="merge")
    res_wrong_id = RealityGate.evaluate_claims(claims, [valid_receipt], active_execution_identity="other_station")
    assert res_wrong_id.is_permitted is False
