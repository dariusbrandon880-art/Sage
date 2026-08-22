"""Bounded evidence feedback from longitudinal outcomes into Frontier Tree."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FeedbackOutcome(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"


@dataclass(frozen=True)
class FrontierFeedback:
    node_id: str
    outcome: FeedbackOutcome
    evidence_ref: str


def apply_feedback(tree, feedback: FrontierFeedback):
    if not feedback.evidence_ref:
        raise ValueError("feedback requires evidence reference")
    node = tree.get(feedback.node_id)
    if feedback.outcome is FeedbackOutcome.NEGATIVE_RESULT:
        tree.forbid(feedback.node_id, feedback.evidence_ref)
    elif feedback.outcome is FeedbackOutcome.HOLD:
        tree.hold(feedback.node_id, feedback.evidence_ref)
    else:
        tree.record_evidence(feedback.node_id, feedback.evidence_ref)
    return node
