"""Adversarial tests for the pure DecisionRecord v0.1 projection."""

import pytest

from sage.decision_record import DecisionRecord

AUTHORITY = "SAGE_LEVEL_3"


def make_record() -> DecisionRecord:
    return DecisionRecord.create(
        decision_id="dec-001", context_id="ctx-001", authority_ref=AUTHORITY,
        evidence_refs=["sha256:receipt-001"],
        decision_payload={"action": "observe", "confidence": 0.8, "features": {"x": [1, 2]}},
        timestamp_locked=1000.0,
        envelope={"context_id": "ctx-001", "authority": AUTHORITY},
    )


def test_deterministic_serialization_and_replay():
    first = make_record(); second = make_record()
    assert first.serialize() == second.serialize()
    assert first.to_dict() == second.to_dict()
    assert first.verify_integrity()


def test_missing_or_invalid_evidence_ref_fails_closed():
    with pytest.raises(ValueError):
        DecisionRecord.create(decision_id="dec-001", context_id="ctx-001", authority_ref=AUTHORITY, evidence_refs=[], decision_payload={}, timestamp_locked=1.0)
    with pytest.raises(ValueError):
        DecisionRecord.create(decision_id="dec-001", context_id="ctx-001", authority_ref=AUTHORITY, evidence_refs=[""], decision_payload={}, timestamp_locked=1.0)


def test_authority_mismatch_fails_closed():
    with pytest.raises(ValueError):
        DecisionRecord.create(decision_id="dec-001", context_id="ctx-001", authority_ref=AUTHORITY, evidence_refs=["receipt-1"], decision_payload={}, timestamp_locked=1.0, envelope={"context_id": "ctx-001", "authority": "WRONG"})


def test_post_lock_mutation_rejected():
    record = make_record()
    with pytest.raises(TypeError): record.decision_payload["action"] = "mutate"
    with pytest.raises(TypeError): record.decision_payload["features"]["x"] += (3,)
    assert record.verify_integrity()


def test_duplicate_resolution_rejected_and_unresolved_preserved():
    record = make_record()
    resolved = record.resolve({"result": "success", "evidence": {"score": 1}}, verification_status="VERIFIED")
    assert record.resolution is None
    assert resolved.resolution["verification_status"] == "VERIFIED"
    with pytest.raises(TypeError): resolved.resolution["evidence"]["score"] = 2
    with pytest.raises(ValueError): resolved.resolve({"result": "again"}, verification_status="VERIFIED")


def test_capability_impact_cannot_mutate_progression():
    record = make_record().with_capability_impact("eval-001")
    assert record.capability_impact_ref == "eval-001"
    assert not hasattr(record, "grant_xp")
    assert not hasattr(record, "grant_authority")
    assert not hasattr(record, "update_qualification")
    assert record.verify_integrity()


def test_envelope_context_linkage():
    with pytest.raises(ValueError):
        DecisionRecord.create(decision_id="dec-001", context_id="ctx-A", authority_ref=AUTHORITY, evidence_refs=["receipt-1"], decision_payload={}, timestamp_locked=1.0, envelope={"context_id": "ctx-B", "authority": AUTHORITY})


def test_tamper_and_hash_integrity():
    record = make_record()
    tampered = record.__class__(**{**record.__dict__, "decision_payload": {"action": "tampered", "confidence": 0.8}})
    assert record.verify_integrity()
    assert not tampered.verify_integrity()


def test_backward_compatible_public_receipt_references():
    record = DecisionRecord.create(decision_id="dec-legacy", context_id="ctx-legacy", authority_ref=AUTHORITY, evidence_refs=["receipt.json", "sha256:legacy-receipt"], decision_payload={"legacy": True}, timestamp_locked="2026-08-21T20:00:00Z")
    assert record.verify_integrity()
    assert record.to_dict()["evidence_refs"] == ["receipt.json", "sha256:legacy-receipt"]
