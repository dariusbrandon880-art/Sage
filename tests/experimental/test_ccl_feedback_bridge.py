"""Tests for CCL Outcome Feedback Bridge."""

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge, CCLFeedbackRecord


def test_feedback_record_hash_integrity():
    record = CCLFeedbackRecord(record_id="fb", mission_id="m", frontier_id="F4", target_namespace="sage/experimental/cognitive", outcome_status="PASS")
    record.record_hash = record.compute_hash()
    assert len(record.record_hash) == 64
    assert record.record_hash == record.compute_hash()


def test_failure_history_closes_adaptive_loop():
    engine = AdaptiveMissionSelectionEngine()
    bridge = CCLOutcomeFeedbackBridge(selection_engine=engine)
    bridge.process_outcome("m-pass", "F4", "sage/experimental/cognitive", "PASS")
    assert bridge.get_failure_history() == []
    for mission_id, status in (("m-fail1", "FAIL"), ("m-fail2", "DRIFT_DETECTED"), ("m-fail3", "FAIL")):
        bridge.process_outcome(mission_id, "F4", "sage/experimental/cognitive", status)
    failures = bridge.get_failure_history()
    assert len(failures) == 3
    packet = engine.evaluate_candidate("cand-retry", "F4", "sage/experimental/cognitive", failure_history=failures)
    assert packet.is_authorized is False
    assert packet.priority_score == 0.25
