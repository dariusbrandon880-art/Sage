import dataclasses

import pytest

from sage.core.attestation_receipt import (
    AttestationDecision,
    AttestationReceipt,
    AttestationReceiptValidationError,
)


BASE = {
    "assessment_digest": "assessment-123",
    "sufficiency_digest": "sufficiency-456",
    "capability_id": "capability.demo",
    "subject_id": "agent.demo",
    "policy_version": "policy-v1",
    "reviewer_id": "reviewer-key-1",
    "authorization_scope": "capability.demo:promote",
    "attested_at": "2026-08-21T20:00:00Z",
    "decision": AttestationDecision.APPROVED,
    "signature": "signature-by-authorized-reviewer",
}


def make_receipt(**overrides: object) -> AttestationReceipt:
    payload = {**BASE, **overrides}
    return AttestationReceipt(**payload)


def test_receipt_binds_required_fields_and_is_non_authoritative() -> None:
    receipt = make_receipt()

    assert receipt.receipt_id
    assert len(receipt.receipt_id) == 64
    assert receipt.state_mutated is False
    assert receipt.to_dict()["decision"] == "APPROVED"
    assert receipt.to_dict()["state_mutated"] is False
    assert receipt.attestation_payload_digest


def test_receipt_is_deterministic() -> None:
    first = make_receipt()
    second = make_receipt()

    assert first.receipt_id == second.receipt_id
    assert first.attestation_payload_digest == second.attestation_payload_digest


def test_receipt_id_changes_when_bound_field_changes() -> None:
    baseline = make_receipt()
    changed = make_receipt(authorization_scope="capability.demo:view")

    assert baseline.receipt_id != changed.receipt_id


def test_signature_is_bound_to_receipt_identity() -> None:
    first = make_receipt(signature="signature-a")
    second = make_receipt(signature="signature-b")

    assert first.receipt_id != second.receipt_id
    assert first.attestation_payload_digest == second.attestation_payload_digest


def test_round_trip_preserves_receipt_identity() -> None:
    receipt = make_receipt()

    restored = AttestationReceipt.from_dict(receipt.to_dict())

    assert restored == receipt
    assert restored.receipt_id == receipt.receipt_id


def test_rejects_invalid_decision() -> None:
    with pytest.raises(AttestationReceiptValidationError):
        make_receipt(decision="APPROVED")


def test_rejects_missing_required_strings() -> None:
    for field_name in (
        "assessment_digest",
        "sufficiency_digest",
        "capability_id",
        "subject_id",
        "policy_version",
        "reviewer_id",
        "authorization_scope",
        "attested_at",
        "signature",
    ):
        with pytest.raises(AttestationReceiptValidationError):
            make_receipt(**{field_name: ""})


def test_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(AttestationReceiptValidationError):
        make_receipt(attested_at="2026-08-21T20:00:00")


def test_accepts_explicit_nonzero_offset() -> None:
    receipt = make_receipt(attested_at="2026-08-21T20:00:00-07:00")

    assert receipt.receipt_id


def test_rejects_invalid_timestamp() -> None:
    with pytest.raises(AttestationReceiptValidationError):
        make_receipt(attested_at="not-a-timestamp")


def test_rejects_receipt_id_tampering_on_import() -> None:
    payload = make_receipt().to_dict()
    payload["receipt_id"] = "0" * 64

    with pytest.raises(AttestationReceiptValidationError):
        AttestationReceipt.from_dict(payload)


def test_rejects_state_mutation_flag_on_import() -> None:
    payload = make_receipt().to_dict()
    payload["state_mutated"] = True

    with pytest.raises(AttestationReceiptValidationError):
        AttestationReceipt.from_dict(payload)


def test_receipt_is_immutable() -> None:
    receipt = make_receipt()

    with pytest.raises(dataclasses.FrozenInstanceError):
        receipt.decision = AttestationDecision.REJECTED


def test_decision_taxonomy_is_closed() -> None:
    assert {item.value for item in AttestationDecision} == {
        "APPROVED",
        "REJECTED",
        "DEFERRED",
    }
