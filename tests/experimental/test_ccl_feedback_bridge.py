from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge
from sage.experimental.cognitive.flight_evidence_feedback import SAGIEvidenceFeedback, project_flight_evidence
from sage.experimental.longitudinal_capability import CapabilityEvaluationReceipt, CapabilityVerdict


def test_reconciled_outcome_boosts_score():
    bridge = CCLOutcomeFeedbackBridge(AdaptiveMissionSelectionEngine())
    reconciliation = OutcomeReconciliation.reconcile(decision_id="dec-100", context_id="ctx-100", t0_claim_ref="claim-100", t1_observation_ref="obs-100", reality_gap_assessment_ref="rg-100", outcome_ref="out-100", status=OutcomeReconciliationStatus.RECONCILED, rationale="Reconciled successfully")
    packet, receipt = bridge.apply_outcome_feedback(reconciliation, "cand-100", "sage/experimental/cognitive/ccl_feedback_bridge.py", 10.0)
    assert packet.rank_score == 12.0
    assert receipt.feedback_applied is True and len(receipt.receipt_hash) == 64


def test_flight_evidence_feedback_projection_pass_and_negative():
    pass_receipt = CapabilityEvaluationReceipt(
        evaluation_id="eval-pass",
        mission_set_id="ms-pass",
        plan_hash="plan-hash-pass",
        baseline_metrics=(),
        sage_metrics=(),
        relative_success_gain=0.5,
        recovery_rate=1.0,
        regression_rate=0.0,
        verdict=CapabilityVerdict.PASS,
    )
    pass_feedback = project_flight_evidence(pass_receipt)
    assert isinstance(pass_feedback, SAGIEvidenceFeedback)
    assert pass_feedback.verdict == CapabilityVerdict.PASS
    assert len(pass_feedback.validated_facts) == 1
    assert pass_feedback.validated_facts[0].confidence_score == 1.0

    neg_receipt = CapabilityEvaluationReceipt(
        evaluation_id="eval-neg",
        mission_set_id="ms-neg",
        plan_hash="plan-hash-neg",
        baseline_metrics=(),
        sage_metrics=(),
        relative_success_gain=-0.2,
        recovery_rate=0.0,
        regression_rate=0.5,
        verdict=CapabilityVerdict.NEGATIVE_RESULT,
        fail_closed_reasons=("Regressed performance on benchmark",),
    )
    neg_feedback = project_flight_evidence(neg_receipt)
    assert neg_feedback.verdict == CapabilityVerdict.NEGATIVE_RESULT
    assert len(neg_feedback.forbidden_regressions) == 1
    assert "Regressed performance on benchmark" in neg_feedback.forbidden_regressions[0].restricted_actions
