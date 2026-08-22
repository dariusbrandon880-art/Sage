"""Evidence Sufficiency v0.1 — deterministic, non-authoritative claim evaluation.

Evaluates whether an existing witnessed claim and its declared evidence satisfy
an explicitly supplied evidentiary burden. This module is pure composition:
no storage, authority mutation, qualification changes, network access, or
truth-by-signature assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Iterable, Optional, Tuple


class EvidenceSufficiencyValidationError(ValueError):
    """Raised when an evaluation request violates the fail-closed contract."""


class SufficiencyStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT = "INSUFFICIENT"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True)
class EvidenceAssessment:
    """One bounded evidence contribution to a claim evaluation."""

    evidence_ref: str
    supports: bool
    relevance: float = 1.0
    coverage: float = 1.0
    contradicts: bool = False
    independently_verified: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_ref, str) or not self.evidence_ref.strip():
            raise EvidenceSufficiencyValidationError("evidence_ref must be a non-empty string")
        for name, value in (("relevance", self.relevance), ("coverage", self.coverage)):
            if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                raise EvidenceSufficiencyValidationError(f"{name} must be between 0 and 1")
        if self.contradicts and self.supports:
            raise EvidenceSufficiencyValidationError("evidence cannot simultaneously support and contradict a claim")


@dataclass(frozen=True)
class EvidenceSufficiencyEvaluation:
    """Immutable evaluation receipt; never grants authority or mutates state."""

    claim_ref: str
    context_id: str
    intent_ref: str
    assessments: Tuple[EvidenceAssessment, ...]
    minimum_coverage: float = 1.0
    require_independent_witness: bool = False
    status: SufficiencyStatus = field(init=False)
    evaluation_digest: str = field(init=False)
    authority_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (self.claim_ref, self.context_id, self.intent_ref)):
            raise EvidenceSufficiencyValidationError("claim_ref, context_id, and intent_ref must be non-empty strings")
        if not isinstance(self.assessments, tuple):
            raise EvidenceSufficiencyValidationError("assessments must be an immutable tuple")
        if not self.assessments:
            raise EvidenceSufficiencyValidationError("at least one evidence assessment is required")
        if not 0.0 <= self.minimum_coverage <= 1.0:
            raise EvidenceSufficiencyValidationError("minimum_coverage must be between 0 and 1")
        object.__setattr__(self, "status", self._evaluate())
        object.__setattr__(self, "evaluation_digest", self._digest())

    @classmethod
    def evaluate(
        cls,
        *,
        claim_ref: str,
        context_id: str,
        intent_ref: str,
        assessments: Iterable[EvidenceAssessment],
        minimum_coverage: float = 1.0,
        require_independent_witness: bool = False,
    ) -> "EvidenceSufficiencyEvaluation":
        return cls(
            claim_ref=claim_ref,
            context_id=context_id,
            intent_ref=intent_ref,
            assessments=tuple(assessments),
            minimum_coverage=minimum_coverage,
            require_independent_witness=require_independent_witness,
        )

    def _evaluate(self) -> SufficiencyStatus:
        if any(a.contradicts for a in self.assessments):
            return SufficiencyStatus.CONTRADICTED
        if not self.assessments:
            return SufficiencyStatus.UNVERIFIABLE
        relevant = [a for a in self.assessments if a.supports]
        if not relevant:
            return SufficiencyStatus.UNVERIFIABLE
        weighted_coverage = sum(a.coverage * a.relevance for a in relevant) / len(relevant)
        if self.require_independent_witness and not any(a.independently_verified for a in relevant):
            return SufficiencyStatus.INSUFFICIENT if weighted_coverage < self.minimum_coverage else SufficiencyStatus.PARTIALLY_SUPPORTED
        if weighted_coverage >= self.minimum_coverage:
            return SufficiencyStatus.SUPPORTED
        return SufficiencyStatus.PARTIALLY_SUPPORTED

    def _canonical_payload(self) -> Dict[str, Any]:
        return {
            "assessments": [
                {
                    "contradicts": a.contradicts,
                    "coverage": a.coverage,
                    "evidence_ref": a.evidence_ref,
                    "independently_verified": a.independently_verified,
                    "relevance": a.relevance,
                    "supports": a.supports,
                }
                for a in sorted(self.assessments, key=lambda x: x.evidence_ref)
            ],
            "claim_ref": self.claim_ref,
            "context_id": self.context_id,
            "intent_ref": self.intent_ref,
            "minimum_coverage": self.minimum_coverage,
            "require_independent_witness": self.require_independent_witness,
            "status": self.status.value,
        }

    def _digest(self) -> str:
        canonical = json.dumps(self._canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        payload = self._canonical_payload()
        payload.update({"evaluation_digest": self.evaluation_digest, "authority_granted": False})
        return payload
