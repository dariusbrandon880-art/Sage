"""Regression coverage for frontier-selection capabilities recovered from #207."""
from sage.experimental.frontier_feedback import FeedbackOutcome, FrontierFeedback, classify_feedback
from sage.experimental.observation_learning import observe
from sage.experimental.pfc_decision_engine import PFCDecisionEngine
from sage.experimental.temporal_research_memory import TemporalResearchMemory

def test_feedback_and_observation_learning_fail_closed():
    assert classify_feedback(FrontierFeedback("F1",FeedbackOutcome.PASS,"receipt"))=="EVIDENCE_OBSERVED"
    assert observe("F1",FeedbackOutcome.HOLD,"receipt").next_action=="HOLD"
    assert observe("F1",FeedbackOutcome.NEGATIVE_RESULT,"receipt").next_action=="BLOCK"

def test_pfc_decision_is_pure_and_hashed():
    decision=PFCDecisionEngine().decide({"validated":True,"evidence_complete":True,"regression_free":True,"authorized":False,"evidence_refs":["r1"]})
    assert decision.action=="BUILD" and len(decision.state_hash)==64

def test_temporal_memory_is_deterministic():
    memory=TemporalResearchMemory(); memory.record("s1","2026-08-22",{"score":1},("r1",)); memory.record("s2","2026-08-23",{"score":2},("r2",))
    assert memory.compare("s1","s2")=={"score":(1,2)}
