"""Zero-storage verification of evidence bindings used by SAGE decisions.

The verifier does not persist evidence or decide capability. It only establishes
whether a supplied evidence object is internally bound to its declared
reference, source identity/version, timestamp, and cryptographic content hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

VERIFIED = "VERIFIED"
FALSIFIED = "FALSIFIED"
PENDING = "PENDING"
BINDING_VERSION = "evidence-binding-v0.1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True)
class EvidenceBinding:
    evidence_ref: str
    source_id: str
    source_version: str
    observed_at: str
    content: Any
    content_hash: str
    verification_status: str = VERIFIED
    binding_version: str = BINDING_VERSION

    def __post_init__(self) -> None:
        _required_text(self.evidence_ref, "evidence_ref")
        _required_text(self.source_id, "source_id")
        _required_text(self.source_version, "source_version")
        _required_text(self.observed_at, "observed_at")
        if self.verification_status not in {VERIFIED, FALSIFIED, PENDING}:
            raise ValueError("verification_status must be VERIFIED, FALSIFIED, or PENDING")
        _required_text(self.content_hash, "content_hash")

    def computed_hash(self) -> str:
        return hashlib.sha256(_canonical(self.content).encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        return self.computed_hash() == self.content_hash.lower()

    def is_admissible(self) -> bool:
        return self.verification_status == VERIFIED and self.verify_integrity()

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_version": self.binding_version,
            "evidence_ref": self.evidence_ref,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "observed_at": self.observed_at,
            "content": self.content,
            "content_hash": self.content_hash.lower(),
            "verification_status": self.verification_status,
        }


class EvidenceBindingVerifier:
    """Fail-closed verifier for a bounded set of evidence references."""

    def verify_required(
        self,
        required_refs: Sequence[str],
        bindings: Mapping[str, EvidenceBinding],
    ) -> dict[str, str]:
        required = tuple(required_refs)
        if len(required) != len(set(required)):
            raise ValueError("duplicate required evidence_ref is not allowed")

        verdicts: dict[str, str] = {}
        for ref in required:
            _required_text(ref, "evidence_ref")
            binding = bindings.get(ref)
            if binding is None:
                verdicts[ref] = PENDING
                continue
            if binding.evidence_ref != ref:
                verdicts[ref] = FALSIFIED
                continue
            verdicts[ref] = VERIFIED if binding.is_admissible() else FALSIFIED
        return verdicts
