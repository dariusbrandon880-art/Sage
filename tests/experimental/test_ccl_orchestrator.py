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
    FutureAgentEntryContract,
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


def test_hardened_three_role_lifecycle_execution():
    """Validate repeated multi-agent lifecycle including rejections, revisions, re-reviews, and operator decision referencing."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_hardened_loop")

    report = macc.execute_hardened_three_role_lifecycle(
        task_objective="obj_continuous_development",
        milestones=["Formulate multi-agent operational boundaries", "Coordinate secure custody handoffs"]
    )

    assert report["status"] == "VALIDATED"
    assert "chatgpt_coordination" in report
    assert "jules_execution" in report
    assert "claude_review_findings_first" in report
    assert "claude_review_findings_final" in report
    assert "decision_evidence_hash" in report

    # Assert compliance statuses match expected loop transitions
    findings_first = report["claude_review_findings_first"]
    findings_final = report["claude_review_findings_final"]
    assert findings_first["is_compliant"] is False
    assert findings_final["is_compliant"] is True

    # Verify execution traces for loop re-entry
    events = [t["event"] for t in report["execution_traces"]]
    assert "CLAUDE_FIRST_REVIEW_REJECTED" in events
    assert "JULES_REVISION_START" in events
    assert "JULES_REVISION_COMPLETED" in events
    assert "CLAUDE_REREVIEW_START" in events
    assert "CLAUDE_REREVIEW_COMPLETED" in events
    assert "OPERATOR_FINAL_DECISION_COMPLETED" in events


def test_production_reliability_simulation_execution():
    """Validate extended long-running simulation with controlled stale context and handoff failure injections."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_reliability")

    report = macc.execute_production_reliability_simulation(
        task_objective="obj_continuous_development",
        milestones=["Harden multi-agent persistence keys", "Verify fault interception mechanics"]
    )

    assert report["status"] == "VALIDATED"
    assert "future_agent_entry_contract" in report
    assert "failure_recovery_logs" in report
    assert "claude_review_findings" in report

    # Verify onboarding contract contract parameters
    contract = report["future_agent_entry_contract"]
    assert contract["agent_id"] == "agent_gemini_scout"
    assert contract["role"] == "RESEARCHER"

    # Assert recoveries are captured correctly
    rec_logs = report["failure_recovery_logs"]
    assert len(rec_logs) == 2
    types = [l["type"] for l in rec_logs]
    assert "STALE_CONTEXT_OBJECTIVE_DRIFT" in types
    assert "FAILED_HANDOFF_INCONSISTENCY" in types
    assert rec_logs[0]["status"] == "RECOVERED"
    assert rec_logs[1]["status"] == "RECOVERED"

    # Assert traces logged fault recovery resolution events
    events = [t["event"] for t in report["execution_traces"]]
    assert "FAILURE_INJECTION_STALE_CONTEXT_RESOLVED" in events
    assert "FAILURE_INJECTION_FAILED_HANDOFF_RESOLVED" in events


def test_control_tower_status_rendering():
    """Verify operator Control Tower ASCII console layout and parameters."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_control_tower")

    # Pre-populate review findings and recovery logs to test explicit visibility
    macc.orchestrator.session.metadata["latest_review_findings"] = {
        "is_compliant": True,
        "observed_findings": ["All systems compliant."],
        "recommendations": ["No actions required."],
        "verification_hash": "a" * 64
    }
    macc.orchestrator.session.metadata["workflow_state"] = "WORKFLOW_COMPLETE"
    macc.orchestrator.session.metadata["active_blocker"] = "None"
    macc.orchestrator.session.metadata["failure_recovery_logs"] = [
        {"type": "STALE_CONTEXT", "status": "RECOVERED"}
    ]
    macc.orchestrator.session.metadata["future_agent_contract"] = {
        "agent_id": "agent_gemini_scout",
        "role": "RESEARCHER"
    }
    macc.orchestrator.session_manager.save_session(macc.orchestrator.session)

    console_output = macc.render_control_tower_view()

    assert "SAGE CO-ORDINATION CONTROL TOWER CONSOLE" in console_output
    assert "Active Operational Session" in console_output
    assert "Workflow State Transition:  WORKFLOW_COMPLETE" in console_output
    assert "Active Blocker / Friction:  None" in console_output
    assert "SAGE Fault Injection & Recovery State Logs:" in console_output
    assert "Active Recovered Faults:   1" in console_output
    assert "Future Collaborator Contract Inheritance Model:" in console_output
    assert "Onboarding Target Agent:   agent_gemini_scout" in console_output
    assert "Workflow Health Score" in console_output
    assert "Active Collaborator Responsibility Hierarchy" in console_output
    assert "Custody Transfer Handoff Lineage Trail" in console_output
    assert "Governing Claude Auditor Validation Findings" in console_output
    assert "Compliance Status:" in console_output
    assert "Operator Visibility Lineage Answers" in console_output
    assert "Who built it?           Jules" in console_output
    assert "Who reviewed it?        Claude" in console_output
