"""SAGE Agent Activation Readiness Pilot Simulation Tests."""

import json
import pytest
from pathlib import Path
from sage.experimental.act import AgentPilotSimulation


def test_agent_pilot_success_lifecycle():
    """Verify that the success path of the controlled experimental agent lifecycle executes cleanly."""
    sim = AgentPilotSimulation()
    assert sim.state == "PROPOSED"

    # 1. Register Mock Agent
    reg = sim.register_agent("agent_jules_01", "cap_file_indexing")
    assert reg["state"] == "PROPOSED"
    assert reg["agent_id"] == "agent_jules_01"
    assert reg["capability_id"] == "cap_file_indexing"

    # 2. Activate Sandbox (Identity & Capability Verification)
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "chatgpt_coordinator",
        "receiver_identity": "jules_executor",
        "task_objective": "Index experimental artifacts",
        "authorized_capability": "cap_file_indexing",
    }
    act = sim.activate_sandbox(
        sender="chatgpt_coordinator",
        receiver="jules_executor",
        envelope=envelope,
    )
    assert act["state"] == "SANDBOX_ACTIVE"
    assert sim.identity_verified
    assert sim.capability_authorized

    # 3. Constrained Sandbox Task Execution (EVALUATED)
    task_payload = {"action": "write_index", "expired_token": False}
    exec_res = sim.execute_sandbox_task("sage/experimental/pilot_run.json", task_payload)
    assert exec_res["state"] == "EVALUATED"
    assert "Execution output trace" in exec_res["execution_trace"]
    assert exec_res["receipt"]["validation_result"] == "PASSED"

    # 4. Human Review Checkpoint Simulation (AUTHORIZED_EXPERIMENTAL)
    app_res = sim.approve_capability(
        reviewer="human_supervisor_01",
        decision="APPROVED",
        reference="SAGE-RFC-PILOT-2026",
    )
    assert app_res["state"] == "AUTHORIZED_EXPERIMENTAL"
    assert app_res["review_record"]["review_decision"] == "APPROVED"

    # 5. Controlled Revocation Test (REVOKED)
    rev_res = sim.revoke_capability()
    assert rev_res["state"] == "REVOKED"
    assert rev_res["block_future_activation"]

    # 6. Attempt future activation must fail
    with pytest.raises(PermissionError, match="Revoked capability prevents activation"):
        sim.reset()
        sim.register_agent("agent_jules_01", "cap_file_indexing")
        sim.revoke_capability()
        sim.activate_sandbox("chatgpt_coordinator", "jules_executor", envelope)


def test_agent_pilot_failure_invalid_identity():
    """Verify that activation with invalid identity throws Failure Validation error."""
    sim = AgentPilotSimulation()
    sim.register_agent("agent_jules_01", "cap_file_indexing")
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "malicious_actor",
        "receiver_identity": "jules_executor",
        "task_objective": "Hack enclaves",
        "authorized_capability": "cap_file_indexing",
    }
    with pytest.raises(ValueError, match="Invalid identity check"):
        sim.activate_sandbox("malicious_actor", "jules_executor", envelope)


def test_agent_pilot_failure_unauthorized_capability():
    """Verify that activation with mismatched capability throws Failure Validation error."""
    sim = AgentPilotSimulation()
    sim.register_agent("agent_jules_01", "cap_file_indexing")
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "chatgpt_coordinator",
        "receiver_identity": "jules_executor",
        "task_objective": "Access unapproved tools",
        "authorized_capability": "cap_unapproved_access",
    }
    with pytest.raises(ValueError, match="Unauthorized capability requested"):
        sim.activate_sandbox("chatgpt_coordinator", "jules_executor", envelope)


def test_agent_pilot_failure_expired_permission():
    """Verify that execution with expired credentials fails-closed."""
    sim = AgentPilotSimulation()
    sim.register_agent("agent_jules_01", "cap_file_indexing")
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "chatgpt_coordinator",
        "receiver_identity": "jules_executor",
        "task_objective": "Read schema",
        "authorized_capability": "cap_file_indexing",
    }
    sim.activate_sandbox("chatgpt_coordinator", "jules_executor", envelope)

    task_payload = {"expired_token": True}
    with pytest.raises(PermissionError, match="Expired permission token"):
        sim.execute_sandbox_task("sage/experimental/pilot_run.json", task_payload)


def test_agent_pilot_failure_boundary_violation():
    """Verify that any write outside of sage/experimental/ is blocked instantly."""
    sim = AgentPilotSimulation()
    sim.register_agent("agent_jules_01", "cap_file_indexing")
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "chatgpt_coordinator",
        "receiver_identity": "jules_executor",
        "task_objective": "Read schema",
        "authorized_capability": "cap_file_indexing",
    }
    sim.activate_sandbox("chatgpt_coordinator", "jules_executor", envelope)

    task_payload = {"action": "exploit"}
    with pytest.raises(PermissionError, match="Boundary violation"):
        sim.execute_sandbox_task("sage/core/spek.py", task_payload)


def test_agent_pilot_failure_human_rejection():
    """Verify that human review gate rejection moves state to REVOKED/REJECTED."""
    sim = AgentPilotSimulation()
    sim.register_agent("agent_jules_01", "cap_file_indexing")
    envelope = {
        "mission_id": "mission_pilot_01",
        "sender_identity": "chatgpt_coordinator",
        "receiver_identity": "jules_executor",
        "task_objective": "Read schema",
        "authorized_capability": "cap_file_indexing",
    }
    sim.activate_sandbox("chatgpt_coordinator", "jules_executor", envelope)
    sim.execute_sandbox_task("sage/experimental/pilot_run.json", {})

    with pytest.raises(ValueError, match="Capability rejected by human supervisor"):
        sim.approve_capability("human_supervisor_01", "REJECTED", "SAGE-RFC-REJECT")


def test_agent_pilot_one_way_import_isolation():
    """Confirm zero experimental code imports inside any production files."""
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "sage.experimental" not in content, f"One-way import violation in {path}"
