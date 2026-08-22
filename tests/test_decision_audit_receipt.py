"""Adversarial tests for DecisionAuditReceipt v0.1."""

import json

import pytest

from sage.decision_audit_receipt import AuditCheck, DecisionAuditReceipt


SHA = "a" * 64


def make_receipt(**overrides):
    values = {
        "decision_id": "decision-001",
        "decision_hash": SHA,
        "context_id": "ctx-001",
        "authority_ref": "c2-level-1",
        "evidence_refs": ["receipt:002", "receipt:001"],
        "checks": [
            AuditCheck("decision_integrity", "PASS", "Decision hash verified"),
            AuditCheck("evidence_binding", "PASS", "All required evidence references present"),
        ],
        "resolution_status": "VERIFIED",
    }
    values.update(overrides)
    return DecisionAuditReceipt(**values)


def test_deterministic_ordering_and_replay():
    first = make_receipt()
    second = make_receipt(evidence_refs=["receipt:001", "receipt:002"])
    assert first.serialize() == second.serialize()
    assert first.replay().serialize() == first.serialize()
    assert first.replay().receipt_hash == first.receipt_hash


def test_missing_refs_and_checks_fail_closed():
    with pytest.raises(ValueError, match="at least one evidence_ref"):
        make_receipt(evidence_refs=[])
    with pytest.raises(ValueError, match="at least one audit check"):
        make_receipt(checks=[])


def test_duplicate_checks_fail_closed():
    check = AuditCheck("integrity", "PASS", "ok")
    with pytest.raises(ValueError, match="duplicate check_id"):
        make_receipt(checks=[check, check])


def test_status_fails_closed_on_failed_check():
    receipt = make_receipt(
        checks=[AuditCheck("integrity", "FAIL", "hash mismatch")],
        resolution_status="VERIFIED",
    )
    assert receipt.status == "FAIL"


def test_pending_or_unresolved_resolution_holds():
    pending = make_receipt(resolution_status="PENDING")
    unresolved = make_receipt(resolution_status="UNRESOLVED")
    assert pending.status == "HOLD"
    assert unresolved.status == "HOLD"


def test_hold_check_produces_hold():
    receipt = make_receipt(
        checks=[AuditCheck("evidence", "HOLD", "binding pending")],
        resolution_status="VERIFIED",
    )
    assert receipt.status == "HOLD"


def test_tamper_is_detected():
    receipt = make_receipt()
    assert receipt.verify_integrity()
    object.__setattr__(receipt, "_authority_ref", "spoofed")
    with pytest.raises(ValueError, match="integrity check failed"):
        receipt.serialize()


def test_private_reasoning_and_authority_mutation_are_absent():
    receipt = make_receipt()
    public = receipt.to_dict()
    serialized = json.dumps(public)
    assert "chain_of_thought" not in serialized.lower()
    assert "private_reasoning" not in serialized.lower()
    assert "grant_authority" not in serialized.lower()


def test_public_projection_is_read_only():
    receipt = make_receipt()
    public = receipt.to_dict()
    public["evidence_refs"].append("spoofed")
    public["checks"][0]["status"] = "FAIL"
    assert receipt.status == "PASS"
    assert "spoofed" not in receipt.serialize()
