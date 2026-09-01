"""Governed decision -> outcome -> autopsy -> counterfactual learning seam.

This module is deliberately deterministic and side-effect free. It preserves the
information boundary at decision time, separates decision quality from outcome
quality, and produces a learning candidate without promoting it to canonical
knowledge. It does not execute actions, grant authority, or capture private
reasoning.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Sequence


OUTCOME_LABELS = {"GOOD", "BAD", "UNKNOWN"}
DECISION_LABELS = {"GOOD_DECISION", "BAD_DECISION", "UNKNOWN_DECISION"}
CAUSALITY_LABELS = {
    "DECISION_ERROR",
    "VARIANCE",
    "INFORMATION_SHOCK",
    "ENVIRONMENT_SHIFT",
    "COORDINATION_FAILURE",
    "CONSTRAINT_FAILURE",
    "INSUFFICIENT_EVIDENCE",
    "UNKNOWN",
}


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _ref(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ch.isspace() for ch in value):
        raise ValueError(f"{field} must be a non-empty reference without whitespace")
    return value


def _probability(value: float, field: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return float(value)


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable point-in-time decision state used as the autopsy baseline."""

    decision_id: str
    mission_id: str
    decided_at_utc: str
    information_snapshot_hash: str
    information_refs: tuple[str, ...]
    assumptions: tuple[str, ...]
    chosen_action: str
    alternatives: tuple[str, ...]
    chosen_expected_utility: float
    alternative_expected_utilities: tuple[tuple[str, float], ...]
    decision_confidence: float

    def __post_init__(self) -> None:
        _ref(self.decision_id, "decision_id")
        _ref(self.mission_id, "mission_id")
        _ref(self.information_snapshot_hash, "information_snapshot_hash")
        _ref(self.chosen_action, "chosen_action")
        if not self.information_refs:
            raise ValueError("information_refs must not be empty")
        if len(self.information_refs) != len(set(self.information_refs)):
            raise ValueError("information_refs must be unique")
        if not self.alternatives:
            raise ValueError("alternatives must include at least one credible alternative")
        names = tuple(name for name, _ in self.alternative_expected_utilities)
        if set(names) != set(self.alternatives) or len(names) != len(set(names)):
            raise ValueError("alternative_expected_utilities must match alternatives exactly")
        _probability(self.decision_confidence, "decision_confidence")

    @property
    def state_hash(self) -> str:
        return hashlib.sha256(_canonical(self.to_dict()).encode()).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "mission_id": self.mission_id,
            "decided_at_utc": self.decided_at_utc,
            "information_snapshot_hash": self.information_snapshot_hash,
            "information_refs": list(self.information_refs),
            "assumptions": list(self.assumptions),
            "chosen_action": self.chosen_action,
            "alternatives": list(self.alternatives),
            "chosen_expected_utility": self.chosen_expected_utility,
            "alternative_expected_utilities": dict(self.alternative_expected_utilities),
            "decision_confidence": self.decision_confidence,
        }


@dataclass(frozen=True)
class CounterfactualRecord:
    """Alternative-path estimate constrained to the decision-time information state."""

    action: str
    expected_utility: float
    information_snapshot_hash: str
    information_cutoff_utc: str

    def __post_init__(self) -> None:
        _ref(self.action, "action")
        _ref(self.information_snapshot_hash, "information_snapshot_hash")
        if not self.information_cutoff_utc.strip():
            raise ValueError("information_cutoff_utc is required")


@dataclass(frozen=True)
class OutcomeRecord:
    """Observed post-decision result; it cannot rewrite the decision state."""

    outcome_id: str
    decision_id: str
    observed_at_utc: str
    actual_utility: float

    def __post_init__(self) -> None:
        _ref(self.outcome_id, "outcome_id")
        _ref(self.decision_id, "decision_id")
        if not self.observed_at_utc.strip():
            raise ValueError("observed_at_utc is required")


@dataclass(frozen=True)
class DecisionAutopsy:
    """Auditable classification of decision quality, outcome quality, and regret."""

    decision_id: str
    outcome_id: str
    decision_quality: str
    outcome_quality: str
    attribution: str
    chosen_expected_utility: float
    actual_utility: float
    best_alternative_action: str
    best_alternative_expected_utility: float
    regret: float
    counterfactuals: tuple[CounterfactualRecord, ...]
    lesson: str

    def __post_init__(self) -> None:
        _ref(self.decision_id, "decision_id")
        _ref(self.outcome_id, "outcome_id")
        if self.decision_quality not in DECISION_LABELS:
            raise ValueError("invalid decision_quality")
        if self.outcome_quality not in OUTCOME_LABELS:
            raise ValueError("invalid outcome_quality")
        if self.attribution not in CAUSALITY_LABELS:
            raise ValueError("invalid attribution")
        if self.regret < 0.0:
            raise ValueError("regret cannot be negative")
        if not self.counterfactuals:
            raise ValueError("at least one counterfactual is required")
        if not self.lesson.strip():
            raise ValueError("lesson is required")


class DecisionAutopsyEngine:
    """Construct an autopsy while enforcing the decision-time information boundary."""

    def autopsy(
        self,
        decision: DecisionRecord,
        outcome: OutcomeRecord,
        counterfactuals: Sequence[CounterfactualRecord],
        *,
        attribution: str = "UNKNOWN",
        lesson: str,
        outcome_tolerance: float = 0.0,
    ) -> DecisionAutopsy:
        if outcome.decision_id != decision.decision_id:
            raise ValueError("outcome decision_id does not match decision")
        if attribution not in CAUSALITY_LABELS:
            raise ValueError("invalid attribution")
        if outcome.observed_at_utc < decision.decided_at_utc:
            raise ValueError("outcome cannot precede decision")
        if outcome_tolerance < 0.0:
            raise ValueError("outcome_tolerance cannot be negative")

        counterfactuals = tuple(counterfactuals)
        expected_names = set(decision.alternatives)
        actual_names = {record.action for record in counterfactuals}
        if actual_names != expected_names:
            raise ValueError("counterfactuals must cover every decision-time alternative")
        if any(record.information_snapshot_hash != decision.information_snapshot_hash for record in counterfactuals):
            raise ValueError("counterfactual uses information outside the decision-time snapshot")
        if any(record.information_cutoff_utc != decision.decided_at_utc for record in counterfactuals):
            raise ValueError("counterfactual information cutoff must equal decision time")

        best = max(counterfactuals, key=lambda record: record.expected_utility)
        gap = best.expected_utility - decision.chosen_expected_utility
        if abs(gap) <= outcome_tolerance:
            decision_quality = "GOOD_DECISION"
        elif gap > outcome_tolerance:
            decision_quality = "BAD_DECISION"
        else:
            decision_quality = "GOOD_DECISION"

        if outcome.actual_utility > decision.chosen_expected_utility + outcome_tolerance:
            outcome_quality = "GOOD"
        elif outcome.actual_utility < decision.chosen_expected_utility - outcome_tolerance:
            outcome_quality = "BAD"
        else:
            outcome_quality = "UNKNOWN"

        if decision_quality == "GOOD_DECISION" and outcome_quality == "BAD":
            final_attribution = "VARIANCE" if attribution == "UNKNOWN" else attribution
        elif decision_quality == "BAD_DECISION" and outcome_quality == "GOOD":
            final_attribution = "DECISION_ERROR" if attribution == "UNKNOWN" else attribution
        else:
            final_attribution = attribution

        return DecisionAutopsy(
            decision_id=decision.decision_id,
            outcome_id=outcome.outcome_id,
            decision_quality=decision_quality,
            outcome_quality=outcome_quality,
            attribution=final_attribution,
            chosen_expected_utility=decision.chosen_expected_utility,
            actual_utility=outcome.actual_utility,
            best_alternative_action=best.action,
            best_alternative_expected_utility=best.expected_utility,
            regret=max(0.0, gap),
            counterfactuals=counterfactuals,
            lesson=lesson,
        )


def classify_outcome_without_decision_hindsight(
    decision: DecisionRecord, outcome: OutcomeRecord
) -> str:
    """Small pure helper for outcome classification against the locked expectation."""
    if outcome.decision_id != decision.decision_id:
        raise ValueError("outcome decision_id does not match decision")
    if outcome.observed_at_utc < decision.decided_at_utc:
        raise ValueError("outcome cannot precede decision")
    if outcome.actual_utility > decision.chosen_expected_utility:
        return "GOOD"
    if outcome.actual_utility < decision.chosen_expected_utility:
        return "BAD"
    return "UNKNOWN"
