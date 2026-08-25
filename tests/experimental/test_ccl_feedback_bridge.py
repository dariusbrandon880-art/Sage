"""Tests for Cognitive Causal Learning (CCL) Outcome Feedback Bridge."""

import pytest
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.experimental.cognitive.ccl_feedback_bridge import (
    CCLOutcomeFeedbackBridge,
    CCLFeedbackRecord,
)


def test_ccl_feedback_record_hash_integrity():
    record = CCLFeedbackRecord(
        record_id="fb-001",
        mission_id="m-001",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        outcome_status="PASS",
    )
    record.record_hash = record.compute_hash()
    assert len(record.record_hash) == 64
    assert record.record_hash == record.compute_hash()


def test_ccl_outcome_feedback_bridge_closed_loop():
    engine = AdaptiveMissionSelectionEngine()
    bridge = CCLOutcomeFeedbackBridge(selection_engine=engine)

    # 1. Process PASS outcome
    r1 = bridge.process_outcome(
        mission_id="m-pass",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        outcome_status="PASS",
    )
    assert r1.outcome_status == "PASS"
    assert len(bridge.get_failure_history()) == 0

    # 2. Process FAIL and DRIFT_DETECTED outcomes
    bridge.process_outcome(
        mission_id="m-fail1",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        outcome_status="FAIL",
    )
    bridge.process_outcome(
        mission_id="m-fail2",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        outcome_status="DRIFT_DETECTED",
    )
    bridge.process_outcome(
        mission_id="m-fail3",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        outcome_status="FAIL",
    )

    failures = bridge.get_failure_history()
    assert len(failures) == 3

    # 3. Evaluate candidate using accumulated feedback
    packet = engine.evaluate_candidate(
        candidate_id="cand-retry",
        frontier_id="F4",
        target_namespace="sage/experimental/cognitive",
        failure_history=failures,
    )

    assert packet.is_authorized is False
    assert packet.priority_score == 0.25
