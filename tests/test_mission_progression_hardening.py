"""Comprehensive Hardening Regression Contract and Verification Suite for SAGE Governed Mission Progression."""

import json
import hashlib
import copy
import subprocess
from pathlib import Path
import pytest
from pydantic import ValidationError

from sage.mission_control import (
    SAGEMissionProgressionController,
    ExperimentalMissionState,
    MissionTransitionResult,
    LIFECYCLE_SEQUENCE
)
from sage.mission_intake import (
    SAGEMissionIntakeLayer,
    MissionProposal
)
from sage.change_impact import (
    SAGEChangeImpactAnalyzer,
    CapabilityImpactResult
)
from sage.capability_registry import (
    SAGEOperationalCapabilityRegistry,
    SAGECapability
)
from sage.core.hdg import HDGEngine
from sage.core.models import HypothesisNode
from sage.core.boundary import BoundaryEnforcer


@pytest.fixture
def mock_registry_file(tmp_path):
    """Fixture to provide a isolated capability registry file on disk."""
    reg_path = tmp_path / "operational_capability_registry.json"
    data = [
        {
            "capability_id": "CAP-COGNITIVE-KERNEL",
            "name": "Cognitive Kernel Foundation",
            "description": "Kernel for cognitive simulation",
            "evidence_references": ["evidence_capture/cognitive_kernel_foundation_report.json"],
            "test_references": ["tests/experimental/test_cognitive_kernel.py"],
            "archive_promotion_status": "READY"
        },
        {
            "capability_id": "CAP-PML-RELIABILITY",
            "name": "PML Operational Reliability",
            "description": "PML Reliability guarantees",
            "evidence_references": ["evidence_capture/ccl_orchestrator_evidence.json"],
            "test_references": ["tests/experimental/test_continuity_control.py"],
            "archive_promotion_status": "READY"
        }
    ]
    with open(reg_path, "w") as f:
        json.dump(data, f)
    return reg_path


@pytest.fixture
def mock_hdg_file(tmp_path):
    """Fixture to provide a clean isolated HDG causality ledger on disk."""
    hdg_path = tmp_path / "hdg_causality.json"
    with open(hdg_path, "w") as f:
        json.dump([], f)
    return hdg_path


# 1. Successful end-to-end progression
def test_successful_end_to_end_progression():
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Harden Progression",
        "description": "Add comprehensive hardening coverage",
        "objective": "Achieve robust regression boundaries",
        "operator_id": "operator_jules_c",
        "prerequisites": {}
    }

    res_intake = intake.submit_proposal(proposal)
    assert res_intake["accepted"] is True
    mission_id = res_intake["mission_id"]

    # Retrieve mission state from queue
    state = intake.get_queue()[0]
    assert state.current_state == "MISSION_PROPOSED"

    # Step-by-step transition
    controller = SAGEMissionProgressionController()

    prereqs = {
        "VALUE_EVALUATED": "value_appraisal_approved",
        "PREFLIGHT_REQUIRED": "preflight_checklist_passed",
        "EXECUTION_AUTHORIZED": "operator_signature_obtained",
        "EXECUTION_COMPLETE": "execution_log_recorded",
        "VALIDATION_REQUIRED": "validation_receipt_issued",
        "EVIDENCE_REQUIRED": "evidence_hashes_verified",
        "REVIEW_REQUIRED": "peer_signoff_completed",
        "PROMOTION_READY": "promotion_approval_granted",
        "CLOSED": "archival_success_confirmed"
    }

    for state_name in LIFECYCLE_SEQUENCE[1:]:
        prereq_key = prereqs[state_name]
        state.prerequisites[prereq_key] = True
        res = controller.evaluate_transition(state, state_name)
        assert res.success is True
        assert res.transitioned is True
        assert state.current_state == state_name


# 2. Failed preflight rejection
def test_failed_preflight_rejection():
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-fail-preflight",
        name="Fail Preflight test",
        current_state="VALUE_EVALUATED",
        prerequisites={"preflight_checklist_passed": False}
    )

    res = controller.evaluate_transition(state, "PREFLIGHT_REQUIRED")
    assert res.success is False
    assert res.transitioned is False
    assert "Missing prerequisite" in res.decision_reason
    assert state.current_state == "VALUE_EVALUATED"


# 3. Unauthorized state transition
def test_unauthorized_state_transition():
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-unauth",
        name="Unauth transition test",
        current_state="PREFLIGHT_REQUIRED",
        prerequisites={"operator_signature_obtained": False}
    )

    res = controller.evaluate_transition(state, "EXECUTION_AUTHORIZED")
    assert res.success is False
    assert res.transitioned is False
    assert "operator_signature_obtained" in res.decision_reason
    assert state.current_state == "PREFLIGHT_REQUIRED"


# 4. Out-of-order transition
def test_out_of_order_transition():
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-ooo",
        name="Out of order test",
        current_state="MISSION_PROPOSED"
    )

    # Attempt skipping VALUE_EVALUATED
    res_skip = controller.evaluate_transition(state, "PREFLIGHT_REQUIRED")
    assert res_skip.success is False
    assert "Cannot skip sequential stages" in res_skip.decision_reason

    # Attempt backward transition
    state.current_state = "EXECUTION_COMPLETE"
    res_back = controller.evaluate_transition(state, "EXECUTION_AUTHORIZED")
    assert res_back.success is False
    assert "Backward progression is forbidden" in res_back.decision_reason


# 5. Malformed mission input
def test_malformed_mission_input():
    intake = SAGEMissionIntakeLayer()

    # Missing operator_id
    proposal_missing = {
        "name": "Audit",
        "description": "Desc",
        "objective": "Obj"
    }
    res_missing = intake.submit_proposal(proposal_missing)
    assert res_missing["accepted"] is False
    assert "Missing required fields" in res_missing["reason"]

    # Empty/blank operator_id
    proposal_blank = {
        "name": "Audit",
        "description": "Desc",
        "objective": "Obj",
        "operator_id": "   "
    }
    res_blank = intake.submit_proposal(proposal_blank)
    assert res_blank["accepted"] is False
    assert "cannot be empty or blank" in res_blank["reason"]


# 6. Malformed MEC handoff
def test_malformed_mec_handoff():
    controller = SAGEMissionProgressionController()

    # Non-dict input
    with pytest.raises(ValueError, match="MEC handoff payload must be a dictionary."):
        controller.validate_mec_handoff("not-a-dict")

    # Missing field
    with pytest.raises(ValueError, match="MEC handoff payload missing required field"):
        controller.validate_mec_handoff({
            "author_id": "jules",
            "branch_name": "session-c",
            "write_lock_token": "lock-123"
            # target_session_id missing
        })

    # Empty string field
    with pytest.raises(ValueError, match="must be a non-empty string."):
        controller.validate_mec_handoff({
            "author_id": "jules",
            "branch_name": "session-c",
            "write_lock_token": "lock-123",
            "target_session_id": "   "
        })


# 7. Missing evidence
def test_missing_evidence(tmp_path):
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-ev",
        name="Evidence check",
        current_state="VALIDATION_REQUIRED"
    )

    missing_path = str(tmp_path / "non_existent_evidence.json")
    expected_hashes = {missing_path: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}

    with pytest.raises(ValueError, match="Evidence file missing"):
        controller.verify_evidence_integrity(state, expected_hashes)


# 8. Corrupted evidence
def test_corrupted_evidence(tmp_path):
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-ev",
        name="Evidence check",
        current_state="VALIDATION_REQUIRED"
    )

    file_path = tmp_path / "some_evidence.json"
    file_path.write_text("unaltered content")

    # Correct hash
    correct_hash = hashlib.sha256(b"unaltered content").hexdigest()

    # Check integrity with correct hash (passes)
    assert controller.verify_evidence_integrity(state, {str(file_path): correct_hash}) is True

    # Check integrity with mismatched/corrupted hash
    with pytest.raises(ValueError, match="Cryptographic hash mismatch"):
        controller.verify_evidence_integrity(state, {str(file_path): "wronghash123"})


# 9. Deterministic transition receipts
def test_deterministic_transition_receipts():
    controller = SAGEMissionProgressionController()

    state1 = ExperimentalMissionState(
        mission_id="msn-deterministic",
        name="Deterministic test",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )
    state2 = ExperimentalMissionState(
        mission_id="msn-deterministic",
        name="Deterministic test",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )

    res1 = controller.evaluate_transition(state1, "VALUE_EVALUATED")
    res2 = controller.evaluate_transition(state2, "VALUE_EVALUATED")

    bytes1 = json.dumps(res1.model_dump(), sort_keys=True).encode("utf-8")
    bytes2 = json.dumps(res2.model_dump(), sort_keys=True).encode("utf-8")

    assert bytes1 == bytes2


# 10. Deterministic serialized output
def test_deterministic_serialized_output():
    state1 = ExperimentalMissionState(
        mission_id="msn-serialized",
        name="Serialize test",
        current_state="MISSION_PROPOSED"
    )
    state2 = ExperimentalMissionState(
        mission_id="msn-serialized",
        name="Serialize test",
        current_state="MISSION_PROPOSED"
    )

    bytes1 = json.dumps(state1.model_dump(), sort_keys=True).encode("utf-8")
    bytes2 = json.dumps(state2.model_dump(), sort_keys=True).encode("utf-8")

    assert bytes1 == bytes2


# 11. Duplicate transition handling
def test_duplicate_transition_handling():
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-dup",
        name="Duplicate test",
        current_state="MISSION_PROPOSED"
    )

    # Transition to the current state (duplicate transition)
    res = controller.evaluate_transition(state, "MISSION_PROPOSED")
    assert res.success is True
    assert res.transitioned is False
    assert state.current_state == "MISSION_PROPOSED"


# 12. Provenance preservation
def test_provenance_preservation():
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit Lineage",
        "description": "Trace cryptographic audit trails",
        "objective": "Verify the integrity",
        "operator_id": "operator_jules_provenance"
    }

    res = intake.submit_proposal(proposal)
    enqueued = intake.get_queue()[0]

    provenance = enqueued.metadata["provenance"]
    assert provenance["operator_id"] == "operator_jules_provenance"
    assert provenance["original_proposal"] == proposal


# 13. Input immutability
def test_input_immutability():
    intake = SAGEMissionIntakeLayer()
    proposal = {
        "name": "Audit Lineage",
        "description": "Trace cryptographic audit trails",
        "objective": "Verify the integrity",
        "operator_id": "operator_jules_immutability",
        "prerequisites": {"value_appraisal_approved": True}
    }

    proposal_snapshot = copy.deepcopy(proposal)

    intake.submit_proposal(proposal)

    # Verify input is byte-for-byte and structurally unchanged
    assert proposal == proposal_snapshot


# 14. Capability-status immutability
def test_capability_status_immutability(mock_registry_file):
    with open(mock_registry_file, "rb") as f:
        snapshot_bytes = f.read()

    # Instantiate analyzer and run analysis
    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(mock_registry_file))
    analyzer.analyze_changes(["sage/mission_control.py"])

    with open(mock_registry_file, "rb") as f:
        after_bytes = f.read()

    # Registry remains completely unchanged
    assert snapshot_bytes == after_bytes


# 15. Zero-spawning enforcement
def test_zero_spawning_enforcement(monkeypatch):
    def fake_popen(*args, **kwargs):
        raise AssertionError("Unauthorized process spawn detected!")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-zero-spawn",
        name="Zero Spawn check",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )

    # Progression run
    res = controller.evaluate_transition(state, "VALUE_EVALUATED")
    assert res.success is True
    # Zero-spawning assertion (completed because Popen was never called)


# 16. Causality-auditor integration
def test_causality_auditor_integration(mock_hdg_file):
    # Set up HDGEngine and add valid nodes
    token = BoundaryEnforcer.SYSTEM_TOKEN
    engine = HDGEngine(storage_path=mock_hdg_file)

    # Node 1
    n1 = HypothesisNode(node_id="node_1", description="Baseline security", parent_ids=[])
    engine.add_node(n1, token)

    # Node 2
    n2 = HypothesisNode(node_id="node_2", description="Harden boundaries", parent_ids=["node_1"])
    engine.add_node(n2, token)

    controller = SAGEMissionProgressionController()

    # Success scenario (no contradiction)
    state_ok = ExperimentalMissionState(
        mission_id="msn-causality-ok",
        name="Causality Integration Test Ok",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True},
        metadata={
            "hdg_node_id": "node_2",
            "hdg_storage_path": str(mock_hdg_file)
        }
    )

    res_ok = controller.evaluate_transition(state_ok, "VALUE_EVALUATED")
    assert res_ok.success is True
    assert state_ok.current_state == "VALUE_EVALUATED"

    # Add contradiction to node 2
    n3 = HypothesisNode(node_id="node_3", description="Contradicts node 1", parent_ids=["node_2"], contradictions=["node_1"])
    engine.add_node(n3, token)

    # Contradiction scenario
    state_fail = ExperimentalMissionState(
        mission_id="msn-causality-fail",
        name="Causality Integration Test Fail",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True},
        metadata={
            "hdg_node_id": "node_3",
            "hdg_storage_path": str(mock_hdg_file)
        }
    )

    res_fail = controller.evaluate_transition(state_fail, "VALUE_EVALUATED")
    assert res_fail.success is False
    assert "Causality Violation" in res_fail.decision_reason
    assert state_fail.current_state == "MISSION_PROPOSED"


# 17. UNAFFECTED classification
def test_unaffected_classification(mock_registry_file):
    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(mock_registry_file))
    report = analyzer.analyze_changes(["completely_unrelated_file.py"])

    for cap_res in report.impacted_capabilities:
        assert cap_res.classification == "UNAFFECTED"


# 18. REVALIDATION_REQUIRED classification
def test_revalidation_required_classification(mock_registry_file):
    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(mock_registry_file))
    # 'tests/experimental/test_cognitive_kernel.py' is a direct test reference for CAP-COGNITIVE-KERNEL
    report = analyzer.analyze_changes(["tests/experimental/test_cognitive_kernel.py"])

    kernel_cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-COGNITIVE-KERNEL")
    assert kernel_cap.classification == "REVALIDATION_REQUIRED"


# 19. UNKNOWN_DEPENDENCY classification
def test_unknown_dependency_classification(mock_registry_file):
    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(mock_registry_file))
    # 'sage/mission_control.py' starts with sage/ but isn't core/ or runtime/ or acr/ and contains 'mission'
    report = analyzer.analyze_changes(["sage/mission_control.py"])

    for cap_res in report.impacted_capabilities:
        assert cap_res.classification == "UNKNOWN_DEPENDENCY"


# 20. Multiple affected capabilities
def test_multiple_affected_capabilities(mock_registry_file):
    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(mock_registry_file))
    # Modifying a root experimental helper file like 'sage/mission_control.py'
    # triggers UNKNOWN_DEPENDENCY across multiple capabilities
    report = analyzer.analyze_changes(["sage/mission_control.py"])

    caps = [c.capability_id for c in report.impacted_capabilities]
    assert "CAP-COGNITIVE-KERNEL" in caps
    assert "CAP-PML-RELIABILITY" in caps
    for cap_res in report.impacted_capabilities:
        assert cap_res.classification == "UNKNOWN_DEPENDENCY"


# 21. Protected-boundary exclusion
def test_protected_boundary_exclusion():
    enforcer = BoundaryEnforcer()
    # Modifying a protected file like '.sage/validation/audit/spek_vault.json' raises PermissionError without the valid token
    with pytest.raises(PermissionError, match="Security Boundary Enforcement Violation"):
        enforcer.validate_mutation(".sage/validation/audit/spek_vault.json", auth_token="unauthorized_operator")


# 22. Failure-closed behavior
def test_failure_closed_behavior():
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-failure-closed",
        name="Failure Closed Test",
        current_state="MISSION_PROPOSED"
    )

    # Transition fails due to missing prerequisite
    res = controller.evaluate_transition(state, "VALUE_EVALUATED")
    assert res.success is False
    assert state.current_state == "MISSION_PROPOSED"  # State is absolutely preserved (unmutated)
