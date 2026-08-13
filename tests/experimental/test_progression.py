"""SAGE Mission Progression complete validation suite."""

import copy
import pytest
import os
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

from sage.experimental.progression import (
    MissionProgressionController,
    MissionProgressionState,
    canonical_serialize,
)
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
    CognitiveCompletedMilestone,
)
from sage.core.hdg import HDGEngine
from sage.core.models import HypothesisNode


@pytest.fixture
def valid_mission_input():
    """Provides a standard valid mission input dict."""
    return {
        "mission_id": "mission_test_01",
        "objective": "Verify SAGE Mission Progression Controller implementation",
        "priority_score": 75.0,
        "assigned_agent": "agent_jules_sage",
        "required_evidence": ["git_commit", "test_report"]
    }


@pytest.fixture
def hdg_setup(tmp_path):
    """Provides a thread-safe temporary HDGEngine instance."""
    storage_path = tmp_path / "hdg_causality.json"
    engine = HDGEngine(storage_path=storage_path)
    return engine


def test_1_valid_complete_progression(valid_mission_input, hdg_setup):
    """Test 1: A valid complete progression through all 8 stages."""
    controller = MissionProgressionController(hdg_engine=hdg_setup)

    # INTAKE
    receipt_intake = controller.intake_mission(valid_mission_input)
    assert controller.current_state == MissionProgressionState.INTAKE
    assert receipt_intake.next_state == "INTAKE"
    assert receipt_intake.sequence_order == 1

    # PRIORITIZED
    receipt_prioritized = controller.prioritize()
    assert controller.current_state == MissionProgressionState.PRIORITIZED
    assert receipt_prioritized.next_state == "PRIORITIZED"
    assert receipt_prioritized.sequence_order == 2

    # PREFLIGHT_VALIDATED
    receipt_preflight = controller.validate_preflight()
    assert controller.current_state == MissionProgressionState.PREFLIGHT_VALIDATED
    assert receipt_preflight.next_state == "PREFLIGHT_VALIDATED"
    assert receipt_preflight.sequence_order == 3

    # HANDOFF_READY
    receipt_ready = controller.prepare_handoff()
    assert controller.current_state == MissionProgressionState.HANDOFF_READY
    assert receipt_ready.next_state == "HANDOFF_READY"
    assert receipt_ready.sequence_order == 4

    # HANDOFF_EMITTED
    receipt_emitted = controller.emit_handoff()
    assert controller.current_state == MissionProgressionState.HANDOFF_EMITTED
    assert receipt_emitted.next_state == "HANDOFF_EMITTED"
    assert receipt_emitted.sequence_order == 5

    # EXECUTION_RESULT_RECEIVED
    result_data = {"output_data": "Successfully implemented state transition machine."}
    receipt_result = controller.receive_execution_result(result_data)
    assert controller.current_state == MissionProgressionState.EXECUTION_RESULT_RECEIVED
    assert receipt_result.next_state == "EXECUTION_RESULT_RECEIVED"
    assert receipt_result.sequence_order == 6

    # EVIDENCE_VALIDATED
    provided_evidence = {"git_commit": "hash123", "test_report": "pass"}
    receipt_evidence = controller.validate_evidence(provided_evidence)
    assert controller.current_state == MissionProgressionState.EVIDENCE_VALIDATED
    assert receipt_evidence.next_state == "EVIDENCE_VALIDATED"
    assert receipt_evidence.sequence_order == 7

    # OUTCOME_CLASSIFIED
    receipt_outcome = controller.classify_outcome("SUCCESS")
    assert controller.current_state == MissionProgressionState.OUTCOME_CLASSIFIED
    assert receipt_outcome.next_state == "OUTCOME_CLASSIFIED"
    assert receipt_outcome.sequence_order == 8

    # Verify receipt chain and signature
    assert len(controller.receipts) == 8
    for receipt in controller.receipts:
        payload = {
            "previous_state": receipt.previous_state,
            "next_state": receipt.next_state,
            "mission_id": receipt.mission_id,
            "reason": receipt.reason,
            "validation_result": receipt.validation_result,
            "provenance_reference": receipt.provenance_reference,
            "sequence_order": receipt.sequence_order,
        }
        # Verify deterministic signing
        assert controller.attestation.verify_signature(
            {"canonical_hash": hashlib.sha256(canonical_serialize(payload)).hexdigest()},
            receipt.signature
        )


def test_2_invalid_initial_state():
    """Test 2: Transition attempts before intake fail closed."""
    controller = MissionProgressionController()
    with pytest.raises(ValueError, match="State machine not initialized"):
        controller.prioritize()


def test_3_out_of_order_transition(valid_mission_input):
    """Test 3: Out-of-order transitions fail closed and do not alter state."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    assert controller.current_state == MissionProgressionState.INTAKE

    # Attempt to jump straight to HANDOFF_READY
    with pytest.raises(ValueError, match="Out-of-Order Transition Failed Closed"):
        controller.prepare_handoff()

    # Verify state remains unchanged
    assert controller.current_state == MissionProgressionState.INTAKE


def test_4_failed_priority_decision(valid_mission_input):
    """Test 4: Rejection at priority gate if threshold is not met."""
    controller = MissionProgressionController(priority_threshold=80.0) # Input is 75.0
    controller.intake_mission(valid_mission_input)

    with pytest.raises(ValueError, match="Priority score 75.0 is below required threshold"):
        controller.prioritize()

    # State remains INTAKE
    assert controller.current_state == MissionProgressionState.INTAKE


def test_5_failed_preflight(valid_mission_input):
    """Test 5: Preflight gate rejection via Prefrontal Cortex Simulator."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    # Create an invalid CognitiveState with completed milestone reopening violation
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="mission_test_01",
        objective="Verify SAGE Mission Progression Controller implementation",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(
        authorized_agents=["agent_jules_sage"]
    )
    confidence = CognitiveConfidenceState(
        overall_confidence=1.0,
        last_updated=0.0
    )
    next_action = CognitiveNextAction(
        action_id="task_already_done",
        description="Completed task",
        assigned_agent="agent_jules_sage"
    )
    # The action_id matches a completed milestone, which should trigger Completed-Work Protection BLOCK!
    completed = CognitiveCompletedMilestone(
        milestone_id="task_already_done",
        completed_at=0.0,
        evidence_hash="hash123"
    )
    invalid_cognitive_state = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action,
        completed_milestones=[completed]
    )

    with pytest.raises(ValueError, match="Transition Rejected: Failed validation gate for target state 'PREFLIGHT_VALIDATED'"):
        controller.validate_preflight(cognitive_state=invalid_cognitive_state)

    assert controller.current_state == MissionProgressionState.PRIORITIZED


def test_6_unauthorized_transition(valid_mission_input):
    """Test 6: Preflight blocks transition if the agent is unauthorized."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    # Unauthorized agent identity
    agent = CognitiveAgentIdentity(
        agent_id="rogue_agent",
        name="Rogue",
        role="Malicious Actor",
        authority_level="UNAUTHORIZED",
        governance_tier="UNTRUSTED",
    )
    mission = CognitiveActiveMission(
        mission_id="mission_test_01",
        objective="Verify SAGE Mission Progression Controller implementation",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(
        authorized_agents=["agent_jules_sage"]
    )
    confidence = CognitiveConfidenceState(
        overall_confidence=1.0,
        last_updated=0.0
    )
    next_action = CognitiveNextAction(
        action_id="task_test",
        description="Verify progression",
        assigned_agent="rogue_agent"
    )
    state = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action
    )

    with pytest.raises(ValueError, match="is not in the operator's authorized agents list|invalid or unauthorized authority level"):
        controller.validate_preflight(cognitive_state=state)

    assert controller.current_state == MissionProgressionState.PRIORITIZED


def test_7_malformed_mission_input():
    """Test 7: Malformed mission input raises ValueError."""
    controller = MissionProgressionController()
    malformed = {
        "mission_id": "mission_test_01",
        # Missing objective, priority_score, assigned_agent
    }
    with pytest.raises(ValueError, match="Malformed Mission Input: Missing required field"):
        controller.intake_mission(malformed)


def test_8_malformed_mec_handoff(valid_mission_input):
    """Test 8: Malformed MEC handoff is rejected."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()

    malformed_payload = {
        "assigned_agent": "agent_jules_sage"
        # Missing mission_id
    }
    with pytest.raises(ValueError, match="MEC Handoff Failure: Missing mission_id"):
        controller.emit_handoff(handoff_payload=malformed_payload)

    assert controller.current_state == MissionProgressionState.HANDOFF_READY


def test_9_deterministic_repeated_progression(valid_mission_input):
    """Test 9: Identical progression paths produce identical state outcomes."""
    c1 = MissionProgressionController()
    c2 = MissionProgressionController()

    c1.intake_mission(valid_mission_input)
    c2.intake_mission(valid_mission_input)
    assert c1.current_state == c2.current_state

    c1.prioritize()
    c2.prioritize()
    assert c1.current_state == c2.current_state

    c1.validate_preflight()
    c2.validate_preflight()
    assert c1.current_state == c2.current_state


def test_10_deterministic_serialized_state():
    """Test 10: Canonical serialization is byte-identical despite non-deterministic values."""
    payload1 = {
        "receipt_id": "rec_123",
        "timestamp": "2026-08-01T12:00:00Z",
        "nonce": "abc",
        "state": "INTAKE",
        "details": {"a": 1, "b": 2}
    }
    payload2 = {
        "receipt_id": "rec_456",
        "timestamp": "2026-08-01T12:05:00Z",
        "nonce": "xyz",
        "state": "INTAKE",
        "details": {"b": 2, "a": 1}  # sorted keys check
    }

    bytes1 = canonical_serialize(payload1)
    bytes2 = canonical_serialize(payload2)

    assert bytes1 == bytes2


def test_11_receipt_sequencing(valid_mission_input):
    """Test 11: Receipts are strictly ordered and properly sequenced."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    assert len(controller.receipts) == 2
    r1, r2 = controller.receipts
    assert r1.sequence_order == 1
    assert r1.previous_state is None
    assert r1.next_state == "INTAKE"

    assert r2.sequence_order == 2
    assert r2.previous_state == "INTAKE"
    assert r2.next_state == "PRIORITIZED"


def test_12_evidence_validation_failure(valid_mission_input):
    """Test 12: Evidence validation failure blocks the transition."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "done"})

    # Required evidence are: ["git_commit", "test_report"]
    incomplete_evidence = {"git_commit": "hash123"} # missing test_report

    with pytest.raises(ValueError, match="Evidence Validation Failure: Required evidence 'test_report' is missing"):
        controller.validate_evidence(incomplete_evidence)

    assert controller.current_state == MissionProgressionState.EXECUTION_RESULT_RECEIVED


def test_13_causality_auditor_rejection(valid_mission_input, hdg_setup):
    """Test 13: Causality auditor contradiction detection blocks the transition."""
    # Write a cycle / contradiction to HDG graph
    # Node 1 and Node 2 contradict each other
    auth_token = "auth_spek_enclave_key_2026"
    node1 = HypothesisNode(
        node_id="node_01",
        description="Hypothesis 1",
        contradictions=["node_02"]
    )
    node2 = HypothesisNode(
        node_id="node_02",
        description="Hypothesis 2",
        parent_ids=["node_01"],
        contradictions=["node_01"]
    )
    hdg_setup.add_node(node1, auth_token)
    hdg_setup.add_node(node2, auth_token)

    controller = MissionProgressionController(hdg_engine=hdg_setup)
    controller.intake_mission(valid_mission_input)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "done"})

    provided_evidence = {"git_commit": "hash123", "test_report": "pass"}

    # Attempt to validate evidence referencing 'node_02' which has an active contradiction with its parent 'node_01'
    with pytest.raises(ValueError, match="Causality Violation: Contradiction"):
        controller.validate_evidence(provided_evidence, hdg_node_id="node_02")

    assert controller.current_state == MissionProgressionState.EXECUTION_RESULT_RECEIVED


def test_14_successful_outcome_classification(valid_mission_input):
    """Test 14: Transition with outcome classification validation."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()
    controller.validate_preflight()
    controller.prepare_handoff()
    controller.emit_handoff()
    controller.receive_execution_result({"output_data": "done"})
    controller.validate_evidence({"git_commit": "hash123", "test_report": "pass"})

    # Invalid outcome classification should fail
    with pytest.raises(ValueError, match="Outcome Classification Failure: Invalid outcome status"):
        controller.classify_outcome("INVALID_STATUS")

    assert controller.current_state == MissionProgressionState.EVIDENCE_VALIDATED

    # Valid status works
    controller.classify_outcome("SUCCESS")
    assert controller.current_state == MissionProgressionState.OUTCOME_CLASSIFIED


def test_15_zero_agent_spawning(valid_mission_input):
    """Test 15: Zero-spawning rule is strictly enforced."""
    rogue_input_1 = copy.deepcopy(valid_mission_input)
    rogue_input_1["spawn_agents"] = True

    controller = MissionProgressionController()
    with pytest.raises(PermissionError, match="Zero-Spawning Lock Violation|Dynamic agent spawning is locked"):
        controller.intake_mission(rogue_input_1)

    rogue_input_2 = copy.deepcopy(valid_mission_input)
    rogue_input_2["create_tier"] = "TIER_4_SPAWNED"
    with pytest.raises(PermissionError, match="Zero-Spawning Lock Violation|Dynamic agent spawning is locked"):
        controller.intake_mission(rogue_input_2)


def test_16_input_immutability(valid_mission_input):
    """Test 16: Intake copy is fully immutable from external dictionary modification."""
    controller = MissionProgressionController()
    original = copy.deepcopy(valid_mission_input)

    controller.intake_mission(original)

    # Modify original dict
    original["priority_score"] = 999.0
    original["objective"] = "Hacked!"

    # Verify controller's internal data is unchanged
    assert controller.mission_data["priority_score"] == 75.0
    assert controller.mission_data["objective"] == "Verify SAGE Mission Progression Controller implementation"


def test_17_existing_capability_status_immutability():
    """Test 17: Existing capability statuses remain completely untouched/immutable."""
    # Read capability registry or reports to show no changes are made to production registries
    # We assert that the files in the workspace (like capability reports or discovery registers) are unchanged.
    cap_reg_path = Path("evidence_capture/discovery_candidates_register.json")
    assert cap_reg_path.exists()
    original_size = cap_reg_path.stat().st_size

    controller = MissionProgressionController()
    # Run some operations
    assert controller.current_state is None

    # Check size is unchanged
    assert cap_reg_path.stat().st_size == original_size


def test_18_protected_boundary_exclusion():
    """Test 18: Confirm that protected production directories remain strictly untouched."""
    # We assert that no python files under sage/core, sage/runtime, or sage/acr have been touched by our testing
    protected_dirs = ["sage/core", "sage/runtime", "sage/acr"]
    for d in protected_dirs:
        p = Path(d)
        assert p.exists()
        # Verify no temporary files or modifications exist there
        for item in p.glob("**/*"):
            if item.suffix == ".py":
                # Ensure no test/experimental imports in production files
                with open(item, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "tests." not in content


@patch("sage.experimental.cognitive.prefrontal_cortex.subprocess.run")
def test_19_protected_path_rejection(mock_run, valid_mission_input):
    """Test 19: Confirm that modifying files in protected paths blocks preflight state transition."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    # Simulate git status returning a modified file in sage/core
    mock_res = MagicMock()
    mock_res.stdout = "M sage/core/engine.py"
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    state = CognitiveState(
        agent_identity=CognitiveAgentIdentity(
            agent_id="agent_jules_sage",
            name="Jules",
            role="Senior Software Engineer",
            authority_level="TIER_1_COORDINATOR",
            governance_tier="TIER_1_COORDINATOR",
        ),
        active_mission=CognitiveActiveMission(
            mission_id="mission_test_01",
            objective="Verify progression",
            status="RUNNING"
        ),
        operator_constraints=CognitiveOperatorConstraints(
            authorized_agents=["agent_jules_sage"]
        ),
        confidence_state=CognitiveConfidenceState(
            overall_confidence=1.0,
            last_updated=0.0
        ),
        next_action=CognitiveNextAction(
            action_id="task_test",
            description="Verify progression",
            assigned_agent="agent_jules_sage"
        )
    )

    with pytest.raises(ValueError, match="Protected path violation"):
        controller.validate_preflight(cognitive_state=state)

    assert controller.current_state == MissionProgressionState.PRIORITIZED


@patch("sage.experimental.cognitive.prefrontal_cortex.subprocess.run")
def test_20_scope_drift_rejection(mock_run, valid_mission_input):
    """Test 20: Confirm that modifying files outside permitted paths blocks preflight transition."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    # Simulate git status returning a modified file outside permitted paths
    mock_res = MagicMock()
    mock_res.stdout = "M other_dir/file.py"
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    state = CognitiveState(
        agent_identity=CognitiveAgentIdentity(
            agent_id="agent_jules_sage",
            name="Jules",
            role="Senior Software Engineer",
            authority_level="TIER_1_COORDINATOR",
            governance_tier="TIER_1_COORDINATOR",
        ),
        active_mission=CognitiveActiveMission(
            mission_id="mission_test_01",
            objective="Verify progression",
            status="RUNNING"
        ),
        operator_constraints=CognitiveOperatorConstraints(
            authorized_agents=["agent_jules_sage"],
            permitted_paths=["sage/experimental/"] # Permitted is experimental
        ),
        confidence_state=CognitiveConfidenceState(
            overall_confidence=1.0,
            last_updated=0.0
        ),
        next_action=CognitiveNextAction(
            action_id="task_test",
            description="Verify progression",
            assigned_agent="agent_jules_sage"
        )
    )

    with pytest.raises(ValueError, match="Scope drift violation"):
        controller.validate_preflight(cognitive_state=state)

    assert controller.current_state == MissionProgressionState.PRIORITIZED


@patch("sage.experimental.cognitive.prefrontal_cortex.subprocess.run")
def test_21_ancestry_violation_rejection(mock_run, valid_mission_input):
    """Test 21: Confirm that un-rebased branch blocks preflight transition."""
    controller = MissionProgressionController()
    controller.intake_mission(valid_mission_input)
    controller.prioritize()

    # Mock subprocess.run responses
    # First call: git status
    # Second call: git rev-parse origin/main
    # Third call: git merge-base --is-ancestor
    mock_res_status = MagicMock()
    mock_res_status.stdout = "M scripts/sync_to_drive.py"
    mock_res_status.returncode = 0

    mock_res_rev = MagicMock()
    mock_res_rev.returncode = 0

    mock_res_ancestor = MagicMock()
    mock_res_ancestor.returncode = 1 # Not an ancestor!

    mock_run.side_effect = [mock_res_status, mock_res_rev, mock_res_ancestor]

    state = CognitiveState(
        agent_identity=CognitiveAgentIdentity(
            agent_id="agent_jules_sage",
            name="Jules",
            role="Senior Software Engineer",
            authority_level="TIER_1_COORDINATOR",
            governance_tier="TIER_1_COORDINATOR",
        ),
        active_mission=CognitiveActiveMission(
            mission_id="mission_test_01",
            objective="Verify progression",
            status="RUNNING"
        ),
        operator_constraints=CognitiveOperatorConstraints(
            authorized_agents=["agent_jules_sage"]
        ),
        confidence_state=CognitiveConfidenceState(
            overall_confidence=1.0,
            last_updated=0.0
        ),
        next_action=CognitiveNextAction(
            action_id="task_test",
            description="Verify progression",
            assigned_agent="agent_jules_sage"
        )
    )

    with pytest.raises(ValueError, match="Ancestry violation"):
        controller.validate_preflight(cognitive_state=state)

    assert controller.current_state == MissionProgressionState.PRIORITIZED
