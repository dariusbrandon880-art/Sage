"""Tests for SAGE Multi-Agent Operational Orchestrator (SAGE-MACC Core)."""

import os
import json
from pathlib import Path
import pytest

from sage.experimental.act.continuity_control import (
    DeveloperWorkflowOrchestrator,
    AgentProgressUpdate,
)
from sage.experimental.act.ccl_orchestrator import (
    SAGEOperationalOrchestrator,
    OperationalStateWindow,
)


def test_orchestrator_initialization():
    """Verify connectors and underlying orchestrator are set up correctly on init."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_init")
    assert macc.chatgpt is not None
    assert macc.jules is not None
    assert macc.claude is not None
    assert macc.orchestrator.session_id == "session_test_macc_init"


def test_two_role_coordination_and_recovery_loop():
    """Validate full multi-agent scenario loop including custody transfers, rehydration, and review contract."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_loop")

    # Run the loop with recovery simulation enabled
    report = macc.execute_two_role_coordination_and_recovery_loop(
        task_objective="obj_continuous_development",
        milestones=["Task 1", "Task 2"],
        simulate_recovery=True
    )

    assert report["status"] == "VALIDATED"
    assert "chatgpt_coordination" in report
    assert "jules_execution" in report
    assert "claude_review_findings" in report
    assert "review_contract" in report

    # Assert execution traces exist
    traces = report["execution_traces"]
    events = [t["event"] for t in traces]
    assert "CHATGPT_COORDINATE_START" in events
    assert "HANDOFF_CHATGPT_TO_JULES_START" in events
    assert "RECOVERY_SIMULATION_INTERRUPT" in events
    assert "RECOVERY_SIMULATION_RESUMED" in events
    assert "CLAUDE_REVIEW_START" in events
    assert "HANDOFF_JULES_TO_CLAUDE_START" in events
    assert "CLAUDE_REVIEW_COMPLETED" in events
    assert "HUMAN_OPERATOR_DECISION_START" in events

    # Assert 8-field complete context window properties
    contract = report["review_contract"]
    inherited = contract["inherited_state"]
    assert "active_mission" in inherited
    assert "workflow_state" in inherited
    assert "milestones" in inherited
    assert "scope" in inherited
    assert "repo_context" in inherited
    assert "blockers" in inherited
    assert "required_actions" in inherited
    assert "evidence_history" in inherited


def test_control_tower_status_rendering():
    """Verify operator Control Tower ASCII console layout and parameters."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_control_tower")

    # Pre-populate review findings to test explicit visibility
    macc.orchestrator.session.metadata["latest_review_findings"] = {
        "is_compliant": True,
        "observed_findings": ["All systems compliant."],
        "recommendations": ["No actions required."],
        "verification_hash": "a" * 64
    }
    macc.orchestrator.session_manager.save_session(macc.orchestrator.session)

    console_output = macc.render_control_tower_view()

    assert "SAGE CO-ORDINATION CONTROL TOWER CONSOLE" in console_output
    assert "Active Operational Session" in console_output
    assert "Workflow Health Score" in console_output
    assert "Active Collaborator Responsibility Hierarchy" in console_output
    assert "Custody Transfer Handoff Lineage Trail" in console_output
    assert "Governing Claude Auditor Validation Findings" in console_output
    assert "Compliance Status:" in console_output
    assert "Operator Visibility Lineage Answers" in console_output
    assert "Who built it?           Jules" in console_output
    assert "Who reviewed it?        Claude" in console_output
