from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge


def test_reconciled_outcome_boosts_score():
    bridge = CCLOutcomeFeedbackBridge(AdaptiveMissionSelectionEngine())
    reconciliation = OutcomeReconciliation.reconcile(decision_id="dec-100", context_id="ctx-100", t0_claim_ref="claim-100", t1_observation_ref="obs-100", reality_gap_assessment_ref="rg-100", outcome_ref="out-100", status=OutcomeReconciliationStatus.RECONCILED, rationale="Reconciled successfully")
    packet, receipt = bridge.apply_outcome_feedback(reconciliation, "cand-100", "sage/experimental/cognitive/ccl_feedback_bridge.py", 10.0)
    assert packet.rank_score == 12.0
    assert receipt.feedback_applied is True and len(receipt.receipt_hash) == 64
