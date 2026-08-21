"""WitnessBinding v0.1 — non-authoritative provenance witness composition.

This module composes the existing cryptographic attestation provider into a
small, deterministic claim that binds evidence identity, context, source
metadata, observation time, and claim semantics. It does not create storage,
grant authority, or assert that a recorded observation is physically true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict

from sage.core.attestation import CryptographicAttestationProvider


class WitnessBindingValidationError(ValueError):
    """Raised when a witness claim violates its fail-closed contract."""


class WitnessClaimKind(str, Enum):
    """Semantics of the fact being witnessed, not its truth value."""

    OBSERVATION = "OBSERVATION"
    CONTROLLER_REPORT = "CONTROLLER_REPORT"
    EFFECT_REPORT = "EFFECT_REPORT"


@dataclass(frozen=True)
class WitnessBinding:
    """Immutable, zero-storage witness claim over an existing evidence ref.

    A valid signature proves only that the configured attestation provider
    signed this exact canonical claim. It does not independently prove that
    the source was truthful, that an action succeeded, or that a physical
    effect occurred. Those are separate evaluation questions.
    """

    evidence_ref: str
    context_id: str
    source_id: str
    source_version: str
    observed_at: str
    witness_id: str
    provider_mode: str
    signature: str
    claim_kind: WitnessClaimKind = WitnessClaimKind.OBSERVATION
    authority_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        required = {
            "evidence_ref": self.evidence_ref,
            "context_id": self.context_id,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "observed_at": self.observed_at,
            "witness_id": self.witness_id,
            "provider_mode": self.provider_mode,
            "signature": self.signature,
        }
        if any(not isinstance(value, str) or not value.strip() for value in required.values()):
            raise WitnessBindingValidationError("all witness identity, provenance, and signature fields must be non-empty strings")
        if not isinstance(self.claim_kind, WitnessClaimKind):
            raise WitnessBindingValidationError("claim_kind must be a WitnessClaimKind")

    def _claim_payload(self) -> Dict[str, Any]:
        return {
            "claim_kind": self.claim_kind.value,
            "context_id": self.context_id,
            "evidence_ref": self.evidence_ref,
            "observed_at": self.observed_at,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "witness_id": self.witness_id,
        }

    @staticmethod
    def _canonical_bytes(payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @property
    def claim_digest(self) -> str:
        """Stable content address for the exact witnessed claim."""
        return hashlib.sha256(self._canonical_bytes(self._claim_payload())).hexdigest()

    @property
    def witness_id_hash(self) -> str:
        """Stable join key for the witness identity without changing authority."""
        return hashlib.sha256(self.witness_id.encode("utf-8")).hexdigest()

    @classmethod
    def create_witness_claim(
        cls,
        evidence_ref: str,
        context_id: str,
        source_id: str,
        source_version: str,
        observed_at: str,
        witness_id: str,
        attestation_provider: CryptographicAttestationProvider,
        claim_kind: WitnessClaimKind = WitnessClaimKind.OBSERVATION,
    ) -> "WitnessBinding":
        """Create and sign a canonical witness claim with existing SAGE crypto."""
        provisional = cls(
            evidence_ref=evidence_ref,
            context_id=context_id,
            source_id=source_id,
            source_version=source_version,
            observed_at=observed_at,
            witness_id=witness_id,
            provider_mode=attestation_provider.get_provider_type(),
            signature="pending",
            claim_kind=claim_kind,
        )
        signature = attestation_provider.sign(provisional._claim_payload())
        return cls(
            evidence_ref=evidence_ref,
            context_id=context_id,
            source_id=source_id,
            source_version=source_version,
            observed_at=observed_at,
            witness_id=witness_id,
            provider_mode=attestation_provider.get_provider_type(),
            signature=signature,
            claim_kind=claim_kind,
        )

    def verify_signature(self, attestation_provider: CryptographicAttestationProvider) -> bool:
        """Verify the signature over the exact canonical claim payload."""
        return attestation_provider.verify(self._claim_payload(), self.signature)

    def verification_report(self, attestation_provider: CryptographicAttestationProvider) -> Dict[str, Any]:
        """Return an epistemically bounded verification result.

        SAGE deliberately separates cryptographic integrity from evidentiary
        sufficiency. A valid signature establishes that this exact claim was
        signed by the configured provider; it does not establish independent
        witnessing or real-world effect. Independence remains UNKNOWN until
        a verifier has separate trust evidence comparing distinct parties.
        """
        signature_valid = self.verify_signature(attestation_provider)
        return {
            "claim_digest": self.claim_digest,
            "signature_valid": signature_valid,
            "provenance_bound": True,
            "independence_status": "UNKNOWN",
            "real_world_effect_proven": False,
            "authority_granted": False,
            "verification_scope": "SIGNED_CLAIM_INTEGRITY_ONLY",
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return deterministic public evidence metadata; no private reasoning."""
        return {
            "claim_digest": self.claim_digest,
            "claim_kind": self.claim_kind.value,
            "context_id": self.context_id,
            "evidence_ref": self.evidence_ref,
            "observed_at": self.observed_at,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "witness_id": self.witness_id,
            "witness_id_hash": self.witness_id_hash,
            "provider_mode": self.provider_mode,
            "signature": self.signature,
            "authority_granted": False,
        }
