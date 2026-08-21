"""DecisionRecord v0.1 — pure, zero-storage decision projection.

This module composes existing context, authority, evidence, outcome, and
capability-evaluation references without creating persistence or mutating any
canonical SAGE state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


VERIFIED = "VERIFIED"
FALSIFIED = "FALSIFIED"
INCONCLUSIVE = "INCONCLUSIVE"


class DecisionRecordValidationError(ValueError):
    """Raised when a DecisionRecord input is invalid."""


class DecisionRecordMutationError(ValueError):
    """Raised when an immutable decision is resolved more than once."""


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


@dataclass(frozen=True)
class DecisionRecord:
    """Deterministic, serializable projection of one governed decision."""

    context_id: str
    authority_ref: str
    evidence_refs: tuple[str, ...]
    decision_payload: Mapping[str, Any]
    timestamp_locked: str
    resolution: Mapping[str, Any] | None = None
    capability_impact_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise DecisionRecordValidationError("context_id must be a non-empty string")
        if not isinstance(self.authority_ref, str) or not self.authority_ref.strip():
            raise DecisionRecordValidationError("authority_ref must be a non-empty string")
        if not isinstance(self.timestamp_locked, str) or not self.timestamp_locked.strip():
            raise DecisionRecordValidationError("timestamp_locked must be a non-empty string")
        if not isinstance(self.evidence_refs, Sequence) or isinstance(self.evidence_refs, (str, bytes)):
            raise DecisionRecordValidationError("evidence_refs must be a sequence of strings")
        refs = tuple(self.evidence_refs)
        if not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise DecisionRecordValidationError("evidence_refs must contain non-empty strings")
        if len(refs) != len(set(refs)):
            raise DecisionRecordValidationError("evidence_refs must not contain duplicates")
        if not isinstance(self.decision_payload, Mapping):
            raise DecisionRecordValidationError("decision_payload must be a mapping")
        if self.resolution is not None and not isinstance(self.resolution, Mapping):
            raise DecisionRecordValidationError("resolution must be a mapping or None")
        if self.capability_impact_ref is not None and (
            not isinstance(self.capability_impact_ref, str) or not self.capability_impact_ref.strip()
        ):
            raise DecisionRecordValidationError("capability_impact_ref must be a non-empty string or None")

        object.__setattr__(self, "evidence_refs", tuple(refs))
        object.__setattr__(self, "decision_payload", dict(self.decision_payload))
        if self.resolution is not None:
            object.__setattr__(self, "resolution", dict(self.resolution))

    @property
    def decision_id(self) -> str:
        """Hash identity derived only from immutable T0 decision inputs."""
        content = {
            "context_id": self.context_id,
            "authority_ref": self.authority_ref,
            "evidence_refs": sorted(self.evidence_refs),
            "decision_payload": self.decision_payload,
            "timestamp_locked": self.timestamp_locked,
        }
        return hashlib.sha256(_canonical(content).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible projection."""
        return {
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "authority_ref": self.authority_ref,
            "evidence_refs": sorted(self.evidence_refs),
            "decision_payload": dict(self.decision_payload),
            "timestamp_locked": self.timestamp_locked,
            "resolution": dict(self.resolution) if self.resolution is not None else None,
            "capability_impact_ref": self.capability_impact_ref,
        }

    def resolve(
        self,
        ground_truth: Mapping[str, Any],
        verification_status: str,
        capability_impact_ref: str | None = None,
    ) -> "DecisionRecord":
        """Return a new resolved projection without mutating the T0 decision."""
        if self.resolution is not None:
            raise DecisionRecordMutationError("DecisionRecord is already resolved")
        if not isinstance(ground_truth, Mapping):
            raise DecisionRecordValidationError("ground_truth must be a mapping")
        if verification_status not in {VERIFIED, FALSIFIED, INCONCLUSIVE}:
            raise DecisionRecordValidationError(
                f"invalid verification_status: {verification_status}"
            )
        resolution_payload = dict(ground_truth)
        resolution_hash = hashlib.sha256(_canonical(resolution_payload).encode("utf-8")).hexdigest()
        resolution = {
            "ground_truth": resolution_payload,
            "verification_status": verification_status,
            "resolution_hash": resolution_hash,
        }
        return DecisionRecord(
            context_id=self.context_id,
            authority_ref=self.authority_ref,
            evidence_refs=self.evidence_refs,
            decision_payload=self.decision_payload,
            timestamp_locked=self.timestamp_locked,
            resolution=resolution,
            capability_impact_ref=capability_impact_ref,
        )
