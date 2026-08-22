"""Adversarial tests for the Tier-4 governed transition boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sage.core.attestation_receipt import AttestationDecision, AttestationReceipt
from sage.core.transition_engine import (
    InvalidAttestationError,
    ReplayAttestationError,
    ScopeMismatchError,
    TransitionAuthorityEngine,
    TransitionRequest,
)


def make_receipt(
    *,
    decision: AttestationDecision = AttestationDecision.APPROVED,
    scope: str = "capability:flight",
    signature: str = "signature",
) -> AttestationReceipt:
    return AttestationReceipt(
        assessment_digest="assessment-digest",
        sufficiency_digest="sufficiency-digest",
        capability_id="flight",
        subject_id="agent-1",
        policy_version="policy-v1",
        reviewer_id="reviewer-1",
        authorization_scope=scope,
        attested_at="2026-08-22T03:30:00+00:00",
        decision=decision,
        signature=signature,
    )


def make_request(*, scope: str = "capability:flight") -> TransitionRequest:
    return TransitionRequest(
        capability_id="flight",
        subject_id="agent-1",
        policy_version="policy-v1",
        authorization_scope=scope,
        target_state="QUALIFIED",
    )


def make_engine(state: dict[str, str] | None = None) -> TransitionAuthorityEngine:
    def verify(receipt: AttestationReceipt, trusted_key: str) -> bool:
        return receipt.signature == f"sig:{trusted_key}:{receipt.attestation_payload_digest}"

    receipt = make_receipt()
    return TransitionAuthorityEngine(
        trusted_reviewer_keys={"reviewer-1": "public-key-1"},
        signature_verifier=verify,
        capability_state=state if state is not None else {},
    )


def signed_receipt() -> AttestationReceipt:
    receipt = make_receipt()
    return AttestationReceipt(
        assessment_digest=receipt.assessment_digest,
        sufficiency_digest=receipt.sufficiency_digest,
        capability_id=receipt.capability_id,
        subject_id=receipt.subject_id,
        policy_version=receipt.policy_version,
        reviewer_id=receipt.reviewer_id,
        authorization_scope=receipt.authorization_scope,
        attested_at=receipt.attested_at,
        decision=receipt.decision,
        signature=f"sig:public-key-1:{receipt.attestation_payload_digest}",
    )


def test_approved_authentic_receipt_applies_exactly_one_transition() -> None:
    state = {"agent-1:other": "QUALIFIED"}
    engine = make_engine(state)

    result = engine.execute(signed_receipt(), make_request())

    assert result.previous_state == "UNQUALIFIED"
    assert result.new_state == "QUALIFIED"
    assert state == {"agent-1:other": "QUALIFIED", "agent-1:flight": "QUALIFIED"}
    assert len(engine.consumed_receipt_ids) == 1
    assert result.state_mutated is True


def test_invalid_signature_cannot_mutate_state() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)

    with pytest.raises(InvalidAttestationError):
        engine.execute(make_receipt(), make_request())

    assert state == {}
    assert engine.consumed_receipt_ids == frozenset()


def test_untrusted_reviewer_cannot_mutate_state() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)
    receipt = signed_receipt()
    receipt = AttestationReceipt(
        assessment_digest=receipt.assessment_digest,
        sufficiency_digest=receipt.sufficiency_digest,
        capability_id=receipt.capability_id,
        subject_id=receipt.subject_id,
        policy_version=receipt.policy_version,
        reviewer_id="unknown-reviewer",
        authorization_scope=receipt.authorization_scope,
        attested_at=receipt.attested_at,
        decision=receipt.decision,
        signature=receipt.signature,
    )

    with pytest.raises(InvalidAttestationError):
        engine.execute(receipt, make_request())

    assert state == {}


def test_non_approved_decision_cannot_mutate_state() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)
    receipt = make_receipt(decision=AttestationDecision.DEFERRED)

    with pytest.raises(InvalidAttestationError):
        engine.execute(receipt, make_request())

    assert state == {}


def test_scope_mismatch_cannot_mutate_state() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)

    with pytest.raises(ScopeMismatchError):
        engine.execute(signed_receipt(), make_request(scope="capability:other"))

    assert state == {}
    assert engine.consumed_receipt_ids == frozenset()


def test_replay_is_rejected_before_second_mutation() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)
    receipt = signed_receipt()

    engine.execute(receipt, make_request())
    with pytest.raises(ReplayAttestationError):
        engine.execute(receipt, make_request())

    assert state["agent-1:flight"] == "QUALIFIED"
    assert len(engine.consumed_receipt_ids) == 1


def test_mutated_receipt_is_rejected() -> None:
    state: dict[str, str] = {}
    engine = make_engine(state)
    receipt = signed_receipt()
    object.__setattr__(receipt, "state_mutated", True)

    with pytest.raises(InvalidAttestationError):
        engine.execute(receipt, make_request())

    assert state == {}


def test_execution_record_is_immutable() -> None:
    state = {"agent-1:flight": "UNQUALIFIED"}
    engine = make_engine(state)
    result = engine.execute(signed_receipt(), make_request())

    with pytest.raises(FrozenInstanceError):
        result.new_state = "ADMIN"


def test_transition_request_requires_explicit_scope() -> None:
    with pytest.raises(ScopeMismatchError):
        TransitionRequest(
            capability_id="flight",
            subject_id="agent-1",
            policy_version="policy-v1",
            authorization_scope="",
            target_state="QUALIFIED",
        )
