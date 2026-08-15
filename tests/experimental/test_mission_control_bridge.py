"""Unit and integration tests for SAGE Mission Execution Bridge and Workspace Revalidator.

Verifies the integration of SAGEChangeImpactAnalyzer, SAGEOperationalCapabilityRegistry,
SAGEMissionProgressionController, and Master Archive under real and mock workloads,
specifically auditing the BondManager and SPEK validation connection boundary.
"""

import os
import json
import pytest
from pathlib import Path

from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge, WorkloadExecutionResult
from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability
from sage.mission_control import ExperimentalMissionState
from sage.acr.bond import BondValidationError


def test_bridge_sequential_pipeline_execution(tmp_path):
    """Verify that SAGEMissionExecutionBridge runs the complete sequential 10-stage progression to CLOSED."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"

    # Pre-populate registry with a capability needing revalidation
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    cap = SAGECapability(
        capability_id="CAP-STATE-PERSISTENCE",
        name="State Persistence",
        description="Continuous atomic serialization of task states.",
        implementation_status="IMPLEMENTED",
        validation_status="UNVERIFIED",  # Needs revalidation!
        evidence_references=["evidence_capture/ccl_operational_feedback.json"],
        test_references=["tests/test_continuity_persistence.py"],
        archive_promotion_status="READY"
    )
    registry.add_capability(cap)

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    # Run execution with mock lint checks
    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_test_1",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False
    )

    assert res["mission_id"] == "mission_reval_test_1"
    assert res["overall_success"] is True
    assert res["final_state"] == "CLOSED"
    assert len(res["transition_trace"]) == 9  # 9 successful state transitions
    assert "CAP-STATE-PERSISTENCE" in res["revalidated_capabilities"]
    assert "archived_entry_id" in res
    assert res["archived_entry_id"] == "ARCHIVE-REVAL-mission_reval_test_1"

    # Verify that capability validation_status was updated to VALIDATED in the registry
    registry.load()
    updated_cap = registry.get_capability("CAP-STATE-PERSISTENCE")
    assert updated_cap is not None
    assert updated_cap.validation_status == "VALIDATED"

    # Verify the ArchiveEntry was promoted durably to the archive
    archive_file = archive_dir / "ARCHIVE-REVAL-mission_reval_test_1.json"
    assert archive_file.exists()

    with open(archive_file, "r") as f:
        entry_data = json.load(f)
    assert entry_data["id"] == "ARCHIVE-REVAL-mission_reval_test_1"
    assert entry_data["tags"] == ["revalidation", "workspace_trace", "governed_execution", "bond_transition"]
    assert entry_data["content"]["overall_success"] is True


def test_bridge_real_ruff_workload(tmp_path):
    """Verify that the bridge executes real-world linter workloads (ruff check) on target files."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"
    dummy_py = tmp_path / "dummy_code.py"
    dummy_py.write_text("def test_func():\n    pass\n")

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    # Run execution with real ruff checks
    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_test_2",
        target_files=[str(dummy_py)],
        run_real_lint=True
    )

    assert res["overall_success"] is True
    assert len(res["execution_results"]) == 1
    exec_res = res["execution_results"][0]
    assert "ruff check" in exec_res["command_run"]
    assert exec_res["success"] is True
    assert "archived_entry_id" in res


def test_bridge_input_immutability(tmp_path):
    """Verify that target_files input list is not mutated during execution."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"
    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    target_files = ["tests/test_continuity_persistence.py", "sage/mission_control.py"]
    target_files_copy = list(target_files)

    bridge.execute_revalidation_workload(
        mission_id="mission_reval_test_3",
        target_files=target_files,
        run_real_lint=False
    )

    assert target_files == target_files_copy


def test_bridge_failure_handling_missing_file(tmp_path):
    """Verify that the bridge handles missing/absent files cleanly without crashing."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"
    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_test_4",
        target_files=["absent_file_not_found.py"],
        run_real_lint=True
    )

    # If the file is missing/absent, the workload overall_success is False, meaning the transition was NOT successful.
    assert res["overall_success"] is False
    assert res["bond_validation"] == "PASS"  # Transition itself technically succeeded but overall_success is false
    assert "archived_entry_id" not in res  # Failing workloads should NOT promote to Master Archive


def test_bridge_successful_bond_transition(tmp_path):
    """Verify that the bridge successfully executes a governed transition and generates a valid cryptographic receipt."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    # Run with standard successful validation score 1.0
    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_success_bond",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False,
        validation_score=1.0
    )

    assert res["bond_validation"] == "PASS"
    assert res["spek_result"] == "APPROVED"
    assert res["state_before"] == "S0"
    assert res["state_after"] == "Delta"
    assert res["overall_success"] is True
    assert res["receipt_id"] != "N/A"
    assert res["receipt_predecessor"] != "N/A"
    assert res["evidence_location"] != "N/A"
    assert "operator_visible_result" in res
    assert "SAGE CONTROL TOWER" in res["operator_visible_result"]

    # Verify that compliance receipt vault has the receipt saved
    assert len(bridge.spek_engine.compliance.vault) >= 1
    receipt = bridge.spek_engine.compliance.vault[-1]
    assert receipt.receipt_id == res["receipt_id"]
    assert receipt.previous_receipt_hash == res["receipt_predecessor"]


def test_bridge_failed_bond_transition_rejection(tmp_path):
    """Verify that a low validation score (<0.7) triggers a REJECTED transition and state rollback to S0."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    # Run with validation score below threshold (e.g., 0.5)
    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_reject_bond",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False,
        validation_score=0.5,
        fail_on_bond_error=False
    )

    # Validate output dict reflecting REJECTION & ROLLBACK state consequences
    assert res["bond_validation"] == "REJECTED"
    assert res["spek_result"] == "REJECTED"
    assert res["state_before"] == "S0"
    assert res["state_after"] == "S0"
    assert res["rollback_state"] is not None
    assert res["rollback_state"]["current_project_state"] == "S0"
    assert res["overall_success"] is False
    assert res["receipt_id"] == "N/A"
    assert res["evidence_location"] == "N/A"

    # Also assert calling with fail_on_bond_error raised exception
    with pytest.raises(BondValidationError) as exc_info:
        bridge.execute_revalidation_workload(
            mission_id="mission_reval_reject_bond_fail",
            target_files=["tests/test_continuity_persistence.py"],
            run_real_lint=False,
            validation_score=0.5,
            fail_on_bond_error=True
        )
    assert exc_info.value.error_code == "CIV-ERR-EXT-004"


def test_bridge_failed_bond_transition_unauthorized(tmp_path):
    """Verify that an unauthorized security boundary violation (bad auth token) fails closed and rolls back state to S0."""
    registry_file = tmp_path / "operational_capability_registry.json"
    archive_dir = tmp_path / "archive"

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(registry_file),
        archive_path=str(archive_dir),
        workspace_path=str(tmp_path)
    )

    # Force a bad token override
    override_payload = {"auth_token": "MALICIOUS_TOKEN_ATTEMPT"}

    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_unauth_bond",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False,
        bond_payload_override=override_payload,
        fail_on_bond_error=False
    )

    assert res["bond_validation"] == "REJECTED"
    assert res["spek_result"] == "BLOCKED_FAIL_CLOSED"
    assert res["state_before"] == "S0"
    assert res["state_after"] == "S0"
    assert res["rollback_state"] is not None
    assert res["rollback_state"]["current_project_state"] == "S0"
    assert res["overall_success"] is False

    # Verify exception is raised if requested
    with pytest.raises(BondValidationError) as exc_info:
        bridge.execute_revalidation_workload(
            mission_id="mission_reval_unauth_bond_fail",
            target_files=["tests/test_continuity_persistence.py"],
            run_real_lint=False,
            bond_payload_override=override_payload,
            fail_on_bond_error=True
        )
    assert exc_info.value.error_code == "CIV-ERR-AUTH-001"
