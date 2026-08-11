"""Unit and regression tests for SAGE ACT-PROD operator dashboard capability."""

import os
import json
import pytest
from pathlib import Path

from sage.experimental.act.act_prod_dashboard import SAGEActProdDashboard
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge


def test_dashboard_operator_summary_retrieval(tmp_path):
    """Verify that SAGEActProdDashboard retrieves correct operator summary and metrics from SAGE Archive."""
    archive_dir = tmp_path / "archive"
    registry_file = tmp_path / "operational_capability_registry.json"

    # 1. Run a revalidation workload to populate the SAGE Archive
    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file), archive_path=str(archive_dir))
    res = bridge.execute_revalidation_workload(
        mission_id="mission_1",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False
    )
    assert res["overall_success"] is True

    # 2. Instantiate dashboard and retrieve summary
    dashboard = SAGEActProdDashboard(archive_path=str(archive_dir))
    summary = dashboard.retrieve_operator_summary()

    assert summary["total_archived_traces"] == 1
    metrics = summary["revalidation_metrics"]
    assert metrics["total_missions_evaluated"] == 1
    assert metrics["successful_revalidations"] == 1
    assert metrics["success_rate_percent"] == 100.0

    active_missions = summary["active_missions"]
    assert len(active_missions) == 1
    assert active_missions[0]["mission_id"] == "mission_1"
    assert active_missions[0]["success"] is True


def test_dashboard_detailed_diagnostics(tmp_path):
    """Verify that SAGEActProdDashboard parses and reports deep diagnostics for a specific archived mission."""
    archive_dir = tmp_path / "archive"
    registry_file = tmp_path / "operational_capability_registry.json"

    # Run revalidation workload
    bridge = SAGEMissionExecutionBridge(registry_path=str(registry_file), archive_path=str(archive_dir))
    bridge.execute_revalidation_workload(
        mission_id="mission_diag_test",
        target_files=["tests/test_continuity_persistence.py"],
        run_real_lint=False
    )

    dashboard = SAGEActProdDashboard(archive_path=str(archive_dir))
    diag = dashboard.retrieve_mission_diagnostics("mission_diag_test")

    assert diag is not None
    assert diag["mission_id"] == "mission_diag_test"
    assert diag["archive_entry_id"] == "ARCHIVE-REVAL-mission_diag_test"
    assert diag["overall_success"] is True
    assert diag["final_state"] == "CLOSED"
    assert diag["validated_by"] == "SAGEMissionExecutionBridge"

    # Assert sequence transition trace is parsed correctly
    assert len(diag["transition_steps"]) == 9
    assert diag["transition_steps"][0]["target_state"] == "VALUE_EVALUATED"
    assert diag["transition_steps"][-1]["target_state"] == "CLOSED"

    # Assert workload executions are captured
    assert len(diag["workload_executions"]) == 1
    assert "mock_check" in diag["workload_executions"][0]["command"]


def test_dashboard_corrupt_data_isolation(tmp_path):
    """Verify that SAGEActProdDashboard identifies, isolates, and survives corrupted JSON trace files in Archive."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write a healthy trace
    healthy_file = archive_dir / "ARCHIVE-REVAL-healthy_trace.json"
    healthy_data = {
        "id": "ARCHIVE-REVAL-healthy_trace",
        "title": "Healthy trace",
        "tags": ["revalidation"],
        "knowledge_state": "archived",
        "content": {"mission_id": "healthy_trace", "overall_success": True}
    }
    healthy_file.write_text(json.dumps(healthy_data))

    # 2. Write a malformed JSON file
    malformed_file1 = archive_dir / "corrupted_file_1.json"
    malformed_file1.write_text("{invalid json...[")

    # 3. Write a json missing minimally required schema keys
    malformed_file2 = archive_dir / "corrupted_file_2.json"
    malformed_file2.write_text(json.dumps({"some_key": "some_value"}))

    dashboard = SAGEActProdDashboard(archive_path=str(archive_dir))

    # Verify summary retrieval does not crash on corrupt JSONs
    summary = dashboard.retrieve_operator_summary()
    assert summary["total_archived_traces"] == 1  # Successfully loaded only the 1 healthy entry
    assert summary["revalidation_metrics"]["total_missions_evaluated"] == 1

    # Verify corrupt file scanner successfully isolates and flags the corrupted files
    corrupt_report = dashboard.handle_corrupted_archive_data()
    assert corrupt_report["status"] == "warning"
    assert corrupt_report["corrupted_count"] == 2

    paths_isolated = [d["file_path"] for d in corrupt_report["details"]]
    assert str(malformed_file1) in paths_isolated
    assert str(malformed_file2) in paths_isolated
