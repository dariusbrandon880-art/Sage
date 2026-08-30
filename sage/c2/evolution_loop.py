"""Bounded SAGE evolution loop primitives.

This module connects existing observation, experimentation, evidence, validation,
and capability-warehouse concepts without granting autonomous promotion authority.
It is deliberately an evaluation/recommendation layer: callers must provide
observations and an external authority remains responsible for promotion.
"""
from __future__ import annotations

from enum import Enum
from typing import Mapping

from pydantic import BaseModel, Field, model_validator


class EvolutionDecision(str, Enum):
    """Evaluation outcome; never an authorization to mutate production state."""

    PROMOTE_CANDIDATE = "PROMOTE_CANDIDATE"
    HOLD = "HOLD"
    REJECT = "REJECT"


class FitnessVector(BaseModel):
    """Normalized evidence dimensions used to compare operating techniques."""

    mission_value: float = Field(ge=0.0, le=1.0)
    correctness: float = Field(ge=0.0, le=1.0)
    repeatability: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    recovery: float = Field(ge=0.0, le=1.0)
    generalization: float = Field(ge=0.0, le=1.0)
    cost: float = Field(gt=0.0, le=1.0)

    def score(self) -> float:
        """Return a transparent scalar for ranking only; vector dimensions remain authoritative."""
        numerator = (
            self.mission_value
            * self.correctness
            * self.repeatability
            * self.evidence_quality
            * self.recovery
            * self.generalization
        )
        return numerator / self.cost


class EvolutionBaseline(BaseModel):
    """Baseline used to prevent an experiment from declaring improvement in isolation."""

    technique_id: str
    trials: int = Field(ge=1)
    fitness: FitnessVector


class EvolutionCandidate(BaseModel):
    """A measured alternative operating technique."""

    technique_id: str
    trials: int = Field(ge=1)
    fitness: FitnessVector
    replicated: bool = False
    adversarially_challenged: bool = False
    regression_free: bool = False
    evidence_complete: bool = False
    human_reviewed: bool = False

    @model_validator(mode="after")
    def require_evidence_for_review(self) -> "EvolutionCandidate":
        if self.human_reviewed and not self.evidence_complete:
            raise ValueError("human_reviewed requires evidence_complete")
        return self


class EvolutionEvaluation(BaseModel):
    """Evaluation record produced by the bounded loop."""

    mission_id: str
    baseline: EvolutionBaseline
    candidates: list[EvolutionCandidate]
    winner: str | None = None
    decision: EvolutionDecision
    reason: str
    ranked_scores: Mapping[str, float]

    @property
    def promotion_authorized(self) -> bool:
        """Always false: evaluation can recommend, but cannot authorize promotion."""
        return False


class EvolutionLoop:
    """Compare bounded experiments and emit a fail-closed recommendation."""

    def __init__(self, minimum_improvement: float = 0.05):
        if minimum_improvement < 0:
            raise ValueError("minimum_improvement must be non-negative")
        self.minimum_improvement = minimum_improvement

    def evaluate(
        self,
        mission_id: str,
        baseline: EvolutionBaseline,
        candidates: list[EvolutionCandidate],
    ) -> EvolutionEvaluation:
        if not candidates:
            return EvolutionEvaluation(
                mission_id=mission_id,
                baseline=baseline,
                candidates=[],
                decision=EvolutionDecision.HOLD,
                reason="No candidate technique supplied.",
                ranked_scores={},
            )

        ranked = {candidate.technique_id: candidate.fitness.score() for candidate in candidates}
        winner = max(candidates, key=lambda candidate: candidate.fitness.score())
        baseline_score = baseline.fitness.score()
        winner_score = winner.fitness.score()
        improvement = (winner_score / baseline_score) - 1.0 if baseline_score else float("inf")

        gates_pass = all(
            (
                winner.replicated,
                winner.adversarially_challenged,
                winner.regression_free,
                winner.evidence_complete,
                winner.human_reviewed,
            )
        )

        if not gates_pass:
            decision = EvolutionDecision.HOLD
            reason = "Winner lacks one or more replication, adversarial, regression, evidence, or human-review gates."
        elif improvement < self.minimum_improvement:
            decision = EvolutionDecision.HOLD
            reason = f"Measured improvement {improvement:.3f} is below threshold {self.minimum_improvement:.3f}."
        else:
            decision = EvolutionDecision.PROMOTE_CANDIDATE
            reason = f"Candidate exceeds baseline by {improvement:.3f}; external promotion authority is still required."

        return EvolutionEvaluation(
            mission_id=mission_id,
            baseline=baseline,
            candidates=candidates,
            winner=winner.technique_id,
            decision=decision,
            reason=reason,
            ranked_scores=ranked,
        )
