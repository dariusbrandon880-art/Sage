"""Attestation receipt v0.1 — immutable authorization artifact.

This module records an already-produced cryptographic attestation. It does
not create signatures, grant authority, mutate capability state, persist
state, or perform a capability transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json


class AttestationReceiptValidationError(ValueError):
    """Raised when an attestation receipt violates its contract."""


class AttestationDecision(str, Enum):
    """Explicit decision carried by an authorized attestation."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class AttestationReceipt:
    """Immutable attestation artifact with no state-transition authority."""

    assessment_digest: str
    sufficiency_digest: str
    capability_id: str
    subject_id: str
    policy_version: str
    reviewer_id: str
    authorization_scope: str
    attested_at: str
    decision: AttestationDecision
    signature: str
    receipt_id: str = field(init=False)
    state_mutated: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        for name in (
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
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise AttestationReceiptValidationError(
                    f"{name} must be a non-empty string."
                )
        if not isinstance(self.decision, AttestationDecision):
            raise AttestationReceiptValidationError(
                "decision must be an AttestationDecision."
            )
        try:
            parsed = datetime.fromisoformat(self.attested_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise AttestationReceiptValidationError(
                "attested_at must be a valid ISO-8601 timestamp."
            ) from exc
        if parsed.tzinfo is None:
            raise AttestationReceiptValidationError(
                "attested_at must include an explicit timezone."
            )
        if not parsed.tzinfo.utcoffset(parsed):
            raise AttestationReceiptValidationError(
                "attested_at must include an explicit timezone."
            )
        object.__setattr__(self, "receipt_id", self._compute_receipt_id())

    def _bound_payload(self) -> dict[str, object]:
        return {
            "assessment_digest": self.assessment_digest,
            "sufficiency_digest": self.sufficiency_digest,
            "capability_id": self.capability_id,
            "subject_id": self.subject_id,
            "policy_version": self.policy_version,
            "reviewer_id": self.reviewer_id,
            "authorization_scope": self.authorization_scope,
            "attested_at": self.attested_at,
            "decision": self.decision.value,
            "signature": self.signature,
            "state_mutated": False,
        }

    def _compute_receipt_id(self) -> str:
        canonical = json.dumps(
            self._bound_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def attestation_payload_digest(self) -> str:
        """Digest of the receipt payload bound by the attestation artifact."""
        payload = dict(self._bound_payload())
        payload.pop("signature")
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "assessment_digest": self.assessment_digest,
            "sufficiency_digest": self.sufficiency_digest,
            "capability_id": self.capability_id,
            "subject_id": self.subject_id,
            "policy_version": self.policy_version,
            "reviewer_id": self.reviewer_id,
            "authorization_scope": self.authorization_scope,
            "attested_at": self.attested_at,
            "decision": self.decision.value,
            "signature": self.signature,
            "state_mutated": self.state_mutated,
            "attestation_payload_digest": self.attestation_payload_digest,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "AttestationReceipt":
        if not isinstance(payload, dict):
            raise AttestationReceiptValidationError("payload must be a dictionary.")
        try:
            receipt = cls(
                assessment_digest=payload["assessment_digest"],
                sufficiency_digest=payload["sufficiency_digest"],
                capability_id=payload["capability_id"],
                subject_id=payload["subject_id"],
                policy_version=payload["policy_version"],
                reviewer_id=payload["reviewer_id"],
                authorization_scope=payload["authorization_scope"],
                attested_at=payload["attested_at"],
                decision=AttestationDecision(payload["decision"]),
                signature=payload["signature"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AttestationReceiptValidationError(
                "payload does not satisfy the attestation receipt contract."
            ) from exc
        supplied_id = payload.get("receipt_id")
        if supplied_id is not None and supplied_id != receipt.receipt_id:
            raise AttestationReceiptValidationError("receipt_id does not match payload.")
        if payload.get("state_mutated", False) is not False:
            raise AttestationReceiptValidationError("state_mutated must be False.")
        return receipt
