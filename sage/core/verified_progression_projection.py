"""Read-only, evidence-grounded progression projection.

This module exposes verified progression state without becoming a progression
writer. It intentionally consumes plain mappings so the projection can compose
with existing/future mission and evaluator contracts without coupling to an
unmerged evaluator implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


PROJECTION_VERSION = "verified-progression-v0.1"
_ALLOWED_VERDICTS = {"VERIFIED", "HOLD", "FALSIFIED", "PENDING", "INDETERMINATE"}
_ALLOWED_QUALIFICATION_STATES = {"QUALIFIED", "UNQUALIFIED"}


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_refs(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of references")
    refs = tuple(_required_text(value, f"{name} reference") for value in values)
    if len(set(refs)) != len(refs):
        raise ValueError(f"{name} references must be unique")
    return tuple(sorted(refs))


@dataclass(frozen=True)
class VerifiedProgressionProjection:
    """Deterministic read-only view of evidence-supported progression state."""

    projection_id: str
    mission_id: str
    mission_state: str
    verification_verdict: str
    evidence_references: tuple[str, ...]
    capability_id: str
    capability_supported: bool
    current_qualification_state: str
    reviewer_authorization_required: bool
    locked_next_capabilities: tuple[str, ...]
    milestone_strike_stars: int
    milestone_strike_label: str
    projection_digest: str
    read_only: bool = True
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _required_text(self.projection_id, "projection_id")
        _required_text(self.mission_id, "mission_id")
        _required_text(self.mission_state, "mission_state")
        _required_text(self.capability_id, "capability_id")
        if self.verification_verdict not in _ALLOWED_VERDICTS:
            raise ValueError("invalid verification_verdict")
        if self.current_qualification_state not in _ALLOWED_QUALIFICATION_STATES:
            raise ValueError("invalid current_qualification_state")
        if not self.read_only:
            raise ValueError("read_only must remain true")
        if self.authority_granted:
            raise ValueError("authority_granted must remain false")
        if self.capability_supported and not self.reviewer_authorization_required:
            raise ValueError("supported capability requires reviewer authorization")
        _normalize_refs(self.evidence_references, "evidence_references")
        _normalize_refs(self.locked_next_capabilities, "locked_next_capabilities")

    @classmethod
    def build(
        cls,
        *,
        projection_id: str,
        mission_id: str,
        mission_state: str,
        evidence_references: Sequence[str],
        verification_verdict: str,
        capability_id: str,
        capability_supported: bool,
        current_qualification_state: str,
        locked_next_capabilities: Sequence[str],
    ) -> "VerifiedProgressionProjection":
        """Build a projection without mutating any supplied input."""
        refs = _normalize_refs(evidence_references, "evidence_references")
        locked = _normalize_refs(locked_next_capabilities, "locked_next_capabilities")
        if verification_verdict not in _ALLOWED_VERDICTS:
            raise ValueError("invalid verification_verdict")
        if current_qualification_state not in _ALLOWED_QUALIFICATION_STATES:
            raise ValueError("invalid current_qualification_state")

        # A capability is only supportable by a VERIFIED evaluation. The
        # projection can expose an explicit negative state but cannot promote
        # an unverified execution into a positive progression signal.
        effective_supported = bool(capability_supported and verification_verdict == "VERIFIED")
        reviewer_required = effective_supported
        payload = {
            "projection_version": PROJECTION_VERSION,
            "projection_id": _required_text(projection_id, "projection_id"),
            "mission_id": _required_text(mission_id, "mission_id"),
            "mission_state": _required_text(mission_state, "mission_state"),
            "verification_verdict": verification_verdict,
            "evidence_references": list(refs),
            "capability_id": _required_text(capability_id, "capability_id"),
            "capability_supported": effective_supported,
            "current_qualification_state": current_qualification_state,
            "reviewer_authorization_required": reviewer_required,
            "locked_next_capabilities": list(locked),
            "milestone_strike_stars": 0,
            "milestone_strike_label": "UNRATED",
            "read_only": True,
            "authority_granted": False,
        }

        # Calculate Milestone Strike Stars deterministically
        stars, label = cls._calculate_milestone_strike(
            verification_verdict=verification_verdict,
            evidence_references=refs,
            capability_supported=effective_supported,
            qualification_state=current_qualification_state,
        )
        payload["milestone_strike_stars"] = stars
        payload["milestone_strike_label"] = label

        digest = _canonical_digest(payload)
        return cls(
            projection_id=payload["projection_id"],
            mission_id=payload["mission_id"],
            mission_state=payload["mission_state"],
            verification_verdict=verification_verdict,
            evidence_references=refs,
            capability_id=payload["capability_id"],
            capability_supported=effective_supported,
            current_qualification_state=current_qualification_state,
            reviewer_authorization_required=reviewer_required,
            locked_next_capabilities=locked,
            milestone_strike_stars=stars,
            milestone_strike_label=label,
            projection_digest=digest,
        )

    @staticmethod
    def _calculate_milestone_strike(
        *,
        verification_verdict: str,
        evidence_references: tuple[str, ...],
        capability_supported: bool,
        qualification_state: str,
        safety_verified: bool = True,
    ) -> tuple[int, str]:
        """Derive deterministic Milestone Strike stars from evidence & verification state."""
        if not safety_verified or verification_verdict != "VERIFIED" or not evidence_references:
            return 0, "UNRATED"

        num_refs = len(evidence_references)
        if num_refs >= 10 and capability_supported and qualification_state == "QUALIFIED":
            return 5, "⭐⭐⭐⭐⭐ FRONTIER_BREAKTHROUGH"
        elif num_refs >= 5 and capability_supported:
            return 4, "⭐⭐⭐⭐ COMPOUND_ADVANCEMENT"
        elif num_refs >= 3:
            return 3, "⭐⭐⭐ MAJOR_ADVANCEMENT"
        elif num_refs >= 2:
            return 2, "⭐⭐ STRONG_PROGRESS"
        else:
            return 1, "⭐ MEANINGFUL_PROGRESS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_version": PROJECTION_VERSION,
            "projection_id": self.projection_id,
            "mission_id": self.mission_id,
            "mission_state": self.mission_state,
            "verification_verdict": self.verification_verdict,
            "evidence_references": list(self.evidence_references),
            "capability_id": self.capability_id,
            "capability_supported": self.capability_supported,
            "current_qualification_state": self.current_qualification_state,
            "reviewer_authorization_required": self.reviewer_authorization_required,
            "locked_next_capabilities": list(self.locked_next_capabilities),
            "milestone_strike_stars": self.milestone_strike_stars,
            "milestone_strike_label": self.milestone_strike_label,
            "projection_digest": self.projection_digest,
            "read_only": self.read_only,
            "authority_granted": self.authority_granted,
        }
