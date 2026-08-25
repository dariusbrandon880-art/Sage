"""Unit tests for Flight B: Reality Gate & Source Receipt Verification."""

import time
from sage.c2.reality_gate import (
    LiveOperationReceipt,
    OperationalClaim,
    RealityGate,
    SourceReceipt,
)


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
            required_source_type="github",
            target_resource="pr:250",
            required_capability="pr_merge",
        )
    ]

    # 1. Failed operation -> BLOCKED
    failed_receipt = LiveOperationReceipt.create(
        operation_id="op-01",
        capability="pr_merge",
        target_resource="pr:250",
        source="github",
        success=False,  # Failed!
        result_digest="digest123",
        execution_identity="canonical_station",
    )
    res_failed = RealityGate.evaluate_claims(claims, [failed_receipt])
    assert res_failed.is_permitted is False

    # 2. Fake hash -> BLOCKED
    bad_hash_receipt = LiveOperationReceipt(
        operation_id="op-02",
        capability="pr_merge",
        target_resource="pr:250",
        source="github",
        timestamp=time.time(),
        success=True,
        result_digest="digest123",
        execution_identity="canonical_station",
        receipt_hash="fake_hash_12345",
    )
    res_bad_hash = RealityGate.evaluate_claims(claims, [bad_hash_receipt])
    assert res_bad_hash.is_permitted is False

    # 3. Wrong execution identity -> BLOCKED
    res_wrong_id = RealityGate.evaluate_claims(claims, [failed_receipt], active_execution_identity="other_station")
    assert res_wrong_id.is_permitted is False
