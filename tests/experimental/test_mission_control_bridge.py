"""Validation tests for SAGEMissionExecutionBridge.

Verifies the complete real workspace -> impact analysis -> revalidation -> result -> measurement execution flow.
"""

import os
import json
import pytest
import shutil
from pathlib import Path

from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge, WorkloadResult, CapabilityRevalidationRecord
from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability


@pytest.fixture
def test_setup(tmp_path):
    """Isolates the operational registry for test runs."""
    original_registry = Path("evidence_capture/operational_capability_registry.json")
    temp_registry = tmp_path / "operational_capability_registry.json"

    # Copy the registry to allow modifications without affecting workspace baseline
    shutil.copy(original_registry, temp_registry)

    # Output lineage file path
    lineage_file = tmp_path / "session_1_execution_lineage.json"

    return {
        "registry_path": str(temp_registry),
        "lineage_path": str(lineage_file)
    }


def test_mission_control_bridge_end_to_end(test_setup):
    """Execute and verify the full end-to-end pipeline through SAGEMissionExecutionBridge."""
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]

    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)

    # We select tests/test_continuity_bridge.py which is modified
    modified_files = ["tests/test_continuity_bridge.py"]

    # Execute the bridge pipeline
    report = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-test-bridge-revalidation",
        lineage_output_path=lineage_path
    )

    # 1. Assert overall pipeline outcome structure
    assert "git_head_hash" in report
    assert report["changed_artifacts"] == modified_files
    assert "predicted_impact" in report
    assert "selected_workloads" in report
    assert "actual_results" in report
    assert "state_progression" in report
    assert "predicted_vs_observed" in report
    assert "telemetry" in report

    # 2. Check impact prediction matching ChangeImpactReport
    predicted_impact = report["predicted_impact"]
    assert predicted_impact["revalidation_required"] is True

    caps = predicted_impact["impacted_capabilities"]
    bridge_cap = next(c for c in caps if c["capability_id"] == "CAP-CONTINUITY-BRIDGE")
    assert bridge_cap["classification"] == "REVALIDATION_REQUIRED"

    # 3. Check selected workloads executed
    workloads = report["selected_workloads"]
    assert len(workloads) == 1
    workload = workloads[0]
    assert workload["capability_id"] == "CAP-CONTINUITY-BRIDGE"
    assert workload["status_updated_to"] == "VALIDATED"

    # Lint check result
    assert workload["lint_result"] is not None
    assert workload["lint_result"]["success"] is True
    assert workload["lint_result"]["returncode"] == 0

    # Test execution result
    assert workload["test_result"] is not None
    assert workload["test_result"]["success"] is True
    assert workload["test_result"]["returncode"] == 0

    # 4. Check capability registry update
    updated_registry = SAGEOperationalCapabilityRegistry(storage_path=registry_path)
    cap = updated_registry.get_capability("CAP-CONTINUITY-BRIDGE")
    assert cap is not None
    assert cap.validation_status == "VALIDATED"

    # 5. Check State Progression of Mission Progression Controller
    state_progression = report["state_progression"]
    assert state_progression["mission_id"] == "msn-test-bridge-revalidation"
    assert state_progression["terminal_state"] == "CLOSED"

    transitions = state_progression["transitions"]
    assert len(transitions) == 9
    assert transitions[-1]["target_state"] == "CLOSED"
    assert all(t["success"] is True for t in transitions)
    assert all(t["transitioned"] is True for t in transitions)

    # 6. Check Predicted-vs-Observed comparison
    pred_vs_obs = report["predicted_vs_observed"]
    assert pred_vs_obs["predicted_revalidation_required"] is True
    assert len(pred_vs_obs["observed_impacts"]) == 1
    assert pred_vs_obs["observed_impacts"][0]["capability_id"] == "CAP-CONTINUITY-BRIDGE"
    assert pred_vs_obs["observed_impacts"][0]["revalidated"] is True

    # 7. Check written file on disk
    assert os.path.exists(lineage_path)
    with open(lineage_path, "r") as f:
        saved_report = json.load(f)
    assert saved_report["telemetry"]["evidence_receipt_id"] == report["telemetry"]["evidence_receipt_id"]
