"""Unit tests for Flight B: Reality Gate & Source Receipt Verification."""

import time
from sage.c2.reality_gate import (
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
