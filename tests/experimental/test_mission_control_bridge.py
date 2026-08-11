"""Unit and integration tests for SAGE Mission Execution Bridge and Workspace Revalidator.

Verifies the integration of SAGEChangeImpactAnalyzer, SAGEOperationalCapabilityRegistry,
and SAGEMissionProgressionController under real and mock workloads.
"""

import os
import json
import pytest
from pathlib import Path

from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge, WorkloadExecutionResult
from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability
from sage.mission_control import ExperimentalMissionState


def test_bridge_sequential_pipeline_execution(tmp_path):
    """Verify that SAGEMissionExecutionBridge runs the complete sequential 10-stage progression to CLOSED."""
    registry_file = tmp_path / "operational_capability_registry.json"

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

    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file))

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

    # Verify that capability validation_status was updated to VALIDATED in the registry
    registry.load()
    updated_cap = registry.get_capability("CAP-STATE-PERSISTENCE")
    assert updated_cap is not None
    assert updated_cap.validation_status == "VALIDATED"


def test_bridge_real_ruff_workload(tmp_path):
    """Verify that the bridge executes real-world linting workloads (ruff check) on target files."""
    registry_file = tmp_path / "operational_capability_registry.json"
    dummy_py = tmp_path / "dummy_code.py"
    dummy_py.write_text("def test_func():\n    pass\n")

    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file))

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


def test_bridge_input_immutability(tmp_path):
    """Verify that target_files input list is not mutated during execution."""
    registry_file = tmp_path / "operational_capability_registry.json"
    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file))

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
    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file))

    res = bridge.execute_revalidation_workload(
        mission_id="mission_reval_test_4",
        target_files=["absent_file_not_found.py"],
        run_real_lint=True
    )

    # Missing files are handled gracefully; the workload fails, but the mission still transitions cleanly to CLOSED
    assert res["overall_success"] is False
    assert res["final_state"] == "CLOSED"
    assert len(res["revalidated_capabilities"]) == 0
