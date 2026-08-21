"""Adversarial tests for evidence-backed capability envelope projection."""

import pytest

from sage.agent_context_envelope import build_agent_context_envelope
from sage.capability_projection import project_capability_state
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
    return build_agent_context_envelope(
        sender="agent:c2",
        recipient="agent:reviewer",
        event_id="evt-001",
        context_id="ctx-001",
        timestamp="2026-08-21T23:06:00Z",
        event_type="CAPABILITY_EVALUATION",
        payload={"public": True},
        sender_identity_projection={"role": "c2"},
    )


def test_projection_is_evidence_backed_and_non_authoritative():
    envelope = make_envelope()
    projected = project_capability_state(envelope, make_evaluation())
    capability = projected["sender_identity_projection"]["capability_projection"]
    assert capability["verdict"] == "PROMOTION_CANDIDATE"
    assert capability["reviewer_required"] is True
    assert capability["authoritative"] is False
    assert projected["read_only"] is True


def test_projection_does_not_mutate_input_envelope():
    envelope = make_envelope()
    before = dict(envelope)
    projected = project_capability_state(envelope, make_evaluation())
    assert envelope == before
    assert projected is not envelope


def test_tampered_evaluation_fails_closed():
    evaluation = make_evaluation()
    payload = evaluation.to_dict()
    payload["verdict"] = "PROMOTED"
    tampered = evaluation.__class__(**payload)
    with pytest.raises(ValueError, match="integrity failed"):
        project_capability_state(make_envelope(), tampered)


def test_non_read_only_envelope_fails_closed():
    envelope = make_envelope()
    envelope["read_only"] = False
    with pytest.raises(ValueError, match="read-only"):
        project_capability_state(envelope, make_evaluation())


def test_missing_context_fails_closed():
    envelope = make_envelope()
    envelope["context_id"] = None
    with pytest.raises(ValueError, match="context_id"):
        project_capability_state(envelope, make_evaluation())
