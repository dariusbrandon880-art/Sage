"""Unit and two-cycle demonstration tests for SAGE Closed-Loop Outcome Feedback Bridge."""
import pytest
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge


def test_process_reconciliation_calculates_risk_adjustments():
    """Verify CCLOutcomeFeedbackBridge maps reconciliation status to risk adjustments."""
    bridge = CCLOutcomeFeedbackBridge()

    rec_unresolved = OutcomeReconciliation.reconcile(
        decision_id="msn-001",
        context_id="ctx-001",
        t0_claim_ref="claim-001",
        t1_observation_ref="sage/experimental/faulty_path.py",
        reality_gap_assessment_ref="gap-001",
        outcome_ref="out-001",
        status=OutcomeReconciliationStatus.UNRESOLVED,
        rationale="Execution failed T1 validation",
    )

    record = bridge.process_reconciliation(rec_unresolved)
    assert record.decision_id == "msn-001"
    assert record.risk_adjustment == 30.0
    assert "sage/experimental/faulty_path.py" in record.forbidden_paths


def test_two_cycle_demonstration_candidate_reranking():
    """Demonstrate two-cycle execution: Run 1 outcome evidence alters Run 2 candidate ranking."""
    bridge = CCLOutcomeFeedbackBridge()

    raw_candidates = [
        {
            "candidate_id": "msn-alpha",
            "description": "Candidate Alpha",
            "affected_paths": ["sage/experimental/alpha.py"],
            "verification_requirements": ["tests/test_alpha.py"],
        },
        {
            "candidate_id": "msn-beta",
            "description": "Candidate Beta",
            "affected_paths": ["sage/experimental/beta.py"],
            "verification_requirements": ["tests/test_beta.py"],
        },
    ]

    # Run 1: Initial evaluation before feedback
    run_1_packets = bridge.evaluate_candidates_with_feedback(raw_candidates)
    assert len(run_1_packets) == 2
    # Equal risk (10.0), sorted lexicographically: msn-alpha is first
    assert run_1_packets[0].candidate_id == "msn-alpha"
    assert run_1_packets[1].candidate_id == "msn-beta"

    # Outcome of Run 1: msn-alpha produces an UNRESOLVED failure
    rec_alpha_failed = OutcomeReconciliation.reconcile(
        decision_id="msn-alpha",
        context_id="ctx-alpha",
        t0_claim_ref="claim-alpha",
        t1_observation_ref="obs-alpha",
        reality_gap_assessment_ref="gap-alpha",
        outcome_ref="out-alpha",
        status=OutcomeReconciliationStatus.UNRESOLVED,
        rationale="Unresolved gap during execution",
    )
    bridge.process_reconciliation(rec_alpha_failed)

    # Outcome of Run 1: msn-beta succeeds with RECONCILED verdict
    rec_beta_success = OutcomeReconciliation.reconcile(
        decision_id="msn-beta",
        context_id="ctx-beta",
        t0_claim_ref="claim-beta",
        t1_observation_ref="obs-beta",
        reality_gap_assessment_ref="gap-beta",
        outcome_ref="out-beta",
        status=OutcomeReconciliationStatus.RECONCILED,
        rationale="Reconciled successfully",
    )
    bridge.process_reconciliation(rec_beta_success)

    # Run 2: Re-evaluate same candidate list with feedback applied
    run_2_packets = bridge.evaluate_candidates_with_feedback(raw_candidates)
    assert len(run_2_packets) == 2

    # msn-beta now has risk 5.0 (10 - 5), msn-alpha has risk 40.0 (10 + 30)
    # msn-beta MUST now be ranked FIRST deterministically
    assert run_2_packets[0].candidate_id == "msn-beta"
    assert run_2_packets[0].risk_score == 5.0

    assert run_2_packets[1].candidate_id == "msn-alpha"
    assert run_2_packets[1].risk_score == 40.0

    # All generated packets MUST remain unauthorized by default (fail-closed posture)
    for p in run_2_packets:
        assert p.is_authorized is False
