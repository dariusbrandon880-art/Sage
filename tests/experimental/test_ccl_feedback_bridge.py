"""Unit tests for Closed-Loop CCL Outcome Feedback Bridge."""

import pytest
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge


def test_ccl_feedback_bridge_positive_outcome():
    engine = AdaptiveMissionSelectionEngine()
    bridge = CCLOutcomeFeedbackBridge(mission_selection_engine=engine)

    reconciliation = OutcomeReconciliation.reconcile(
        decision_id="dec-100",
        context_id="ctx-100",
        t0_claim_ref="claim-100",
        t1_observation_ref="obs-100",
        reality_gap_assessment_ref="rg-100",
        outcome_ref="out-100",
        status=OutcomeReconciliationStatus.RECONCILED,
        rationale="Reconciled successfully",
    )

    packet, rcpt = bridge.apply_outcome_feedback(
        reconciliation=reconciliation,
        candidate_id="cand-100",
        target="sage/experimental/cognitive/ccl_feedback_bridge.py",
        base_priority=10.0,
    )

    assert packet.rank_score == 12.0  # 10.0 * 1.2
    assert rcpt.feedback_applied is True
    assert len(rcpt.receipt_hash) == 64
