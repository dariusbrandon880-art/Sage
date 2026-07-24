"""Comprehensive end-to-end State Transition Protocol (STP) and CIV-001 Validation tests."""

import pytest
from sage.runtime import SageRuntime
from sage.models import DecisionType, DecisionEntry


@pytest.fixture
def test_runtime(tmp_path):
    return SageRuntime(workspace_path=str(tmp_path))


def test_stp_successful_transition(test_runtime):
    # Set up initial S0 state
    test_runtime.set_objective("Initial State S0")

    # 1. Execute a successful state transition
    def mutate():
        test_runtime.current_state.active_task = "Task Committed in S1"
        test_runtime._save_state()

    res = test_runtime.state_transition.execute_transition(mutate, "Successful Task Transition")
    assert res["success"] is True
    assert res["status"] == "committed_s1"
    assert test_runtime.current_state.active_task == "Task Committed in S1"

    # Confirm checkpoint was saved
    assert "checkpoint_id" in res
    assert "snapshot_id" in res


def test_stp_exception_rollback(test_runtime):
    # Set up initial state S0
    test_runtime.set_objective("State S0")
    test_runtime.current_state.active_task = "Original S0 Task"
    test_runtime._save_state()

    # Create mutation that raises an exception
    def bad_mutate():
        test_runtime.current_state.active_task = "Modified Task before exception"
        test_runtime._save_state()
        raise RuntimeError("Fatal process crash")

    res = test_runtime.state_transition.execute_transition(bad_mutate, "Crash Transition")

    # Verify transition fails and rolls back state to S0
    assert res["success"] is False
    assert res["status"] == "execution_failed_rolled_back"
    assert test_runtime.current_state.active_task == "Original S0 Task"  # Rolled back!

    # Confirm a reliability incident was logged in memory ledger
    incidents = test_runtime.validation.memory.search_by_type("reliability_incident")
    assert len(incidents) == 1
    assert incidents[0].content["incident_type"] == "exception"
    assert "Fatal process crash" in incidents[0].content["description"]


def test_stp_validation_failure_rollback(test_runtime):
    # Set up initial state S0
    test_runtime.set_objective("Initial S0 Objective")
    test_runtime._save_state()

    # Mutation that intentionally creates an integrity violation
    # (Decision referencing a non-existent evidence ID)
    def invalidate_mutate():
        test_runtime.current_state.active_task = "Task causing validation failure"
        test_runtime._save_state()

        # Insert a decision with invalid evidence
        d_entry = DecisionEntry(
            id="dec_corrupted",
            decision_type=DecisionType.ARCHITECTURAL,
            description="Bad decision",
            rationale="No rationale",
            evidence=["non_existent_memory_id_999"],
        )
        test_runtime.decisions.record_decision(
            decision_type=d_entry.decision_type,
            description=d_entry.description,
            rationale=d_entry.rationale,
            evidence=d_entry.evidence,
            decision_id=d_entry.id,
        )

    res = test_runtime.state_transition.execute_transition(invalidate_mutate, "Corrupt Transition")

    # Verify transition fails the integrity check and rolls back to S0
    assert res["success"] is False
    assert res["status"] == "validation_failed_rolled_back"
    assert test_runtime.current_state.active_task is None  # Rolled back to initial S0!

    # Decisions directory is cleared and restored to S0
    assert len(test_runtime.decisions.list_all()) == 0

    # Confirm a reliability incident of type validation_failure was logged in memory ledger
    incidents = test_runtime.validation.memory.search_by_type("reliability_incident")
    assert len(incidents) == 1
    assert incidents[0].content["incident_type"] == "validation_failure"
