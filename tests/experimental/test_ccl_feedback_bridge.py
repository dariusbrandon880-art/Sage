"""Tests for recovered CCL outcome feedback bridge."""
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge, CCLFeedbackRecord

def test_feedback_hash_integrity():
    r=CCLFeedbackRecord(record_id="r",mission_id="m",frontier_id="F4",target_namespace="sage/experimental/cognitive",outcome_status="PASS"); r.record_hash=r.compute_hash(); assert len(r.record_hash)==64 and r.record_hash==r.compute_hash()
def test_feedback_compounds_failure_history():
    e=AdaptiveMissionSelectionEngine(); b=CCLOutcomeFeedbackBridge(e); b.process_outcome("m1","F4","sage/experimental/cognitive","PASS"); assert not b.get_failure_history(); b.process_outcome("m2","F4","sage/experimental/cognitive","FAIL"); b.process_outcome("m3","F4","sage/experimental/cognitive","DRIFT_DETECTED"); b.process_outcome("m4","F4","sage/experimental/cognitive","FAIL"); failures=b.get_failure_history(); assert len(failures)==3; p=e.evaluate_candidate("retry","F4","sage/experimental/cognitive",failure_history=failures); assert not p.is_authorized and p.priority_score==.25
