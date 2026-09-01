"""Governed metacognitive state for SAGI decision quality.

This is an experimental, side-effect-free substrate. It records explicit
confidence dimensions and risk regulation without simulating emotion,
consciousness, or private reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class MetacognitiveState:
    """Immutable snapshot of explicit self-monitoring signals."""

    knowledge_confidence: float
    inference_confidence: float
    decision_confidence: float
    outcome_confidence: float
    risk_tolerance: float
    risk_score: float
    calibration_error: float = 0.0
    degraded: bool = False
    unknowns: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "knowledge_confidence",
            "inference_confidence",
            "decision_confidence",
            "outcome_confidence",
            "risk_tolerance",
            "risk_score",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.calibration_error < 0.0:
            raise ValueError("calibration_error cannot be negative")
        if len(self.unknowns) != len(set(self.unknowns)):
            raise ValueError("unknowns must be unique")
        if len(self.assumptions) != len(set(self.assumptions)):
            raise ValueError("assumptions must be unique")

    @property
    def composite_confidence(self) -> float:
        """Conservative confidence: weakest link controls the aggregate."""
        return min(
            self.knowledge_confidence,
            self.inference_confidence,
            self.decision_confidence,
        )

    @property
    def uncertainty(self) -> float:
        return 1.0 - self.composite_confidence

    @property
    def risk_regulation_score(self) -> float:
        """Distance between assessed risk and permitted risk tolerance."""
        return max(0.0, self.risk_score - self.risk_tolerance)

    @property
    def requires_review(self) -> bool:
        return self.degraded or bool(self.unknowns) or self.risk_regulation_score > 0.0

    def with_outcome(self, actual_quality: float) -> "MetacognitiveState":
        if not 0.0 <= actual_quality <= 1.0:
            raise ValueError("actual_quality must be between 0 and 1")
        error = abs(self.decision_confidence - actual_quality)
        return replace(
            self,
            outcome_confidence=actual_quality,
            calibration_error=error,
        )


@dataclass(frozen=True)
class MetacognitiveAssessment:
    """Bounded recommendation generated from a metacognitive snapshot."""

    state: MetacognitiveState
    action_allowed: bool
    review_required: bool
    reasons: tuple[str, ...]


class MetacognitiveEngine:
    """Evaluate confidence, uncertainty, degradation, and risk without acting."""

    def assess(self, state: MetacognitiveState) -> MetacognitiveAssessment:
        reasons: list[str] = []
        if state.knowledge_confidence < 0.5:
            reasons.append("low knowledge confidence")
        if state.inference_confidence < 0.5:
            reasons.append("low inference confidence")
        if state.decision_confidence < 0.5:
            reasons.append("low decision confidence")
        if state.unknowns:
            reasons.append("unresolved unknowns")
        if state.assumptions:
            reasons.append("active assumptions")
        if state.degraded:
            reasons.append("degraded capability")
        if state.risk_regulation_score > 0.0:
            reasons.append("risk exceeds tolerance")
        review_required = bool(reasons)
        return MetacognitiveAssessment(
            state=state,
            action_allowed=not review_required,
            review_required=review_required,
            reasons=tuple(reasons),
        )
