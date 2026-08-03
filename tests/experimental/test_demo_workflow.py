"""Unit test suite for SAGE First repeatable User Demonstration Workflow."""

import os
import json
import pytest
from sage.experimental.act.demo_workflow import DemoWorkflowOrchestrator


def test_demo_workflow_clean_path(tmp_path):
    """Verify end-to-end demonstration workflow on a clean workspace."""
    evidence_file = tmp_path / "demo_workflow_evidence.json"
    orchestrator = DemoWorkflowOrchestrator(output_path=str(evidence_file))

    files = ["src/app.py", "docs/index.md"]
    receipt = orchestrator.run_workflow(files)

    # Invariants
    assert receipt["workflow_stages"]["intake"]["status"] == "COMPLETED"
    assert receipt["workflow_stages"]["intake"]["files_count"] == 2
    assert receipt["workflow_stages"]["evaluation"]["status"] == "CLEAN_WORKSPACE"
    assert receipt["workflow_stages"]["checkpoint"]["decision_state"] == "AUTO_AUTHORIZED"
    assert receipt["observed_results"]["violations_intercepted"] == 0
    assert receipt["observed_results"]["is_held"] == 0
    assert receipt["boundary_integrity_verification"]["sage_runtime_untouched"] is True

    # Check dashboard lines are generated
    assert len(receipt["dashboard_rendering"]) > 0
    dashboard_text = "\n".join(receipt["dashboard_rendering"])
    assert "SAGE ENTERPRISE INTERACTIVE WORKFLOW DASHBOARD" in dashboard_text
    assert "AUTO_AUTHORIZED" in dashboard_text

    # Check file persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["demonstration_id"] == receipt["demonstration_id"]


def test_demo_workflow_violating_held_path(tmp_path):
    """Verify workflow holds execution if protected files are touched and no override exists."""
    evidence_file = tmp_path / "demo_workflow_evidence.json"
    orchestrator = DemoWorkflowOrchestrator(output_path=str(evidence_file))

    files = ["sage/core/spek.py"]
    receipt = orchestrator.run_workflow(files)

    assert receipt["workflow_stages"]["evaluation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert receipt["workflow_stages"]["evaluation"]["violations_found"] == 1
    assert receipt["workflow_stages"]["checkpoint"]["decision_state"] == "HELD_FOR_HUMAN_APPROVAL"
    assert receipt["observed_results"]["violations_intercepted"] == 1
    assert receipt["observed_results"]["is_held"] == 1


def test_demo_workflow_violating_override_path(tmp_path):
    """Verify workflow applies supervisor decisions when overrides are supplied."""
    evidence_file = tmp_path / "demo_workflow_evidence.json"
    orchestrator = DemoWorkflowOrchestrator(output_path=str(evidence_file))

    files = ["sage/runtime/engine.py"]
    override = {
        "decision": "AUTHORIZED",
        "supervisor_id": "human_supervisor_99",
        "comments": "Explicit supervisor patch override approved."
    }
    receipt = orchestrator.run_workflow(files, supervisor_override=override)

    assert receipt["workflow_stages"]["evaluation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert receipt["workflow_stages"]["checkpoint"]["decision_state"] == "AUTHORIZED"
    assert receipt["workflow_stages"]["checkpoint"]["supervisor_id"] == "human_supervisor_99"
    assert receipt["workflow_stages"]["checkpoint"]["action_taken"] == "COMMIT_APPROVED"
    assert receipt["observed_results"]["violations_intercepted"] == 1
    assert receipt["observed_results"]["is_held"] == 0
