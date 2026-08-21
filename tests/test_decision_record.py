"""Adversarial contract tests for DecisionRecord v0.1."""

import json

import pytest

from sage.decision_record import DecisionRecord, DecisionResolution


SHA = "a" * 64


def make_record(**overrides):
    values = {
        "decision_id": "decision-001",
        "context_id": "ctx-001",
        "authority_ref": "c2-level-1",
        "evidence_refs": [SHA, "receipt:001"],
        "decision_payload": {"action": "research", "confidence": 0.8},
        "timestamp_locked": "2026-08-21T22:00:00Z",
        "active_authority_ref": "c2-level-1",
    }
    values.update(overrides)
    return DecisionRecord(**values)


def test_deterministic_serialization_and_replay():
    record = make_record()
    serialized = record.serialize()
    assert serialized == make_record().serialize()
    replayed = record.replay()
    assert replayed.serialize() == serialized
    assert replayed.decision_hash == record.decision_hash


def test_missing_or_invalid_evidence_ref_fails_closed():
    with pytest.raises(ValueError, match="at least one evidence_ref"):
        make_record(evidence_refs=[])
    with pytest.raises(ValueError, match="invalid evidence_ref"):
        make_record(evidence_refs=["not valid ref!"])


def test_authority_mismatch_fails_closed():
    with pytest.raises(ValueError, match="authority mismatch"):
        make_record(authority_ref="director-level-9")


def test_post_lock_mutation_rejected():
    record = make_record()
    with pytest.raises(AttributeError, match="immutable"):
        record._decision_payload = {"action": "mutated"}
    with pytest.raises(AttributeError, match="immutable"):
        record._authority_ref = "spoofed"
    with pytest.raises(AttributeError, match="immutable"):
        record._status = "MUTATED"


def test_duplicate_resolution_is_idempotent_but_conflict_rejected():
    record = make_record()
    resolution = DecisionResolution(
        resolution_id="resolution-001",
        verification_status="VERIFIED",
        ground_truth_result={"result": "complete"},
        verified_timestamp="2026-08-21T23:00:00Z",
        delta_metric={"error": 0.1},
    )
    record.add_resolution(resolution)
    record.add_resolution(resolution)
    assert record.resolution == resolution

    conflicting = DecisionResolution(
        resolution_id="resolution-002",
        verification_status="FALSIFIED",
        ground_truth_result={"result": "different"},
        verified_timestamp="2026-08-21T23:01:00Z",
    )
    with pytest.raises(ValueError, match="conflicting resolution"):
        record.add_resolution(conflicting)


def test_unresolved_outcome_preserved():
    record = make_record()
    record.add_resolution(
        DecisionResolution(
            resolution_id="resolution-pending",
            verification_status="PENDING",
            ground_truth_result={"status": "UNRESOLVED"},
            verified_timestamp="2026-08-21T23:00:00Z",
        )
    )
    assert record.to_dict()["resolution"]["verification_status"] == "PENDING"
    assert record.to_dict()["resolution"]["ground_truth_result"]["status"] == "UNRESOLVED"


def test_capability_impact_is_reference_only():
    record = make_record(capability_impact_ref="evaluation:001")
    public = record.to_dict()
    assert public["capability_impact_ref"] == "evaluation:001"
    assert not hasattr(record, "grant_xp")
    assert not hasattr(record, "grant_authority")
    assert not hasattr(record, "update_qualification")


def test_envelope_context_linkage():
    record = make_record(context_id="ctx-envelope-123")
    assert record.to_dict()["context_id"] == "ctx-envelope-123"


def test_tamper_and_hash_integrity():
    record = make_record()
    assert record.verify_integrity()
    # Bypass the public mutation firewall to simulate disk/object tampering.
    object.__setattr__(record, "_decision_hash", "0" * 64)
    with pytest.raises(ValueError, match="integrity check failed"):
        record.serialize()


def test_public_serialization_contains_no_private_reasoning_field():
    record = make_record(decision_payload={"action": "observe", "evidence": "public"})
    decoded = json.loads(record.serialize())
    assert "chain_of_thought" not in decoded
    assert "private_reasoning" not in decoded
    assert decoded["decision_payload"]["action"] == "observe"


def test_backward_compatible_receipt_reference_shape():
    record = make_record(evidence_refs=[SHA, "AGENT_COORDINATION_RECEIPT:evt-001"])
    assert len(record.to_dict()["evidence_refs"]) == 2
