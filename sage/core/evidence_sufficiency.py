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
    def evaluate(cls, *, claim_ref: str, context_id: str, intent_ref: str, assessments: Iterable[EvidenceAssessment], minimum_coverage: float = 1.0, require_independent_witness: bool = False) -> "EvidenceSufficiencyEvaluation":
        return cls(claim_ref=claim_ref, context_id=context_id, intent_ref=intent_ref, assessments=tuple(assessments), minimum_coverage=minimum_coverage, require_independent_witness=require_independent_witness)

    def _evaluate(self) -> SufficiencyStatus:
        if any(a.contradicts for a in self.assessments):
            return SufficiencyStatus.CONTRADICTED
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
        return {"assessments": [{"contradicts": a.contradicts, "coverage": a.coverage, "evidence_ref": a.evidence_ref, "independently_verified": a.independently_verified, "relevance": a.relevance, "supports": a.supports} for a in sorted(self.assessments, key=lambda x: x.evidence_ref)], "claim_ref": self.claim_ref, "context_id": self.context_id, "intent_ref": self.intent_ref, "minimum_coverage": self.minimum_coverage, "require_independent_witness": self.require_independent_witness, "status": self.status.value}

    def _digest(self) -> str:
        canonical = json.dumps(self._canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        payload = self._canonical_payload()
        payload.update({"evaluation_digest": self.evaluation_digest, "authority_granted": False})
        return payload


class WitnessSufficiencyEvaluator:
    """Pure bridge from witnessed decisions to epistemic sufficiency.

    Uses only the public shape of DecisionRecord and WitnessBinding so the
    evaluator can be stacked onto either primitive without creating storage,
    transport, or authority coupling.
    """

    @staticmethod
    def evaluate_witnessed_decision(decision_record: Any, witness_binding: Any, declared_intent: str, required_burden: str = "STRICT_DIRECT_PROOF", *, independent_witness: bool = False, signature_verified: Optional[bool] = None) -> EvidenceSufficiencyEvaluation:
        if not isinstance(declared_intent, str) or not declared_intent.strip():
            raise EvidenceSufficiencyValidationError("declared_intent must be a non-empty string")
        if required_burden not in {"STRICT_DIRECT_PROOF", "STANDARD_SUPPORT", "EXPLORATORY"}:
            raise EvidenceSufficiencyValidationError(f"unsupported evidentiary burden: {required_burden}")

        decision_context = getattr(decision_record, "context_id", None)
        witness_context = getattr(witness_binding, "context_id", None)
        decision_id = getattr(decision_record, "decision_id", None)
        evidence_refs = tuple(getattr(decision_record, "evidence_refs", ()) or ())
        witness_ref = getattr(witness_binding, "evidence_ref", None)
        witness_status = getattr(witness_binding, "verification_status", "WITNESS_VERIFIED")

        if not all(isinstance(v, str) and v.strip() for v in (decision_context, witness_context, decision_id)):
            raise EvidenceSufficiencyValidationError("decision and witness must expose non-empty context/identity fields")
        if witness_ref not in evidence_refs:
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=witness_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref or "missing-witness-ref", supports=False)])
        if decision_context != witness_context:
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=witness_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref, supports=False, contradicts=True)])

        integrity = getattr(decision_record, "verify_integrity", None)
        if callable(integrity) and not integrity():
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=decision_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref, supports=False, contradicts=True)])

        if witness_status != "WITNESS_VERIFIED":
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=decision_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref, supports=False)])

        if signature_verified is False:
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=decision_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref, supports=False, contradicts=True)])
        if signature_verified is not True:
            return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=decision_context, intent_ref=declared_intent, assessments=[EvidenceAssessment(witness_ref, supports=False)])

        coverage = 1.0 if required_burden != "STRICT_DIRECT_PROOF" else 0.5
        assessment = EvidenceAssessment(evidence_ref=witness_ref, supports=True, coverage=coverage, relevance=1.0, independently_verified=independent_witness)
        minimum = 1.0 if required_burden != "EXPLORATORY" else 0.5
        return EvidenceSufficiencyEvaluation.evaluate(claim_ref=decision_id, context_id=decision_context, intent_ref=declared_intent, assessments=[assessment], minimum_coverage=minimum, require_independent_witness=(required_burden == "STRICT_DIRECT_PROOF"))
