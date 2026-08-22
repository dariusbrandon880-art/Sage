"""Governed observation-to-learning candidate projection."""
from __future__ import annotations
from dataclasses import dataclass
from .frontier_feedback import FeedbackOutcome, FrontierFeedback, classify_feedback

@dataclass(frozen=True)
class LearningCandidate:
    node_id: str
    outcome: str
    evidence_ref: str
    next_action: str

def observe(node_id: str, outcome: FeedbackOutcome, evidence_ref: str) -> LearningCandidate:
    feedback=FrontierFeedback(node_id,outcome,evidence_ref)
    classification=classify_feedback(feedback)
    next_action={"EVIDENCE_OBSERVED":"RETAIN","UNRESOLVED":"HOLD","FORBIDDEN_REGRESSION":"BLOCK"}[classification]
    return LearningCandidate(node_id,classification,evidence_ref,next_action)
