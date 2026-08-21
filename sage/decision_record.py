"""Deterministic, zero-storage SAGE decision record projection.

DecisionRecord composes existing context, authority, evidence, and evaluation
references. It does not persist state, grant capability, or capture private
reasoning. The decision block becomes immutable when locked; resolution is a
separate append-only projection.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

DECISION_RECORD_VERSION = "decision-record-v0.1"
_LOCKED = "LOCKED"
_PENDING = "PENDING"
_VERIFIED = "VERIFIED"
_FALSIFIED = "FALSIFIED"

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(copy.deepcopy(dict(value)))


def _validate_ref(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty reference")
    # Existing receipt/artifact references are either canonical SHA-256 digests
    # or explicit stable identifiers. Never accept whitespace-only references.
    if any(ch.isspace() for ch in value):
        raise ValueError(f"{field} must not contain whitespace")
    return value


def _validate_evidence_ref(value: str) -> str:
    value = _validate_ref(value, "evidence_ref")
    if _SHA256.fullmatch(value):
        return value.lower()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{1,255}", value):
        raise ValueError(f"invalid evidence_ref: {value!r}")
    return value


@dataclass(frozen=True)
class DecisionResolution:
    """Immutable post-decision verification projection."""

    resolution_id: str
    verification_status: str
    ground_truth_result: Any
    verified_timestamp: str
    delta_metric: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_ref(self.resolution_id, "resolution_id")
        if self.verification_status not in {_PENDING, _VERIFIED, _FALSIFIED}:
            raise ValueError("verification_status must be PENDING, VERIFIED, or FALSIFIED")
        object.__setattr__(self, "ground_truth_result", copy.deepcopy(self.ground_truth_result))
        object.__setattr__(
            self,
            "delta_metric",
            _freeze_mapping(self.delta_metric) if self.delta_metric is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "verification_status": self.verification_status,
            "ground_truth_result": copy.deepcopy(self.ground_truth_result),
            "verified_timestamp": self.verified_timestamp,
            "delta_metric": copy.deepcopy(dict(self.delta_metric)) if self.delta_metric else None,
        }


class DecisionRecord:
    """Pure decision lifecycle projection with no persistence side effects."""

    __slots__ = (
        "_decision_id",
        "_context_id",
        "_authority_ref",
        "_evidence_refs",
        "_decision_payload",
        "_timestamp_locked",
        "_status",
        "_resolution",
        "_capability_impact_ref",
        "_decision_hash",
    )

    def __init__(
        self,
        *,
        decision_id: str,
        context_id: str,
        authority_ref: str,
        evidence_refs: Sequence[str],
        decision_payload: Mapping[str, Any],
        timestamp_locked: str | float,
        active_authority_ref: str,
        capability_impact_ref: str | None = None,
    ) -> None:
        self._decision_id = _validate_ref(decision_id, "decision_id")
        self._context_id = _validate_ref(context_id, "context_id")
        self._authority_ref = _validate_ref(authority_ref, "authority_ref")
        active_authority_ref = _validate_ref(active_authority_ref, "active_authority_ref")
        if self._authority_ref != active_authority_ref:
            raise ValueError("authority mismatch: authority_ref does not match active authority")
        refs = tuple(_validate_evidence_ref(ref) for ref in evidence_refs)
        if not refs:
            raise ValueError("at least one evidence_ref is required")
        if len(refs) != len(set(refs)):
            raise ValueError("duplicate evidence_ref is not allowed")
        self._evidence_refs = refs
        self._decision_payload = _freeze_mapping(decision_payload)
        if timestamp_locked is None or str(timestamp_locked).strip() == "":
            raise ValueError("timestamp_locked is required")
        self._timestamp_locked = timestamp_locked
        self._status = _LOCKED
        self._resolution = None
        self._capability_impact_ref = (
            _validate_ref(capability_impact_ref, "capability_impact_ref")
            if capability_impact_ref is not None
            else None
        )
        self._decision_hash = self._compute_decision_hash()

    def _decision_block(self) -> dict[str, Any]:
        return {
            "decision_record_version": DECISION_RECORD_VERSION,
            "decision_id": self._decision_id,
            "context_id": self._context_id,
            "authority_ref": self._authority_ref,
            "evidence_refs": list(self._evidence_refs),
            "decision_payload": copy.deepcopy(dict(self._decision_payload)),
            "timestamp_locked": self._timestamp_locked,
            "capability_impact_ref": self._capability_impact_ref,
        }

    def _compute_decision_hash(self) -> str:
        return hashlib.sha256(_canonical(self._decision_block()).encode("utf-8")).hexdigest()

    @property
    def decision_hash(self) -> str:
        return self._decision_hash

    @property
    def status(self) -> str:
        return self._status

    @property
    def resolution(self) -> DecisionResolution | None:
        return self._resolution

    def add_resolution(self, resolution: DecisionResolution) -> None:
        """Append exactly one resolution; never mutate the locked decision."""
        if self._resolution is not None:
            if self._resolution == resolution:
                return
            raise ValueError("duplicate decision resolution: conflicting resolution")
        self._resolution = resolution

    def verify_integrity(self) -> bool:
        return self._decision_hash == self._compute_decision_hash()

    def to_dict(self) -> dict[str, Any]:
        if not self.verify_integrity():
            raise ValueError("decision integrity check failed")
        return {
            **self._decision_block(),
            "status": self._status,
            "decision_hash": self._decision_hash,
            "resolution": self._resolution.to_dict() if self._resolution else None,
        }

    def serialize(self) -> str:
        return _canonical(self.to_dict())

    def replay(self) -> "DecisionRecord":
        """Reconstruct a detached record from its public serialization."""
        payload = json.loads(self.serialize())
        replayed = DecisionRecord(
            decision_id=payload["decision_id"],
            context_id=payload["context_id"],
            authority_ref=payload["authority_ref"],
            evidence_refs=payload["evidence_refs"],
            decision_payload=payload["decision_payload"],
            timestamp_locked=payload["timestamp_locked"],
            active_authority_ref=payload["authority_ref"],
            capability_impact_ref=payload["capability_impact_ref"],
        )
        if payload.get("resolution"):
            replayed.add_resolution(DecisionResolution(**payload["resolution"]))
        if replayed.decision_hash != self.decision_hash:
            raise ValueError("replay integrity mismatch")
        return replayed

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_decision_payload", "_evidence_refs", "_authority_ref", "_context_id", "_decision_id", "_timestamp_locked", "_capability_impact_ref", "_decision_hash"} and hasattr(self, name):
            raise AttributeError("locked DecisionRecord decision block is immutable")
        if name == "_status" and hasattr(self, "_status") and self._status == _LOCKED:
            raise AttributeError("DecisionRecord status cannot mutate the locked decision block")
        super().__setattr__(name, value)
