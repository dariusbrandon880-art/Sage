"""Adversarial tests for capability-to-envelope projection."""

import copy

import pytest

from sage.agent_context_envelope import ENVELOPE_VERSION
from sage.capability_context_projection import (
    PROJECTION_VERSION,
    project_capability_evaluation_to_envelope,
)
from sage.decision_record import DecisionRecord, DecisionResolution
from sage.evidence_capability_evaluator import EvidenceCapabilityEvaluator


def make_evaluation():
    decision = DecisionRecord(
        decision_id="decision-001",
        context_id="ctx-001",
        authority_ref="c2-level-1",
        evidence_refs=["receipt:001"],
        decision_payload={"action": "evaluate"},
        timestamp_locked="2026-08-21T23:00:00Z",
        active_authority_ref="c2-level-1",
    )
    decision.add_resolution(
        DecisionResolution(
            resolution_id="resolution-001",
            verification_status="VERIFIED",
            ground_truth_result={"result": "complete"},
            verified_timestamp="2026-08-21T23:05:00Z",
        )
    )
    return EvidenceCapabilityEvaluator().evaluate(
        decision,
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED"},
    )


def make_envelope():
    return {
        "envelope_version": ENVELOPE_VERSION,
        "sender": "SAGE::ENGINE",
        "recipient": "SAGE::C2",
        "context_id": "ctx-001",
        "event_id": "event-001",
        "event_type": "DECISION",
        "timestamp": "2026-08-21T23:00:00Z",
        "projection_version": ENVELOPE_VERSION,
        "delivery_state": "PENDING",
        "sender_identity_projection": {"agent": "SAGE"},
        "authority": "canonical_airspace_state_and_event_ledger",
        "read_only": True,
        "payload": {"kind": "test"},
    }


def test_complete_evaluation_projects_candidate_without_authority():
    envelope = make_envelope()
    projected = project_capability_evaluation_to_envelope(envelope, make_evaluation())
    identity = projected["sender_identity_projection"]

    assert projected["projection_version"] == ENVELOPE_VERSION
    assert projected["capability_projection_version"] == PROJECTION_VERSION
    assert identity["capability_verdict"] == "PROMOTION_CANDIDATE"
    assert identity["capability_delta"] == "CANDIDATE_UP"
    assert identity["reviewer_required"] is True
    assert identity["authority_granted"] is False
    assert identity["qualification_mutated"] is False
    assert projected["read_only"] is True


def test_hold_evaluation_remains_hold():
    evaluation = make_evaluation()
    decision = DecisionRecord(
        decision_id="decision-pending",
        context_id="ctx-001",
        authority_ref="c2-level-1",
        evidence_refs=["receipt:001"],
        decision_payload={"action": "evaluate"},
        timestamp_locked="2026-08-21T23:00:00Z",
        active_authority_ref="c2-level-1",
    )
    hold = EvidenceCapabilityEvaluator().evaluate(
        decision,
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "PENDING"},
    )
    envelope = make_envelope()
    projected = project_capability_evaluation_to_envelope(envelope, hold)
    assert projected["sender_identity_projection"]["capability_verdict"] == "HOLD"
    assert projected["sender_identity_projection"]["capability_delta"] == "NO_CHANGE"
    assert projected["sender_identity_projection"]["authority_granted"] is False
    assert evaluation.verdict == "PROMOTION_CANDIDATE"


def test_projection_does_not_mutate_envelope():
    envelope = make_envelope()
    before = copy.deepcopy(envelope)
    project_capability_evaluation_to_envelope(envelope, make_evaluation())
    assert envelope == before


def test_invalid_evaluation_fails_closed():
    evaluation = make_evaluation()
    object.__setattr__(evaluation, "evaluation_hash", "0" * 64)
    with pytest.raises(ValueError, match="integrity failed"):
        project_capability_evaluation_to_envelope(make_envelope(), evaluation)


def test_invalid_envelope_version_fails_closed():
    envelope = make_envelope()
    envelope["envelope_version"] = "unknown"
    with pytest.raises(ValueError, match="unsupported"):
        project_capability_evaluation_to_envelope(envelope, make_evaluation())


def test_projection_preserves_existing_identity_fields():
    envelope = make_envelope()
    envelope["sender_identity_projection"]["role"] = "research"
    projected = project_capability_evaluation_to_envelope(envelope, make_evaluation())
    assert projected["sender_identity_projection"]["role"] == "research"
    assert projected["sender_identity_projection"]["agent"] == "SAGE"
