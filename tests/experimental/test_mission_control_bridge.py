"""Unit and integration tests for the SAGE Mission Execution Bridge.

Verifies secure workload execution, sequential mission control transitions,
and dynamic operational capability registry revalidation and status updates.
"""

import os
import json
import pytest
from pathlib import Path

from sage.experimental.mission_control_bridge import (
    SAGEMissionExecutionBridge,
    SAGEWorkloadRequest,
    SAGEWorkloadResult
)
from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability


@pytest.fixture
def temp_registry(tmp_path):
    """Fixture to create a temporary operational capability registry for isolated testing."""
    registry_file = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))

    # Pre-populate registry with mock capabilities matching our baseline tests
    registry.add_capability(
        SAGECapability(
            capability_id="CAP-STATE-PERSISTENCE",
            name="State Persistence",
            description="Continuous, atomic serialization of active objectives and task states.",
            implementation_status="IMPLEMENTED",
            validation_status="UNVERIFIED",  # Start as unverified to test revalidation update
            evidence_references=["evidence_capture/ccl_operational_feedback.json"],
            test_references=["tests/test_continuity_persistence.py"],
            archive_promotion_status="READY"
        )
    )
    return registry_file


def test_execute_empty_workload(temp_registry, tmp_path):
    """Verify that a workload request with zero target files completes cleanly with appropriate metrics."""
    evidence_file = tmp_path / "workspace_revalidation_evidence.json"
    bridge = SAGEMissionExecutionBridge(
        registry_path=str(temp_registry),
        evidence_path=str(evidence_file)
    )

    request = SAGEWorkloadRequest(
        task_id="task_empty_test",
        target_files=["non_existent_file_a.py"]
    )

    result = bridge.execute_workload(request)
    assert result.task_id == "task_empty_test"
    assert result.status == "COMPLETED"
    assert "No existing target files" in result.output_log
    assert result.metrics["files_checked"] == 0
    assert "duration_ms" in result.metrics


def test_execute_real_linting_workload(temp_registry, tmp_path):
    """Verify executing a linting workload on an actual file inside the workspace."""
    evidence_file = tmp_path / "workspace_revalidation_evidence.json"
    bridge = SAGEMissionExecutionBridge(
        registry_path=str(temp_registry),
        evidence_path=str(evidence_file)
    )

    # Use a real file that exists
    test_file = "sage/change_impact.py"
    request = SAGEWorkloadRequest(
        task_id="task_real_file_test",
        target_files=[test_file]
    )

    result = bridge.execute_workload(request)
    assert result.task_id == "task_real_file_test"
    assert result.status in ["COMPLETED", "FAILED"]  # Could be FAILED if ruff has complaints, which is valid
    assert result.metrics["files_checked"] == 1


def test_execute_governed_cycle_sequential_transitions(temp_registry, tmp_path):
    """Verify that execute_governed_cycle successfully runs the full sequential mission progression.

    It must drive the state to CLOSED and update affected capability validation status.
    """
    evidence_file = tmp_path / "workspace_revalidation_evidence.json"
    bridge = SAGEMissionExecutionBridge(
        registry_path=str(temp_registry),
        evidence_path=str(evidence_file)
    )

    # Modify a file related to our registered mock capability CAP-STATE-PERSISTENCE
    modified_files = ["tests/test_continuity_persistence.py"]

    # First, verify status is UNVERIFIED in registry
    initial_registry = SAGEOperationalCapabilityRegistry(storage_path=str(temp_registry))
    cap_before = initial_registry.get_capability("CAP-STATE-PERSISTENCE")
    assert cap_before is not None
    assert cap_before.validation_status == "UNVERIFIED"

    # Run the governed cycle
    report = bridge.execute_governed_cycle(modified_files, task_id="task_reval_cycle_test")

    # Assert output schema matches evidence lineage expectations
    assert report["task_id"] == "task_reval_cycle_test"
    assert report["mission_id"] == "mission_task_reval_cycle_test"
    assert report["changed_files"] == modified_files
    assert report["impact_evaluation"]["revalidation_required"] is True
    assert "CAP-STATE-PERSISTENCE" in report["impact_evaluation"]["affected_capabilities"]
    assert report["progression_state"]["terminal_state"] == "CLOSED"
    assert report["metrics"]["capabilities_updated_count"] == 1
    assert report["metrics"]["prediction_vs_observed_impact"]["predicted_revalidation_needed"] is True
    assert "CAP-STATE-PERSISTENCE" in report["metrics"]["prediction_vs_observed_impact"]["observed_capabilities_revalidated"]

    # Verify capability validation status is updated to VALIDATED inside the capability registry file
    updated_registry = SAGEOperationalCapabilityRegistry(storage_path=str(temp_registry))
    cap_after = updated_registry.get_capability("CAP-STATE-PERSISTENCE")
    assert cap_after is not None
    assert cap_after.validation_status == "VALIDATED"

    # Verify that the complete evidence file is serialized correctly to disk
    assert evidence_file.exists()
    with open(evidence_file, "r") as f:
        stored_report = json.load(f)
    assert stored_report["task_id"] == "task_reval_cycle_test"
    assert stored_report["git_head_commit"] != ""
