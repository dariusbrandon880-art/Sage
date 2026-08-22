"""Governed Tier-4 capability transition engine v0.1.

This module is the first state-mutating boundary in SAGE. It accepts only an
immutable, already-produced AttestationReceipt and performs one bounded
capability transition after independently validating authenticity, decision,
scope, and replay state.

Cryptographic key management/signing remains outside this engine. A trusted
signature verifier is injected at the boundary so this primitive never
creates, stores, or escalates signing authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, MutableMapping

from .attestation_receipt import AttestationDecision, AttestationReceipt


class TransitionAuthorityError(ValueError):
    """Base error for rejected governed transitions."""


class InvalidAttestationError(TransitionAuthorityError):
    """Raised when receipt authenticity or structural invariants fail."""


class ReplayAttestationError(TransitionAuthorityError):
    """Raised when an already-consumed receipt is presented again."""


class ScopeMismatchError(TransitionAuthorityError):
    """Raised when requested transition scope does not match the receipt."""


class TransitionDecision(str, Enum):
    """Outcome of one bounded capability transition attempt."""

    APPLIED = "APPLIED"


SignatureVerifier = Callable[[AttestationReceipt, str], bool]


@dataclass(frozen=True)
class TransitionRequest:
    """Exact single-target transition requested by a caller."""

    capability_id: str
    subject_id: str
    policy_version: str
    target_state: str

    def __post_init__(self) -> None:
        for name in (
            "capability_id",
            "subject_id",
            "policy_version",
            "target_state",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ScopeMismatchError(f"{name} must be a non-empty string.")


@dataclass(frozen=True)
class TransitionExecutionRecord:
    """Immutable receipt of one successfully applied state transition."""

    receipt_id: str
    capability_id: str
    subject_id: str
    previous_state: str
    new_state: str
    policy_version: str
    decision: TransitionDecision = TransitionDecision.APPLIED
    state_mutated: bool = True

    def __post_init__(self) -> None:
        if not self.receipt_id.strip():
            raise ValueError("receipt_id must be non-empty")
        if not self.capability_id.strip() or not self.subject_id.strip():
            raise ValueError("capability_id and subject_id must be non-empty")
        if not self.previous_state.strip() or not self.new_state.strip():
            raise ValueError("transition states must be non-empty")
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")
        if self.decision is not TransitionDecision.APPLIED:
            raise ValueError("decision must be APPLIED")
        if not self.state_mutated:
            raise ValueError("successful execution record must mark mutation")


class TransitionAuthorityEngine:
    """Single-target, replay-protected capability state mutator.

    ``capability_state`` is an explicitly supplied mutable state boundary.
    The engine mutates exactly one key per successful call and records the
    consumed receipt ID in the supplied replay ledger. It never creates keys
    or signs receipts.
    """

    def __init__(
        self,
        *,
        trusted_reviewer_keys: Mapping[str, str],
        signature_verifier: SignatureVerifier,
        capability_state: MutableMapping[str, str],
        consumed_receipt_ids: set[str] | None = None,
    ) -> None:
        self._trusted_reviewer_keys = dict(trusted_reviewer_keys)
        self._signature_verifier = signature_verifier
        self._capability_state = capability_state
        self._consumed_receipt_ids = consumed_receipt_ids if consumed_receipt_ids is not None else set()

    @property
    def consumed_receipt_ids(self) -> frozenset[str]:
        return frozenset(self._consumed_receipt_ids)

    def execute(
        self,
        receipt: AttestationReceipt,
        request: TransitionRequest,
    ) -> TransitionExecutionRecord:
        """Validate one receipt and apply exactly one requested transition."""
        if not isinstance(receipt, AttestationReceipt):
            raise InvalidAttestationError("receipt must be an AttestationReceipt")
        if receipt.state_mutated:
            raise InvalidAttestationError("attestation receipt is already mutated")
        if receipt.decision is not AttestationDecision.APPROVED:
            raise InvalidAttestationError("only APPROVED attestations may transition state")
        if receipt.receipt_id in self._consumed_receipt_ids:
            raise ReplayAttestationError("attestation receipt has already been consumed")

        expected_key = self._trusted_reviewer_keys.get(receipt.reviewer_id)
        if expected_key is None:
            raise InvalidAttestationError("reviewer_id is not trusted")
        try:
            authentic = self._signature_verifier(receipt, expected_key)
        except Exception as exc:
            raise InvalidAttestationError("signature verification failed") from exc
        if not authentic:
            raise InvalidAttestationError("attestation signature is invalid")

        if (
            receipt.capability_id != request.capability_id
            or receipt.subject_id != request.subject_id
            or receipt.policy_version != request.policy_version
        ):
            raise ScopeMismatchError("transition request does not match attestation scope")

        state_key = f"{request.subject_id}:{request.capability_id}"
        previous_state = self._capability_state.get(state_key, "UNQUALIFIED")

        # Commit the bounded transition only after every validation gate passes.
        self._capability_state[state_key] = request.target_state
        self._consumed_receipt_ids.add(receipt.receipt_id)

        return TransitionExecutionRecord(
            receipt_id=receipt.receipt_id,
            capability_id=request.capability_id,
            subject_id=request.subject_id,
            previous_state=previous_state,
            new_state=request.target_state,
            policy_version=request.policy_version,
        )
