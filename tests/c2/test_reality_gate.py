"""Unit tests for Flight B: Reality Gate & Source Receipt Verification."""

import time

from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt


def _receipt(resource_id: str, digest: str, source_type: str = "github", **metadata) -> SourceReceipt:
    return SourceReceipt(
        source_type=source_type,
        resource_id=resource_id,
        sha256_digest=digest,
        timestamp_utc=time.time(),
        metadata={"origin": "operation_boundary", "operation": "github_observation", **metadata},
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
    eval_res = RealityGate.evaluate_claims(claims, [])

    assert eval_res.is_permitted is False
    assert len(eval_res.permitted_claims) == 1
    assert eval_res.permitted_claims[0].claim_id == "c1"
    assert len(eval_res.blocked_claims) == 1
    assert eval_res.blocked_claims[0].claim_id == "c2"
    assert any("explicit target resource/fingerprint" in v for v in eval_res.violations)


def test_reality_gate_blocks_generic_source_claim_without_resource():
    claim = OperationalClaim("c1", "GitHub repo is completely clean.", "github")
    receipt = _receipt(
        "commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        "70d1e798d5deee425a138e12ec070c8b10af2793",
    )

    eval_res = RealityGate.evaluate_claims([claim], [receipt])

    assert eval_res.is_permitted is False
    assert len(eval_res.blocked_claims) == 1
    assert any("explicit target resource/fingerprint" in v for v in eval_res.violations)


def test_reality_gate_permits_exact_resource_and_fingerprint():
    resource = "commit:70d1e798d5deee425a138e12ec070c8b10af2793"
    claim = OperationalClaim("c1", "GitHub currently reports main at 70d1e7.", "github", resource)
    receipt = _receipt(resource, "70d1e798d5deee425a138e12ec070c8b10af2793")

    eval_res = RealityGate.evaluate_claims([claim], [receipt])

    assert eval_res.is_permitted is True
    assert len(eval_res.permitted_claims) == 1
    assert len(eval_res.blocked_claims) == 0


def test_reality_gate_blocks_exact_resource_with_wrong_fingerprint():
    claim = OperationalClaim("c1", "GitHub currently reports main at abc.", "github", "commit:abc")
    receipt = _receipt("commit:abc", "def")

    eval_res = RealityGate.evaluate_claims([claim], [receipt])

    assert eval_res.is_permitted is False
    assert len(eval_res.blocked_claims) == 1
    assert any("fingerprint mismatch" in v for v in eval_res.violations)


def test_reality_gate_blocks_receipt_not_created_by_operation_boundary():
    claim = OperationalClaim("c1", "GitHub currently reports main at abc.", "github", "commit:abc")
    receipt = SourceReceipt("github", "commit:abc", "abc", time.time(), metadata={})

    eval_res = RealityGate.evaluate_claims([claim], [receipt])

    assert eval_res.is_permitted is False
    assert any("operation boundary" in v for v in eval_res.violations)
