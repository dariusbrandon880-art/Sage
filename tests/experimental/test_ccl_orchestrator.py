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
    SAGEImprovementCandidate,
    SAGEIncidentReport,
    PMLStateRecord,
    PersistentMissionLedger,
    SAGEWorkflowPattern,
    SAGEOperationalRecommendation,
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


def test_controlled_operational_pilot_execution():
    """Validate end-to-end controlled operational pilot with metrics collection and improvement discovery."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_pilot")

    report = macc.execute_controlled_operational_pilot(
        task_objective="obj_continuous_development",
        milestones=["Formulate multi-agent operational boundaries", "Coordinate secure custody handoffs"]
    )

    assert report["status"] == "VALIDATED"
    assert "pilot_operational_metrics" in report
    assert "discovered_improvements" in report
    assert "chatgpt_coordination" in report
    assert "jules_execution" in report
    assert "claude_review_findings" in report

    # Validate pilot metrics structure and constraints
    metrics = report["pilot_operational_metrics"]
    assert metrics["workflow_duration_seconds"] >= 0.0
    assert metrics["context_recovery_effectiveness_pct"] == 100.0
    assert metrics["duplicate_work_avoided_lines_bypassed"] == 150
    assert metrics["evidence_quality_index"] == 1.0
    assert metrics["operator_visibility_score_answers_present"] == 5
    assert metrics["recovery_effectiveness_pct"] == 100.0

    # Validate improvements
    imps = report["discovered_improvements"]
    assert len(imps) == 1
    assert "pre-commit lint triggers" in imps[0]


def test_operational_intelligence_optimization_execution():
    """Validate end-to-end Operational Intelligence Layer (OIL) with prioritized candidates and immune-inspired isolate reports."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_macc_oil")

    report = macc.execute_operational_intelligence_optimization(
        task_objective="obj_continuous_development",
        milestones=["Verify immune-inspired tests", "Harden velocity telemetry pipelines"]
    )

    assert report["status"] == "VALIDATED"
    assert "oil_metrics" in report
    assert "latest_oil_incident" in report
    assert "latest_oil_improvement" in report
    assert "chatgpt_coordination" in report
    assert "jules_execution" in report
    assert "claude_review_findings" in report

    # Assert incident properties
    inc = report["latest_oil_incident"]
    assert inc["affected_component"] == "DeveloperWorkflowOrchestrator"
    assert "automated post-build metrics validation" in inc["failure_condition"]

    # Assert prioritized candidate scoring
    imp = report["latest_oil_improvement"]
    assert imp["opportunity_type"] == "OPERATIONAL_EFFICIENCY"
    assert imp["priority_score"] == 11.33  # (8.5 + 9.0 + 9.5 + 10.0 - 3.0) / 3.0 = 11.33

    # Assert OIL formula metrics are present
    metrics = report["oil_metrics"]
    assert metrics["mission_velocity_index"] == 2.3
    assert metrics["context_preservation_score_pct"] == 100.0
    assert metrics["recovery_intelligence_score_pct"] == 100.0
    assert metrics["evidence_density_index"] == 1.0
    assert metrics["improvement_compounding_rate_pct"] == 12.5


def test_persistent_mission_ledger_controlled_slice():
    """Validate PML State Record serialization, file storage, and rehydration path."""
    pml = PersistentMissionLedger(ledger_dir="sage_data/test_pml")

    record = PMLStateRecord(
        session_id="session_test_pml_serialization",
        active_owner_id="agent_jules_sage",
        workflow_state="ENGINEERING_BUILD",
        milestones_summary=[{"action": "Coordinate", "status": "COMPLETED"}],
        evidence_references=["CCL-REC-992"],
        workspace_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        required_next_action="Audit Validation"
    )

    filepath = pml.save_mission_state(record)
    assert filepath.exists()

    rehydrated = pml.load_mission_state(record.session_id)
    assert rehydrated is not None
    assert rehydrated.session_id == record.session_id
    assert rehydrated.active_owner_id == record.active_owner_id
    assert rehydrated.workspace_checksum == record.workspace_checksum

    # Clean up test PML state file
    if filepath.exists():
        filepath.unlink()


def test_bottleneck_detection_and_advisory_recommendations():
    """Validate pattern matching and generation of actionable advisory recommendations."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_bottleneck")

    # Pre-populate session with uncommitted files (by mocking workspace scan)
    res = macc.generate_operational_recommendations()
    assert "detected_patterns" in res
    assert "generated_recommendations" in res


def test_endurance_compounding_simulation_execution():
    """Validate successive long-running multi-cycle loop with compounding velocity improvements and PML saves."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_endurance_loop")

    report = macc.execute_endurance_simulation_run(
        task_objective="obj_continuous_development",
        milestones=["Harden multi-agent persistence keys", "Verify fault interception mechanics"]
    )

    assert report["status"] == "VALIDATED"
    assert "endurance_report" in report

    # Verify compounding metrics
    metrics = report["endurance_report"]["aggregate_performance"]
    assert metrics["total_pml_states_written"] == 3
    assert metrics["average_cycle_duration_seconds"] > 0.0
    assert metrics["compound_velocity_improvement_pct"] > 0.0
    assert metrics["duplicate_setup_bypassed_lines"] == 450  # 75 + 150 + 225 = 450


def test_manual_mode_emergency_stop_override():
    """Verify that creating the EMERGENCY_STOP lockfile immediately halts loops and raises a controlled exception."""
    macc = SAGEOperationalOrchestrator(session_id="session_test_emergency")

    # Create the root emergency lockfile
    lockfile = Path("EMERGENCY_STOP")
    with open(lockfile, "w") as f:
        f.write("STOP RUN")

    try:
        # Loop invocation must raise RuntimeError
        with pytest.raises(RuntimeError) as exc:
            macc.execute_controlled_operational_pilot(
                task_objective="obj_continuous_development",
                milestones=["Harden safety lines"]
            )
        assert "Manual operator emergency freeze" in str(exc.value)
    finally:
        # Always clean up the lockfile
        if lockfile.exists():
            lockfile.unlink()


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
    macc.orchestrator.session.metadata["pilot_operational_metrics"] = {
        "workflow_duration_seconds": 12.34,
        "context_recovery_effectiveness_pct": 100.0,
        "duplicate_work_avoided_lines_bypassed": 150,
        "evidence_quality_index": 1.0
    }
    macc.orchestrator.session.metadata["discovered_improvements"] = ["Add automated lint checks."]
    macc.orchestrator.session.metadata["oil_metrics_dashboard"] = {
        "mission_velocity_index": 2.3,
        "context_preservation_score_pct": 100.0,
        "recovery_intelligence_score_pct": 100.0,
        "evidence_density_index": 1.0,
        "improvement_compounding_rate_pct": 12.5
    }
    macc.orchestrator.session.metadata["endurance_report_dashboard"] = {
        "aggregate_performance": {
            "average_cycle_duration_seconds": 3.9,
            "compound_velocity_improvement_pct": 42.0,
            "duplicate_setup_bypassed_lines": 450,
            "total_pml_states_written": 3
        }
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
    assert "Pilot Captured Operational Metrics & Performance:" in console_output
    assert "Workflow Duration:       12.34s" in console_output
    assert "Context Recovery:        100.0%" in console_output
    assert "Duplicate Work Avoided:  150 lines setup" in console_output
    assert "Evidence Quality Index:  1.0" in console_output
    assert "Discovered Improvements: Add automated lint checks." in console_output
    assert "SAGE Operational Intelligence Layer (OIL) Performance:" in console_output
    assert "Mission Velocity Index (MVI):  2.3x cycle speedup" in console_output
    assert "Context Preservation (CPS):    100.0%" in console_output
    assert "Recovery Intelligence (RIS):   100.0%" in console_output
    assert "Evidence Density Index (ED):   1.0" in console_output
    assert "Improvement Compounding (ICR): 12.5% rate" in console_output
    assert "SAGE Multi-Cycle Learning Compounding (How SAGE Improves):" in console_output
    assert "Avg Cycle Duration:     3.9s" in console_output
    assert "Compounding Improvement: 42.0% cycle speedup" in console_output
    assert "Duplicate Setup Bypassed: 450 lines bypass" in console_output
    assert "Persistent PML States:   3 files written" in console_output
    assert "Workflow Health Score" in console_output
    assert "Active Collaborator Responsibility Hierarchy" in console_output
    assert "Custody Transfer Handoff Lineage Trail" in console_output
    assert "Governing Claude Auditor Validation Findings" in console_output
    assert "Compliance Status:" in console_output
    assert "Operator Visibility Lineage Answers" in console_output
    assert "Who built it?           Jules" in console_output
    assert "Who reviewed it?        Claude" in console_output
