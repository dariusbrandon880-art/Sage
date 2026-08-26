"""Bounded evidence feedback; no mutation of canonical frontier authority."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class FeedbackOutcome(str,Enum): PASS="PASS"; HOLD="HOLD"; NEGATIVE_RESULT="NEGATIVE_RESULT"
@dataclass(frozen=True)
class FrontierFeedback:
    node_id:str; outcome:FeedbackOutcome; evidence_ref:str
def classify_feedback(feedback:FrontierFeedback)->str:
    if not feedback.node_id or not feedback.evidence_ref: raise ValueError("MISSING_FEEDBACK_PROVENANCE")
    if feedback.outcome is FeedbackOutcome.NEGATIVE_RESULT:return "FORBIDDEN_REGRESSION"
    if feedback.outcome is FeedbackOutcome.HOLD:return "UNRESOLVED"
    return "EVIDENCE_OBSERVED"
