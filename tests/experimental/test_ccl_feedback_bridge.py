"""Unit, adversarial falsification, and two-cycle causal demonstration tests for CCLOutcomeFeedbackBridge."""
import pytest
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus
from sage.experimental.cognitive.ccl_feedback_bridge import CCLOutcomeFeedbackBridge, CCLFeedbackRecord


def test_process_reconciliation_calculates_risk_adjustments_and_lineage():
    """Verify CCLOutcomeFeedbackBridge maps reconciliation status to risk adjustments and binds cycle lineage."""
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

    record = bridge.process_reconciliation(rec_unresolved, cycle_id="cycle-1", parent_cycle_id="cycle-0")
    assert record.decision_id == "msn-001"
    assert record.cycle_id == "cycle-1"
    assert record.parent_cycle_id == "cycle-0"
    assert record.source_outcome_ref == "out-001"
    assert record.risk_adjustment == 30.0
    assert "sage/experimental/faulty_path.py" in record.forbidden_paths
    assert record.verify_lineage() is True


def test_adversarial_invalid_lineage_and_fake_reconciliation_rejected():
    """Adversarial test: verify that records with missing lineage or invalid digests are rejected."""
    bridge = CCLOutcomeFeedbackBridge()

    with pytest.raises(ValueError, match="OutcomeReconciliation with valid reconciliation_digest required"):
        bridge.process_reconciliation(None)

    invalid_record = CCLFeedbackRecord(
        cycle_id="",
        parent_cycle_id="cycle-0",
        decision_id="msn-fake",
        context_id="ctx-fake",
        reconciliation_digest="invalid_short_digest",
        source_outcome_ref="out-fake",
        status=OutcomeReconciliationStatus.UNRESOLVED,
        risk_adjustment=30.0,
    )
    assert invalid_record.verify_lineage() is False


def test_two_cycle_causal_demonstration_candidate_reranking():
    """Demonstrate two-cycle execution: Run 1 outcome evidence causally alters Run 2 candidate ranking."""
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

    # Cycle 1: Initial candidate evaluation
    run_1_packets = bridge.evaluate_candidates_with_feedback(raw_candidates, active_cycle_id="cycle-1")
    assert len(run_1_packets) == 2
    # Equal risk (10.0), sorted lexicographically: msn-alpha is first
    assert run_1_packets[0].candidate_id == "msn-alpha"
    assert run_1_packets[1].candidate_id == "msn-beta"

    # Measured Outcome Cycle 1: msn-alpha produces an UNRESOLVED failure
    rec_alpha_failed = OutcomeReconciliation.reconcile(
        decision_id="msn-alpha",
        context_id="ctx-alpha",
        t0_claim_ref="claim-alpha",
        t1_observation_ref="obs-alpha",
        reality_gap_assessment_ref="gap-alpha",
        outcome_ref="out-alpha",
        status=OutcomeReconciliationStatus.UNRESOLVED,
        rationale="Unresolved gap during Cycle 1 execution",
    )
    record_alpha = bridge.process_reconciliation(rec_alpha_failed, cycle_id="cycle-1", parent_cycle_id="cycle-0")

    # Measured Outcome Cycle 1: msn-beta succeeds with RECONCILED verdict
    rec_beta_success = OutcomeReconciliation.reconcile(
        decision_id="msn-beta",
        context_id="ctx-beta",
        t0_claim_ref="claim-beta",
        t1_observation_ref="obs-beta",
        reality_gap_assessment_ref="gap-beta",
        outcome_ref="out-beta",
        status=OutcomeReconciliationStatus.RECONCILED,
        rationale="Reconciled successfully in Cycle 1",
    )
    record_beta = bridge.process_reconciliation(rec_beta_success, cycle_id="cycle-1", parent_cycle_id="cycle-0")

    # Assert 1: Feedback consumed and lineage verified
    assert len(bridge.feedback_records) == 2
    assert all(r.verify_lineage() for r in bridge.feedback_records)

    # Cycle 2: Re-evaluate same candidate list consuming Cycle 1 feedback
    run_2_packets = bridge.evaluate_candidates_with_feedback(raw_candidates, active_cycle_id="cycle-2")
    assert len(run_2_packets) == 2

    # Assert 2: Candidate selection materially influenced and improved
    # msn-beta risk score decreased to 5.0; msn-alpha risk score increased to 40.0
    assert run_2_packets[0].candidate_id == "msn-beta"
    assert run_2_packets[0].risk_score == 5.0

    assert run_2_packets[1].candidate_id == "msn-alpha"
    assert run_2_packets[1].risk_score == 40.0

    # Assert 3: All decision packets remain unauthorized by default (fail-closed posture)
    for p in run_2_packets:
        assert p.is_authorized is False
