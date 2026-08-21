"""Pure, transport-neutral DecisionRecord v0.1 composition layer.

DecisionRecord is deliberately not a ledger or persistence mechanism. It composes
existing envelope/evidence references into a deterministic public integrity record.
Capability impact is a passive reference; this module never mutates progression,
XP, qualification, authority, or runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


DECISION_RECORD_VERSION = "decision-record-v0.1"


def _freeze(value: Any) -> Any:
    """Recursively freeze JSON-like public decision data."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    """Return JSON-serializable mutable copies of frozen public data."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(_thaw(value), sort_keys=True, separators=(",", ":"), default=str)


def _require_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_evidence_refs(refs: list[str]) -> tuple[str, ...]:
    if not isinstance(refs, list) or not refs:
        raise ValueError("evidence_refs must contain at least one reference")
    normalized: list[str] = []
    for ref in refs:
        _require_text(ref, "evidence_ref")
        normalized.append(ref)
    return tuple(normalized)


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable decision projection over existing SAGE evidence and state."""

    decision_id: str
    context_id: str
    authority_ref: str
    evidence_refs: tuple[str, ...]
    decision_payload: Mapping[str, Any]
    timestamp_locked: float | str
    resolution: Mapping[str, Any] | None = None
    capability_impact_ref: str | None = None
    decision_hash: str = ""
    version: str = DECISION_RECORD_VERSION

    @classmethod
    def create(
        cls,
        *,
        decision_id: str,
        context_id: str,
        authority_ref: str,
        evidence_refs: list[str],
        decision_payload: Mapping[str, Any],
        timestamp_locked: float | str,
        envelope: Mapping[str, Any] | None = None,
    ) -> "DecisionRecord":
        """Create a locked record after validating context/authority linkage."""
        _require_text(decision_id, "decision_id")
        _require_text(context_id, "context_id")
        _require_text(authority_ref, "authority_ref")
        refs = _validate_evidence_refs(evidence_refs)
        if not isinstance(decision_payload, Mapping):
            raise ValueError("decision_payload must be a mapping")
        if timestamp_locked is None or (isinstance(timestamp_locked, str) and not timestamp_locked.strip()):
            raise ValueError("timestamp_locked is required")

        if envelope is not None:
            if envelope.get("context_id") != context_id:
                raise ValueError("authority/context envelope mismatch: context_id")
            if envelope.get("authority") != authority_ref:
                raise ValueError("authority/context envelope mismatch: authority")

        payload = _freeze(decision_payload)
        decision_block = {
            "decision_id": decision_id,
            "context_id": context_id,
            "authority_ref": authority_ref,
            "evidence_refs": refs,
            "decision_payload": payload,
            "timestamp_locked": timestamp_locked,
            "version": DECISION_RECORD_VERSION,
        }
        digest = hashlib.sha256(_canonical(decision_block).encode("utf-8")).hexdigest()
        return cls(
            decision_id=decision_id,
            context_id=context_id,
            authority_ref=authority_ref,
            evidence_refs=refs,
            decision_payload=payload,
            timestamp_locked=timestamp_locked,
            decision_hash=digest,
        )

    def _decision_block(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "authority_ref": self.authority_ref,
            "evidence_refs": self.evidence_refs,
            "decision_payload": self.decision_payload,
            "timestamp_locked": self.timestamp_locked,
            "version": self.version,
        }

    def verify_integrity(self) -> bool:
        """Verify the immutable pre-lock decision block against its stored hash."""
        if not self.decision_hash:
            return False
        expected = hashlib.sha256(_canonical(self._decision_block()).encode("utf-8")).hexdigest()
        return expected == self.decision_hash

    def resolve(self, outcome: Mapping[str, Any], *, verification_status: str) -> "DecisionRecord":
        """Append a resolution as a new immutable projection; never mutate the lock."""
        if self.resolution is not None:
            raise ValueError("decision already has a resolution")
        if not isinstance(outcome, Mapping):
            raise ValueError("resolution must be a mapping")
        _require_text(verification_status, "verification_status")
        resolution = _freeze({**dict(outcome), "verification_status": verification_status})
        return replace(self, resolution=resolution)

    def with_capability_impact(self, capability_impact_ref: str) -> "DecisionRecord":
        """Attach an external evaluation reference without granting capability."""
        _require_text(capability_impact_ref, "capability_impact_ref")
        return replace(self, capability_impact_ref=capability_impact_ref)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic public serialization with no private reasoning."""
        return {
            "decision_record_version": self.version,
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "authority_ref": self.authority_ref,
            "evidence_refs": list(self.evidence_refs),
            "decision_payload": _thaw(self.decision_payload),
            "timestamp_locked": self.timestamp_locked,
            "resolution": _thaw(self.resolution) if self.resolution is not None else None,
            "capability_impact_ref": self.capability_impact_ref,
            "decision_hash": self.decision_hash,
        }

    def serialize(self) -> str:
        return _canonical(self.to_dict())
