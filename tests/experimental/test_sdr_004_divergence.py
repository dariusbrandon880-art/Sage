"""Unit test suite for SAGE-SDR-004 State Divergence & Recovery Simulation Foundation."""

import os
import json
import pytest
from datetime import datetime, timezone, timedelta
from sage.experimental.act.sdr_004_divergence import (
    DivergentAgentStateSimulator,
    StateDivergenceDetector,
    RecoveryResolutionWorkflow,
    DivergenceEvidenceGenerator
)


def test_sdr_004_state_cloning_and_validation():
    """Verify state simulator clones base state and enforces contracts."""
    # Invalid session id should fail
    with pytest.raises(ValueError, match="Invalid session_id format"):
        DivergentAgentStateSimulator("invalid_id", ["obj_audit"])

    # Valid initialization
    sim = DivergentAgentStateSimulator("session_sdr004_01", ["obj_audit", "obj_verify"])

    # Task objective must be present in active objectives
    with pytest.raises(ValueError, match="Task objective 'obj_unknown' not in session active objectives"):
        sim.add_base_task("task_01", "obj_unknown", "agent_coord_01")

    # Invalid task id format
    with pytest.raises(ValueError, match="Invalid task_id"):
        sim.add_base_task("invalid_task", "obj_audit", "agent_coord_01")

    # Correct additions
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")
    sim.add_base_task("task_02", "obj_verify", "agent_exec_01")

    assert len(sim.base_tasks) == 2

    # Branch duplication and diverging
    branch_a_update = [
        {
            "task_id": "task_diverged_03",
            "objective_id": "obj_audit",
            "actor_id": "agent_analyst_01",
            "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
            "status": "completed",
            "parent_task_id": "task_01"
        }
    ]
    branch_b_update = [
        {
            "task_id": "task_diverged_03",
            "objective_id": "obj_audit",
            "actor_id": "agent_exec_01",  # Conflict: Mismatched actor_id for same task_id
            "timestamp": (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(),
            "status": "completed",
            "parent_task_id": "task_01"
        }
    ]

    branches = sim.generate_divergent_branches(branch_a_update, branch_b_update)

    assert "branch_a" in branches
    assert "branch_b" in branches
    assert len(branches["branch_a"]["mapped_tasks"]) == 3
    assert len(branches["branch_b"]["mapped_tasks"]) == 3


def test_sdr_004_conflict_detection():
    """Verify that detector correctly identifies all divergent and cyclical anomalies."""
    sim = DivergentAgentStateSimulator("session_sdr004_02", ["obj_audit", "obj_verify"])
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")

    # 1. Test Task Mutation/Override Conflict
    branch_a_up = [
        {
            "task_id": "task_conflict",
            "objective_id": "obj_audit",
            "actor_id": "agent_analyst_01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "parent_task_id": "task_01"
        }
    ]
    branch_b_up = [
        {
            "task_id": "task_conflict",
            "objective_id": "obj_audit",
            "actor_id": "agent_exec_01",  # Conflicting actor_id
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress",      # Conflicting status
            "parent_task_id": "task_01"
        }
    ]

    branches = sim.generate_divergent_branches(branch_a_up, branch_b_up)

    detector = StateDivergenceDetector()
    report = detector.detect_conflicts(branches["branch_a"], branches["branch_b"])

    assert report["conflicts_found"] == 1
    assert report["status"] == "CONFL_DETECTED"
    assert report["conflicts"][0]["conflict_type"] == "TASK_MUTATION_OVERRIDE"
    assert set(report["conflicts"][0]["fields_mismatched"]) == {"actor_id", "status"}


def test_sdr_004_relational_loops_and_objective_mismatch():
    """Verify that detector catches objective alignment violations and relational loop cycles."""
    sim = DivergentAgentStateSimulator("session_sdr004_03", ["obj_audit"])
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")

    # 1. Relational Loop where task points to itself as parent
    branch_a_up = [
        {
            "task_id": "task_loop",
            "objective_id": "obj_audit",
            "actor_id": "agent_exec_01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "parent_task_id": "task_loop"  # Cyclic self-reference loop
        }
    ]
    # 2. Objective Mismatch where task points to non-active objective
    branch_b_up = [
        {
            "task_id": "task_mismatch",
            "objective_id": "obj_verify",  # Conflicting objective mismatch (not active)
            "actor_id": "agent_exec_01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "parent_task_id": "task_01"
        }
    ]

    branches = sim.generate_divergent_branches(branch_a_up, branch_b_up)

    detector = StateDivergenceDetector()
    report = detector.detect_conflicts(branches["branch_a"], branches["branch_b"])

    # Expecting objective mismatch (conflict) and cyclical loop (anomaly)
    assert report["anomalies_found"] == 1
    assert report["conflicts_found"] == 1
    assert report["anomalies"][0]["anomaly_type"] == "RELATIONAL_LOOP_DETECTED"
    assert report["conflicts"][0]["conflict_type"] == "OBJECTIVE_ALIGNMENT_VIOLATION"


def test_sdr_004_resolution_strategies():
    """Verify chronological priority and authority priority resolution merging."""
    sim = DivergentAgentStateSimulator("session_sdr004_04", ["obj_audit"])
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")

    time_early = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    time_late = datetime.now(timezone.utc).isoformat()

    branch_a_up = [
        {
            "task_id": "task_conflict",
            "objective_id": "obj_audit",
            "actor_id": "agent_analyst_01",
            "timestamp": time_early,
            "status": "completed",
            "parent_task_id": "task_01"
        }
    ]
    branch_b_up = [
        {
            "task_id": "task_conflict",
            "objective_id": "obj_audit",
            "actor_id": "agent_exec_01",
            "timestamp": time_late,
            "status": "in_progress",
            "parent_task_id": "task_01"
        }
    ]

    branches = sim.generate_divergent_branches(branch_a_up, branch_b_up)
    workflow = RecoveryResolutionWorkflow()

    # 1. Test CHRONOLOGICAL_PRIORITY (should select the early update)
    res_chrono = workflow.resolve_divergence(branches["branch_a"], branches["branch_b"], "CHRONOLOGICAL_PRIORITY")
    assert res_chrono["status"] == "RESOLVED"
    assert res_chrono["strategy"] == "CHRONOLOGICAL_PRIORITY"
    resolved_tasks = {t["task_id"]: t for t in res_chrono["resolved_tasks"]}
    assert resolved_tasks["task_conflict"]["actor_id"] == "agent_analyst_01"
    assert resolved_tasks["task_conflict"]["timestamp"] == time_early

    # 2. Test AUTHORITY_PRIORITY (Coordinator > Reviewer > Analyst > Executor)
    # branch_a_up has agent_analyst_01, branch_b_up has agent_exec_01 (Analyst wins over Executor)
    res_auth = workflow.resolve_divergence(branches["branch_a"], branches["branch_b"], "AUTHORITY_PRIORITY")
    assert res_auth["status"] == "RESOLVED"
    resolved_tasks_auth = {t["task_id"]: t for t in res_auth["resolved_tasks"]}
    assert resolved_tasks_auth["task_conflict"]["actor_id"] == "agent_analyst_01"

    # Swap branch_b to be a coordinator (Coordinator wins over Analyst)
    branches["branch_b"]["mapped_tasks"][-1]["actor_id"] = "agent_coord_01"
    res_auth_coord = workflow.resolve_divergence(branches["branch_a"], branches["branch_b"], "AUTHORITY_PRIORITY")
    resolved_tasks_auth_coord = {t["task_id"]: t for t in res_auth_coord["resolved_tasks"]}
    assert resolved_tasks_auth_coord["task_conflict"]["actor_id"] == "agent_coord_01"


def test_sdr_004_human_gate_escalation():
    """Verify that simulated human approval checkpoints hold execution until authorization."""
    sim = DivergentAgentStateSimulator("session_sdr004_05", ["obj_audit"])
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")

    branch_a_up = [{"task_id": "task_conf", "objective_id": "obj_audit", "actor_id": "agent_exec_01", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "completed", "parent_task_id": "task_01"}]
    branch_b_up = [{"task_id": "task_conf", "objective_id": "obj_audit", "actor_id": "agent_analyst_01", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "completed", "parent_task_id": "task_01"}]

    branches = sim.generate_divergent_branches(branch_a_up, branch_b_up)
    workflow = RecoveryResolutionWorkflow()

    # Should pause without human override input
    res_held = workflow.resolve_divergence(branches["branch_a"], branches["branch_b"], "HUMAN_GATE_ESCALATION")
    assert res_held["status"] == "HELD_FOR_HUMAN_APPROVAL"
    assert len(res_held["resolved_tasks"]) == 0

    # Supply simulated human approval
    override_input = {
        "checkpoint_id": "chk_sdr004_override_01",
        "approved_tasks": [
            {
                "task_id": "task_conf",
                "objective_id": "obj_audit",
                "actor_id": "human_supervisor_01",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "parent_task_id": "task_01"
            }
        ]
    }
    res_override = workflow.resolve_divergence(
        branches["branch_a"], branches["branch_b"], "HUMAN_GATE_ESCALATION", human_decision_override=override_input
    )
    assert res_override["status"] == "RESOLVED"
    assert res_override["strategy"] == "HUMAN_GATE_ESCALATION"
    assert len(res_override["resolved_tasks"]) == 1
    assert res_override["resolved_tasks"][0]["actor_id"] == "human_supervisor_01"


def test_sdr_004_evidence_packaging(tmp_path):
    """Verify evidence structure generation and compliant serialization."""
    sim = DivergentAgentStateSimulator("session_sdr004_06", ["obj_audit"])
    sim.add_base_task("task_01", "obj_audit", "agent_coord_01")

    branch_a_up = [{"task_id": "task_conf", "objective_id": "obj_audit", "actor_id": "agent_exec_01", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "completed", "parent_task_id": "task_01"}]
    branch_b_up = [{"task_id": "task_conf", "objective_id": "obj_audit", "actor_id": "agent_analyst_01", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "completed", "parent_task_id": "task_01"}]

    branches = sim.generate_divergent_branches(branch_a_up, branch_b_up)
    detector = StateDivergenceDetector()
    conflict_report = detector.detect_conflicts(branches["branch_a"], branches["branch_b"])

    workflow = RecoveryResolutionWorkflow()
    res_report = workflow.resolve_divergence(branches["branch_a"], branches["branch_b"], "CHRONOLOGICAL_PRIORITY")

    # Generate evidence in temporary test file
    evidence_file = tmp_path / "sdr_004_divergence_resolution_evidence.json"
    generator = DivergenceEvidenceGenerator(output_path=str(evidence_file))

    evidence_pack = generator.package_evidence(branches, conflict_report, res_report)

    # Verify structural and formatting invariants (Option B metadata & non-absolute vocabulary compliance)
    assert "simulation_id" in evidence_pack
    assert "timestamp" in evidence_pack
    assert "divergence_details" in evidence_pack
    assert "conflict_detection_report" in evidence_pack
    assert "resolution_details" in evidence_pack
    assert "cryptographic_continuity_proofs" in evidence_pack
    assert "boundary_integrity_verification" in evidence_pack
    assert "observed_results" in evidence_pack

    # Read from output file
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded_evidence = json.load(f)

    assert loaded_evidence["simulation_id"] == evidence_pack["simulation_id"]
    assert loaded_evidence["boundary_integrity_verification"]["sage_runtime_untouched"] is True
