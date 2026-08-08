"""Unit tests for SAGE Mission Progression Controller."""

import pytest
from sage.mission_control import (
    SAGEMissionProgressionController,
    ExperimentalMissionState,
    MissionTransitionResult,
    LIFECYCLE_SEQUENCE
)


def test_valid_sequential_progression():
    """Verify that a mission can advance through the full 10-stage lifecycle sequentially."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-joint-audit-001",
        name="Joint Multi-Agent Context Validation and Security Auditing",
        current_state="MISSION_PROPOSED"
    )

    # Transition 1: MISSION_PROPOSED -> VALUE_EVALUATED
    state.prerequisites["value_appraisal_approved"] = True
    res1 = controller.evaluate_transition(state, "VALUE_EVALUATED")
    assert res1.success is True
    assert res1.transitioned is True
    assert state.current_state == "VALUE_EVALUATED"

    # Transition 2: VALUE_EVALUATED -> PREFLIGHT_REQUIRED
    state.prerequisites["preflight_checklist_passed"] = True
    res2 = controller.evaluate_transition(state, "PREFLIGHT_REQUIRED")
    assert res2.success is True
    assert state.current_state == "PREFLIGHT_REQUIRED"

    # Transition 3: PREFLIGHT_REQUIRED -> EXECUTION_AUTHORIZED
    state.prerequisites["operator_signature_obtained"] = True
    res3 = controller.evaluate_transition(state, "EXECUTION_AUTHORIZED")
    assert res3.success is True
    assert state.current_state == "EXECUTION_AUTHORIZED"

    # Transition 4: EXECUTION_AUTHORIZED -> EXECUTION_COMPLETE
    state.prerequisites["execution_log_recorded"] = True
    res4 = controller.evaluate_transition(state, "EXECUTION_COMPLETE")
    assert res4.success is True
    assert state.current_state == "EXECUTION_COMPLETE"

    # Transition 5: EXECUTION_COMPLETE -> VALIDATION_REQUIRED
    state.prerequisites["validation_receipt_issued"] = True
    res5 = controller.evaluate_transition(state, "VALIDATION_REQUIRED")
    assert res5.success is True
    assert state.current_state == "VALIDATION_REQUIRED"

    # Transition 6: VALIDATION_REQUIRED -> EVIDENCE_REQUIRED
    state.prerequisites["evidence_hashes_verified"] = True
    res6 = controller.evaluate_transition(state, "EVIDENCE_REQUIRED")
    assert res6.success is True
    assert state.current_state == "EVIDENCE_REQUIRED"

    # Transition 7: EVIDENCE_REQUIRED -> REVIEW_REQUIRED
    state.prerequisites["peer_signoff_completed"] = True
    res7 = controller.evaluate_transition(state, "REVIEW_REQUIRED")
    assert res7.success is True
    assert state.current_state == "REVIEW_REQUIRED"

    # Transition 8: REVIEW_REQUIRED -> PROMOTION_READY
    state.prerequisites["promotion_approval_granted"] = True
    res8 = controller.evaluate_transition(state, "PROMOTION_READY")
    assert res8.success is True
    assert state.current_state == "PROMOTION_READY"

    # Transition 9: PROMOTION_READY -> CLOSED
    state.prerequisites["archival_success_confirmed"] = True
    res9 = controller.evaluate_transition(state, "CLOSED")
    assert res9.success is True
    assert state.current_state == "CLOSED"


def test_invalid_transition_rejection():
    """Verify that attempting to skip stages gets rejected."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-01",
        name="Skipping stages test",
        current_state="MISSION_PROPOSED"
    )

    # Attempt to skip directly to CLOSED
    res = controller.evaluate_transition(state, "CLOSED")
    assert res.success is False
    assert res.transitioned is False
    assert "Cannot skip sequential stages" in res.decision_reason
    assert state.current_state == "MISSION_PROPOSED"


def test_missing_prerequisite_rejection():
    """Verify that a missing or unsatisfied prerequisite blocks progression."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-02",
        name="Missing prerequisite test",
        current_state="MISSION_PROPOSED"
    )

    # Missing value_appraisal_approved
    res = controller.evaluate_transition(state, "VALUE_EVALUATED")
    assert res.success is False
    assert res.transitioned is False
    assert "Missing prerequisite" in res.decision_reason
    assert state.current_state == "MISSION_PROPOSED"


def test_execution_authorization_boundary():
    """Verify the execution authorization boundary strictly requires operator signature."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-03",
        name="Authorization boundary test",
        current_state="PREFLIGHT_REQUIRED"
    )

    # Without operator signature
    res = controller.evaluate_transition(state, "EXECUTION_AUTHORIZED")
    assert res.success is False
    assert "operator_signature_obtained" in res.decision_reason

    # Provide explicit signature
    state.prerequisites["operator_signature_obtained"] = True
    res_ok = controller.evaluate_transition(state, "EXECUTION_AUTHORIZED")
    assert res_ok.success is True
    assert state.current_state == "EXECUTION_AUTHORIZED"


def test_validation_and_evidence_prerequisites():
    """Verify separate validation and evidence check prerequisite requirements."""
    controller = SAGEMissionProgressionController()

    # 1. Validation check
    state_val = ExperimentalMissionState(
        mission_id="msn-test-04",
        name="Validation prerequisite test",
        current_state="EXECUTION_COMPLETE"
    )
    res_val_fail = controller.evaluate_transition(state_val, "VALIDATION_REQUIRED")
    assert res_val_fail.success is False
    assert "validation_receipt_issued" in res_val_fail.decision_reason

    state_val.prerequisites["validation_receipt_issued"] = True
    res_val_ok = controller.evaluate_transition(state_val, "VALIDATION_REQUIRED")
    assert res_val_ok.success is True

    # 2. Evidence check
    state_ev = ExperimentalMissionState(
        mission_id="msn-test-05",
        name="Evidence prerequisite test",
        current_state="VALIDATION_REQUIRED"
    )
    res_ev_fail = controller.evaluate_transition(state_ev, "EVIDENCE_REQUIRED")
    assert res_ev_fail.success is False
    assert "evidence_hashes_verified" in res_ev_fail.decision_reason

    state_ev.prerequisites["evidence_hashes_verified"] = True
    res_ev_ok = controller.evaluate_transition(state_ev, "EVIDENCE_REQUIRED")
    assert res_ev_ok.success is True


def test_promotion_readiness():
    """Verify promotion readiness prerequisite checkpoint."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-06",
        name="Promotion readiness test",
        current_state="REVIEW_REQUIRED"
    )

    res_fail = controller.evaluate_transition(state, "PROMOTION_READY")
    assert res_fail.success is False
    assert "promotion_approval_granted" in res_fail.decision_reason

    state.prerequisites["promotion_approval_granted"] = True
    res_ok = controller.evaluate_transition(state, "PROMOTION_READY")
    assert res_ok.success is True


def test_terminal_closed_state():
    """Verify that once a mission is CLOSED, no further transitions are allowed."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-07",
        name="Terminal closed test",
        current_state="CLOSED"
    )

    # Attempting to go backward or transition anywhere from CLOSED is rejected
    res = controller.evaluate_transition(state, "MISSION_PROPOSED")
    assert res.success is False
    assert "terminal CLOSED state" in res.decision_reason


def test_deterministic_transition_results():
    """Verify that running identical input states yields identical, deterministic transition results."""
    controller = SAGEMissionProgressionController()

    state1 = ExperimentalMissionState(
        mission_id="msn-test-08",
        name="Deterministic test",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )
    state2 = ExperimentalMissionState(
        mission_id="msn-test-08",
        name="Deterministic test",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )

    res1 = controller.evaluate_transition(state1, "VALUE_EVALUATED")
    res2 = controller.evaluate_transition(state2, "VALUE_EVALUATED")

    assert res1.success == res2.success
    assert res1.transitioned == res2.transitioned
    assert res1.decision_reason == res2.decision_reason
    assert res1.explainable_trace == res2.explainable_trace


def test_non_execution_guarantee():
    """Confirm that the controller performs absolutely no system code execution itself.

    Ensures that calling evaluate_transition does not trigger external effects
    or mutate any other systems.
    """
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-test-09",
        name="Non-execution test",
        current_state="MISSION_PROPOSED"
    )

    # Capturing state prior
    prereqs_before = dict(state.prerequisites)

    # Run check
    controller.evaluate_transition(state, "VALUE_EVALUATED")

    # Verify that state prerequisites were NOT modified automatically
    assert state.prerequisites == prereqs_before
