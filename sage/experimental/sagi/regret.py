"""Governed regret and outcome-attribution seam for the SAGE organism.

This module converts an already-validated decision autopsy into a bounded learning
signal. It distinguishes avoidable decision regret from outcome variance and other
causal classes without capturing private reasoning or executing actions.
"""
from __future__ import annotations

from dataclasses import dataclass

from sage.c2.decision_autopsy import DecisionAutopsy, CAUSALITY_LABELS


REGRET_CLASSES = {
    "NO_REGRET",
    "DECISION_REGRET",
    "VARIANCE_REGRET",
    "INFORMATION_SHOCK_REGRET",
    "ENVIRONMENT_SHIFT_REGRET",
    "COORDINATION_REGRET",
    "CONSTRAINT_REGRET",
    "INSUFFICIENT_EVIDENCE_REGRET",
    "UNKNOWN_REGRET",
}


@dataclass(frozen=True)
class RegretRecord:
    """Immutable learning signal derived from a validated decision autopsy."""

    decision_id: str
    outcome_id: str
    regret: float
    regret_class: str
    attribution: str
    avoidable: bool
    counterfactual_gap: float
    learning_signal: str

    def __post_init__(self) -> None:
        if not self.decision_id.strip() or any(ch.isspace() for ch in self.decision_id):
            raise ValueError("decision_id must be a non-empty reference without whitespace")
        if not self.outcome_id.strip() or any(ch.isspace() for ch in self.outcome_id):
            raise ValueError("outcome_id must be a non-empty reference without whitespace")
        if self.regret < 0.0:
            raise ValueError("regret cannot be negative")
        if self.counterfactual_gap < 0.0:
            raise ValueError("counterfactual_gap cannot be negative")
        if self.regret_class not in REGRET_CLASSES:
            raise ValueError("invalid regret_class")
        if self.attribution not in CAUSALITY_LABELS:
            raise ValueError("invalid attribution")
        if not self.learning_signal.strip():
            raise ValueError("learning_signal is required")


class RegretAttributionEngine:
    """Map autopsy evidence into a conservative, reusable regret signal."""

    _CLASS_BY_ATTRIBUTION = {
        "DECISION_ERROR": "DECISION_REGRET",
        "VARIANCE": "VARIANCE_REGRET",
        "INFORMATION_SHOCK": "INFORMATION_SHOCK_REGRET",
        "ENVIRONMENT_SHIFT": "ENVIRONMENT_SHIFT_REGRET",
        "COORDINATION_FAILURE": "COORDINATION_REGRET",
        "CONSTRAINT_FAILURE": "CONSTRAINT_REGRET",
        "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE_REGRET",
        "UNKNOWN": "UNKNOWN_REGRET",
    }

    def derive(self, autopsy: DecisionAutopsy) -> RegretRecord:
        if autopsy.regret == 0.0:
            regret_class = "NO_REGRET"
            avoidable = False
        else:
            regret_class = self._CLASS_BY_ATTRIBUTION[autopsy.attribution]
            avoidable = autopsy.attribution == "DECISION_ERROR"

        gap = max(
            0.0,
            autopsy.best_alternative_expected_utility - autopsy.chosen_expected_utility,
        )
        if avoidable:
            signal = "REVIEW_DECISION_HEURISTIC"
        elif regret_class == "VARIANCE_REGRET":
            signal = "PRESERVE_DECISION_POLICY; UPDATE_VARIANCE_MEMORY"
        elif regret_class == "INFORMATION_SHOCK_REGRET":
            signal = "UPDATE_INFORMATION_REQUIREMENTS"
        elif regret_class == "ENVIRONMENT_SHIFT_REGRET":
            signal = "UPDATE_ENVIRONMENT_MODEL"
        elif regret_class == "COORDINATION_REGRET":
            signal = "UPDATE_COORDINATION_BOUNDARY"
        elif regret_class == "CONSTRAINT_REGRET":
            signal = "UPDATE_CONSTRAINT_MODEL"
        elif regret_class == "INSUFFICIENT_EVIDENCE_REGRET":
            signal = "RAISE_EVIDENCE_THRESHOLD"
        elif regret_class == "UNKNOWN_REGRET":
            signal = "RETAIN_UNCERTAINTY; REQUEST_EVIDENCE"
        else:
            signal = "NO_LEARNING_DELTA"

        return RegretRecord(
            decision_id=autopsy.decision_id,
            outcome_id=autopsy.outcome_id,
            regret=autopsy.regret,
            regret_class=regret_class,
            attribution=autopsy.attribution,
            avoidable=avoidable,
            counterfactual_gap=gap,
            learning_signal=signal,
        )
