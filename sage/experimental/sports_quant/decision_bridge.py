"""Bridge paper sports-quant decisions into governed SAGE autopsy learning.

The bridge is pure and research-only: it records decision-time market/model state,
binds a later paper outcome, and delegates regret attribution to the governed C2/SAGI
seams. It never places wagers, grants authority, or captures private reasoning.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Sequence

from sage.c2.decision_autopsy import (
    CounterfactualRecord,
    DecisionAutopsy,
    DecisionAutopsyEngine,
    DecisionRecord,
    OutcomeRecord,
)
from sage.experimental.sagi.regret import RegretAttributionEngine, RegretRecord
from .prediction import PropEdgeResult


@dataclass(frozen=True)
class SportsDecision:
    """Immutable paper decision with enough state to support later autopsy."""

    decision_id: str
    mission_id: str
    event_id: str
    decided_at_utc: str
    information_snapshot_hash: str
    chosen_selection: str
    chosen_projected_probability: float
    alternatives: tuple[tuple[str, float], ...]
    wagering_executed: bool = False

    def __post_init__(self) -> None:
        if not self.decision_id.strip() or any(ch.isspace() for ch in self.decision_id):
            raise ValueError("decision_id must be a non-empty reference without whitespace")
        if not self.mission_id.strip() or any(ch.isspace() for ch in self.mission_id):
            raise ValueError("mission_id must be a non-empty reference without whitespace")
        if not self.event_id.strip() or any(ch.isspace() for ch in self.event_id):
            raise ValueError("event_id must be a non-empty reference without whitespace")
        if not 0.0 <= self.chosen_projected_probability <= 1.0:
            raise ValueError("chosen_projected_probability must be between 0 and 1")
        if not self.alternatives:
            raise ValueError("at least one alternative is required for autopsy")
        if self.wagering_executed:
            raise ValueError("SHADOW_BOUNDARY_VIOLATION: wagering execution is prohibited")


def _reference_component(value: str) -> str:
    """Normalize human labels into deterministic reference-safe components."""
    normalized = re.sub(r"\s+", "_", value.strip())
    normalized = re.sub(r"[^A-Za-z0-9_.:-]", "_", normalized)
    return normalized


def _snapshot_hash(edge: PropEdgeResult, candidates: Sequence[PropEdgeResult]) -> str:
    payload = {
        "player": edge.player_name,
        "category": edge.prop_category,
        "selection": edge.selection,
        "fd_price": edge.fanduel_decimal_price,
        "fd_probability": edge.fanduel_implied_prob,
        "projected_probability": edge.projected_prob,
        "candidates": [
            {
                "selection": item.selection,
                "fd_price": item.fanduel_decimal_price,
                "projected_probability": item.projected_prob,
            }
            for item in candidates
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def build_sports_decision(
    edge: PropEdgeResult,
    alternatives: Sequence[PropEdgeResult],
    *,
    decision_id: str,
    mission_id: str,
    decided_at_utc: str,
) -> SportsDecision:
    """Create a locked paper decision from one chosen prop and alternatives."""
    if any(item.player_name != edge.player_name or item.prop_category != edge.prop_category for item in alternatives):
        raise ValueError("SPORTS_DECISION_SCOPE_VIOLATION: alternatives must share player and prop category")
    if any(item.selection == edge.selection for item in alternatives):
        raise ValueError("SPORTS_DECISION_ALTERNATIVE_DUPLICATE: chosen selection cannot be an alternative")
    snapshot_hash = _snapshot_hash(edge, alternatives)
    event_id = f"{_reference_component(edge.player_name)}_{_reference_component(edge.prop_category)}"
    return SportsDecision(
        decision_id=decision_id,
        mission_id=mission_id,
        event_id=event_id,
        decided_at_utc=decided_at_utc,
        information_snapshot_hash=snapshot_hash,
        chosen_selection=edge.selection,
        chosen_projected_probability=edge.projected_prob,
        alternatives=tuple((item.selection, item.projected_prob) for item in alternatives),
    )


def autopsy_sports_decision(
    decision: SportsDecision,
    edge: PropEdgeResult,
    *,
    outcome_id: str,
    observed_at_utc: str,
    actual_utility: float,
    attribution: str = "UNKNOWN",
    lesson: str = "Evaluate the paper decision against decision-time alternatives.",
) -> DecisionAutopsy:
    """Convert a paper sports decision and outcome into a governed autopsy."""
    if edge.selection != decision.chosen_selection:
        raise ValueError("SPORTS_DECISION_BINDING_VIOLATION: chosen selection does not match decision")
    decision_record = DecisionRecord(
        decision_id=decision.decision_id,
        mission_id=decision.mission_id,
        decided_at_utc=decision.decided_at_utc,
        information_snapshot_hash=decision.information_snapshot_hash,
        information_refs=(decision.information_snapshot_hash,),
        assumptions=("paper_prediction",),
        chosen_action=decision.chosen_selection,
        alternatives=tuple(selection for selection, _ in decision.alternatives),
        chosen_expected_utility=decision.chosen_projected_probability,
        alternative_expected_utilities=decision.alternatives,
        decision_confidence=edge.confidence_score,
    )
    outcome = OutcomeRecord(
        outcome_id=outcome_id,
        decision_id=decision.decision_id,
        observed_at_utc=observed_at_utc,
        actual_utility=actual_utility,
    )
    counterfactuals = tuple(
        CounterfactualRecord(action, utility, decision.information_snapshot_hash, decision.decided_at_utc)
        for action, utility in decision.alternatives
    )
    return DecisionAutopsyEngine().autopsy(
        decision_record,
        outcome,
        counterfactuals,
        attribution=attribution,
        lesson=lesson,
    )


def derive_sports_learning_signal(autopsy: DecisionAutopsy) -> RegretRecord:
    """Derive a bounded regret signal without mutating historical decision state."""
    return RegretAttributionEngine().derive(autopsy)
