"""Governed technique-learning boundary for GPT/C2 self-improvement.

This module turns observed execution experience into a measurable, immutable
technique candidate and a validation posture. It deliberately does not mutate
model behavior, grant authority, persist state, or promote capability.

The design follows SAGE's existing evidence and causal-learning primitives:
reconciliation establishes lineage, independent observation establishes effect,
and this boundary evaluates whether a proposed operating technique has enough
replicated evidence to be considered for review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import ClassVar


class TechniqueLearningValidationError(ValueError):
    """Raised when a technique candidate or evaluation violates its contract."""


class TechniqueValidationVerdict(str, Enum):
    """Non-authoritative validation posture for a technique candidate."""

    HOLD = "HOLD"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"


@dataclass(frozen=True)
class TechniqueCandidate:
    """Immutable description of a proposed way of operating C2."""

    technique_id: str
    mission_class: str
    preconditions: tuple[str, ...]
    execution_technique: str
    expected_mechanism: str
    observed_result: str
    evidence_refs: tuple[str, ...]
    failure_modes: tuple[str, ...]
    cost_risk_notes: str
    counterexamples: tuple[str, ...] = ()
    authority_granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        for name in (
            "technique_id",
            "mission_class",
            "execution_technique",
            "expected_mechanism",
            "observed_result",
            "cost_risk_notes",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise TechniqueLearningValidationError(
                    f"{name} must be a non-empty string."
                )
        for name in (
            "preconditions",
            "evidence_refs",
            "failure_modes",
            "counterexamples",
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise TechniqueLearningValidationError(f"{name} must be a tuple.")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise TechniqueLearningValidationError(
                    f"{name} must contain only non-empty strings."
                )
        if not self.evidence_refs:
            raise TechniqueLearningValidationError("evidence_refs must not be empty.")

    @property
    def technique_digest(self) -> str:
        """Return deterministic identity for the technique evidence envelope."""
        payload = {
            "cost_risk_notes": self.cost_risk_notes,
            "counterexamples": list(self.counterexamples),
            "execution_technique": self.execution_technique,
            "expected_mechanism": self.expected_mechanism,
            "evidence_refs": list(self.evidence_refs),
            "failure_modes": list(self.failure_modes),
            "mission_class": self.mission_class,
            "observed_result": self.observed_result,
            "preconditions": list(self.preconditions),
            "technique_id": self.technique_id,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "technique_id": self.technique_id,
            "mission_class": self.mission_class,
            "preconditions": list(self.preconditions),
            "execution_technique": self.execution_technique,
            "expected_mechanism": self.expected_mechanism,
            "observed_result": self.observed_result,
            "evidence_refs": list(self.evidence_refs),
            "failure_modes": list(self.failure_modes),
            "cost_risk_notes": self.cost_risk_notes,
            "counterexamples": list(self.counterexamples),
            "technique_digest": self.technique_digest,
            "authority_granted": self.authority_granted,
        }


@dataclass(frozen=True)
class TechniqueValidation:
    """Immutable comparison of replicated technique outcomes.

    ``baseline_score`` and ``technique_score`` are caller-defined metrics. The
    boundary never assumes what a score means; callers must supply the metric
    definition and evidence references. A positive delta alone is insufficient:
    minimum replication and evidence requirements also apply.
    """

    technique_digest: str
    metric_definition: str
    baseline_score: float
    technique_score: float
    replication_count: int
    independent_evidence_refs: tuple[str, ...]
    counterexample_count: int = 0
    minimum_replications: int = 3
    verdict: TechniqueValidationVerdict = field(init=False)
    authority_granted: bool = field(default=False, init=False)
    reviewer_authorization_required: bool = field(default=True, init=False)

    MINIMUM_REPLICATION_FLOOR: ClassVar[int] = 2

    def __post_init__(self) -> None:
        if not isinstance(self.technique_digest, str) or not self.technique_digest.strip():
            raise TechniqueLearningValidationError("technique_digest must be non-empty.")
        if not isinstance(self.metric_definition, str) or not self.metric_definition.strip():
            raise TechniqueLearningValidationError("metric_definition must be non-empty.")
        for name in ("baseline_score", "technique_score"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TechniqueLearningValidationError(f"{name} must be numeric.")
        if self.replication_count < self.MINIMUM_REPLICATION_FLOOR:
            raise TechniqueLearningValidationError(
                f"replication_count must be >= {self.MINIMUM_REPLICATION_FLOOR}."
            )
        if self.minimum_replications < self.MINIMUM_REPLICATION_FLOOR:
            raise TechniqueLearningValidationError(
                f"minimum_replications must be >= {self.MINIMUM_REPLICATION_FLOOR}."
            )
        if self.replication_count < self.minimum_replications:
            raise TechniqueLearningValidationError(
                "replication_count must meet minimum_replications."
            )
        if self.counterexample_count < 0:
            raise TechniqueLearningValidationError("counterexample_count cannot be negative.")
        if not isinstance(self.independent_evidence_refs, tuple) or not self.independent_evidence_refs:
            raise TechniqueLearningValidationError(
                "independent_evidence_refs must be a non-empty tuple."
            )
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.independent_evidence_refs):
            raise TechniqueLearningValidationError(
                "independent_evidence_refs must contain only non-empty strings."
            )
        object.__setattr__(
            self,
            "verdict",
            TechniqueValidationVerdict.READY_FOR_REVIEW
            if self.technique_score > self.baseline_score and self.counterexample_count == 0
            else TechniqueValidationVerdict.HOLD,
        )

    @property
    def delta(self) -> float:
        return self.technique_score - self.baseline_score

    @property
    def validation_digest(self) -> str:
        payload = {
            "baseline_score": self.baseline_score,
            "counterexample_count": self.counterexample_count,
            "independent_evidence_refs": list(self.independent_evidence_refs),
            "metric_definition": self.metric_definition,
            "minimum_replications": self.minimum_replications,
            "replication_count": self.replication_count,
            "technique_digest": self.technique_digest,
            "technique_score": self.technique_score,
            "verdict": self.verdict.value,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "technique_digest": self.technique_digest,
            "metric_definition": self.metric_definition,
            "baseline_score": self.baseline_score,
            "technique_score": self.technique_score,
            "delta": self.delta,
            "replication_count": self.replication_count,
            "minimum_replications": self.minimum_replications,
            "independent_evidence_refs": list(self.independent_evidence_refs),
            "counterexample_count": self.counterexample_count,
            "verdict": self.verdict.value,
            "validation_digest": self.validation_digest,
            "authority_granted": self.authority_granted,
            "reviewer_authorization_required": self.reviewer_authorization_required,
        }
