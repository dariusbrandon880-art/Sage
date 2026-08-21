"""Deterministic evidence-to-capability evaluation projection.

This module is intentionally zero-storage and non-authoritative. It consumes a
locked DecisionRecord plus externally supplied evidence verdicts and produces a
replayable evaluation receipt. It never mutates the capability registry,
qualification state, XP, authority, mission state, or archive.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from sage.decision_record import DecisionRecord

EVALUATOR_VERSION = "evidence-capability-evaluator-v0.1"
VERIFIED = "VERIFIED"
FALSIFIED = "FALSIFIED"
PENDING = "PENDING"
_ALLOWED_EVIDENCE_VERDICTS = {VERIFIED, FALSIFIED, PENDING}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _require_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True)
class CapabilityEvaluation:
    """Public, deterministic evaluation result; never a promotion command."""

    evaluation_id: str
    decision_id: str
    capability_ref: str
    verdict: str
    capability_delta: str
    evidence_verdicts: Mapping[str, str]
    unmet_requirements: tuple[str, ...]
    reviewer_required: bool
    evaluation_hash: str
    version: str = EVALUATOR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_version": self.version,
            "evaluation_id": self.evaluation_id,
            "decision_id": self.decision_id,
            "capability_ref": self.capability_ref,
            "verdict": self.verdict,
            "capability_delta": self.capability_delta,
            "evidence_verdicts": dict(self.evidence_verdicts),
            "unmet_requirements": list(self.unmet_requirements),
            "reviewer_required": self.reviewer_required,
            "evaluation_hash": self.evaluation_hash,
        }

    def serialize(self) -> str:
        return _canonical(self.to_dict())


class EvidenceCapabilityEvaluator:
    """Pure evaluator connecting DecisionRecord evidence to capability readiness."""

    def evaluate(
        self,
        decision: DecisionRecord,
        *,
        capability_ref: str,
        evidence_verdicts: Mapping[str, str],
        required_evidence_refs: Sequence[str] | None = None,
    ) -> CapabilityEvaluation:
        _require_text(capability_ref, "capability_ref")
        if not decision.verify_integrity():
            raise ValueError("decision integrity failed; capability evaluation is blocked")

        required = tuple(required_evidence_refs or decision.to_dict()["evidence_refs"])
        if len(required) != len(set(required)):
            raise ValueError("duplicate required evidence_ref is not allowed")
        decision_refs = set(decision.to_dict()["evidence_refs"])
        verdicts = dict(evidence_verdicts)
        for ref, status in verdicts.items():
            _require_text(ref, "evidence_ref")
            if status not in _ALLOWED_EVIDENCE_VERDICTS:
                raise ValueError(f"invalid evidence verdict: {status}")

        unmet: list[str] = []
        for ref in required:
            _require_text(ref, "evidence_ref")
            if ref not in decision_refs:
                unmet.append(f"UNBOUND:{ref}")
            elif verdicts.get(ref) != VERIFIED:
                status = verdicts.get(ref, PENDING)
                unmet.append(f"{status}:{ref}")

        resolution = decision.resolution
        if resolution is None:
            unmet.append("NO_RESOLUTION")
        elif resolution.verification_status != VERIFIED:
            unmet.append(f"RESOLUTION:{resolution.verification_status}")

        if unmet:
            verdict = "HOLD"
            capability_delta = "NO_CHANGE"
        else:
            verdict = "PROMOTION_CANDIDATE"
            capability_delta = "CANDIDATE_UP"

        payload = {
            "evaluation_version": EVALUATOR_VERSION,
            "decision_id": decision.to_dict()["decision_id"],
            "capability_ref": capability_ref,
            "verdict": verdict,
            "capability_delta": capability_delta,
            "evidence_verdicts": dict(sorted(verdicts.items())),
            "unmet_requirements": sorted(unmet),
            "reviewer_required": True,
        }
        digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
        evaluation_id = f"eval_{digest[:16]}"
        return CapabilityEvaluation(
            evaluation_id=evaluation_id,
            decision_id=decision.to_dict()["decision_id"],
            capability_ref=capability_ref,
            verdict=verdict,
            capability_delta=capability_delta,
            evidence_verdicts=_freeze(dict(sorted(verdicts.items()))),
            unmet_requirements=tuple(sorted(unmet)),
            reviewer_required=True,
            evaluation_hash=digest,
        )

    @staticmethod
    def verify(evaluation: CapabilityEvaluation) -> bool:
        payload = evaluation.to_dict()
        payload.pop("evaluation_id")
        payload.pop("evaluation_hash")
        return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest() == evaluation.evaluation_hash
