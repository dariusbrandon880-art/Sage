"""Governed observation-to-learning candidate projection."""
from __future__ import annotations
from dataclasses import dataclass
from .frontier_feedback import FeedbackOutcome, FrontierFeedback, classify_feedback
@dataclass(frozen=True)
class LearningCandidate:
    node_id:str; outcome:str; evidence_ref:str; next_action:str
def observe(node_id:str,outcome:FeedbackOutcome,evidence_ref:str)->LearningCandidate:
    classification=classify_feedback(FrontierFeedback(node_id,outcome,evidence_ref))
    return LearningCandidate(node_id,classification,evidence_ref,{"EVIDENCE_OBSERVED":"RETAIN","UNRESOLVED":"HOLD","FORBIDDEN_REGRESSION":"BLOCK"}[classification])
