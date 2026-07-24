"""Adversarial and Lifecycle Test Suite for SAGE Agent Workflow Layer v1."""

import pytest
from pathlib import Path

from sage.agents import (
    AgentRole,
    MemoryAccess,
    ValidationAuthority,
    AgentTaskState,
    AgentIdentity,
    PermissionBoundary,
    AgentTask,
    AgentExecutionContract,
    AgentMemoryInterface,
    AgentTaskRouter,
    AgentValidationReporting,
)
from sage.core import BoundaryEnforcer, CryptographicAttestationProvider


def test_agent_registration_and_task_lifecycle():
    """Test standard registration, task creation, routing, execution, and completion flow."""
    # 1. Setup router & registered agent
    router = AgentTaskRouter()

    agent = AgentIdentity(
        agent_id="agent_007",
        name="Jules-Agent",
        role=AgentRole.ENFORCER,
        memory_access=MemoryAccess.READ_WRITE,
        validation_authority=ValidationAuthority.HIGH,
    )
    boundary = PermissionBoundary(
        agent_id="agent_007",
        allowed_paths=["sage/", "tests/"],
        prohibited_paths=["/etc"],
        prohibited_actions=["delete_database"],
    )
    router.register_agent(agent, boundary)

    # Confirm registration
    assert "agent_007" in router.agents
    assert router.agents["agent_007"].name == "Jules-Agent"

    # 2. Initialize a task
    task = router.create_task(objective_id="obj_2026", title="Implement agent routing layer")
    assert task.state == AgentTaskState.PENDING
    assert len(task.history) == 1
    assert task.history[0].action == "initialize_task"

    # 3. Route task
    router.route_task(task.task_id, "agent_007")
    assert task.state == AgentTaskState.ROUTED
    assert task.assigned_agent_id == "agent_007"

    # 4. Start execution
    router.start_execution(task.task_id)
    assert task.state == AgentTaskState.EXECUTING

    # 5. Complete task with validation receipt hashes
    router.complete_task(task.task_id, ["eas_receipt_hash_123"])
    assert task.state == AgentTaskState.COMPLETED
    assert "eas_receipt_hash_123" in task.validation_records
    assert task.completed_at is not None
    assert task.history[-1].action == "complete_task"


def test_permission_boundary_enforcement():
    """Test that agent actions violating permission boundaries are strictly blocked."""
    contract = AgentExecutionContract()

    agent = AgentIdentity(
        agent_id="agent_bob",
        name="Developer Bob",
        role=AgentRole.CONTRIBUTOR,
    )
    boundary = PermissionBoundary(
        agent_id="agent_bob",
        allowed_paths=["sage/"],
        prohibited_paths=["sage/core"],
        prohibited_actions=["delete_constitution"],
    )

    # Attempt a prohibited action
    with pytest.raises(PermissionError, match="Action 'delete_constitution' is strictly prohibited"):
        contract.validate_action(agent, boundary, action_name="delete_constitution")

    # Attempt to write to a prohibited path
    with pytest.raises(PermissionError, match="prohibited from accessing path"):
        contract.validate_action(agent, boundary, action_name="write_file", target_path="sage/core/spek.py")

    # Attempt to access a path outside allowed paths
    with pytest.raises(PermissionError, match="outside the allowed boundary paths"):
        contract.validate_action(agent, boundary, action_name="write_file", target_path="tests/test_agents.py")

    # Valid path should pass
    contract.validate_action(agent, boundary, action_name="write_file", target_path="sage/agents/models.py")


def test_critical_spek_boundary_integration():
    """Test that mutating critical SAGE governance paths is governed by the SPEK BoundaryEnforcer."""
    boundary_enforcer = BoundaryEnforcer()
    contract = AgentExecutionContract(boundary_enforcer=boundary_enforcer)

    agent = AgentIdentity(
        agent_id="agent_alice",
        name="Security Auditor Alice",
        role=AgentRole.OBSERVER,
    )
    boundary = PermissionBoundary(
        agent_id="agent_alice",
        allowed_paths=["."],
    )

    # Attempting to touch critical constitution file without system token fails
    with pytest.raises(PermissionError, match="Security Boundary Enforcement Violation"):
        contract.validate_action(
            agent,
            boundary,
            action_name="write_file",
            target_path="docs/master/CONSTITUTION.md",
            auth_token="invalid_token",
        )

    # Touch succeeds with correct SYSTEM_TOKEN
    contract.validate_action(
        agent,
        boundary,
        action_name="write_file",
        target_path="docs/master/CONSTITUTION.md",
        auth_token=BoundaryEnforcer.SYSTEM_TOKEN,
    )


def test_agent_memory_interface():
    """Test that episodic logging and archive searches integrate with SAGE memory layers."""
    # Mock memory and archive stores
    memory_store = []
    archive_store = []

    class MockMemoryStore:
        def store(self, obj):
            memory_store.append(obj)
            return f"ref_{len(memory_store)}"

    class MockArchiveStore:
        def search_by_title(self, query):
            return [x for x in archive_store if query.lower() in x.title.lower()]

    class MockArchiveEntry:
        def __init__(self, title):
            self.title = title
        def model_dump(self):
            return {"title": self.title, "knowledge_state": "ARCHIVED"}

    mem_interface = AgentMemoryInterface(MockMemoryStore(), MockArchiveStore())

    agent = AgentIdentity(agent_id="agent_jules", name="Jules", role=AgentRole.ENFORCER)
    task = AgentTask(task_id="task_x", objective_id="obj_x", title="Deploy kernel")

    # 1. Record episodic event
    ref_id = mem_interface.record_episodic_event(agent, task, "Kernel verification complete")
    assert ref_id == "ref_1"
    assert len(memory_store) == 1
    stored_obj = memory_store[0]
    assert stored_obj.object_type == "agent_episodic_event"
    assert "agent_workflow" in stored_obj.tags
    assert stored_obj.content["description"] == "Kernel verification complete"

    # 2. Retrieve archive entry
    archive_store.append(MockArchiveEntry("SPEK v1.1 Production Specification"))
    archive_store.append(MockArchiveEntry("SAGE Constitutional Core Laws"))

    results = mem_interface.retrieve_archive_wisdom("SPEK")
    assert len(results) == 1
    assert "SPEK v1.1" in results[0]["title"]


def test_agent_validation_reporting():
    """Test compiling and cryptographically signing the final task execution validation report."""
    attestation = CryptographicAttestationProvider()
    reporter = AgentValidationReporting(attestation_provider=attestation)

    agent = AgentIdentity(
        agent_id="agent_validate",
        name="Validator Agent",
        role=AgentRole.VALIDATOR,
    )
    task = AgentTask(task_id="task_v", objective_id="obj_v", title="E2E Validation Audit")

    report = reporter.generate_validation_report(
        agent=agent,
        task=task,
        actions_performed=["Run unit tests", "Audit ledger hash chain"],
        files_changed=["sage/core/compliance.py"],
        tests_completed=["test_valid_proposal_approval", "test_audit_tampering_detection"],
        validation_status="PASSED_VERIFIED",
        architecture_impact="Verified compliance ledger and SPEK lifecycle integrity.",
        remaining_risks=[],
    )

    # 1. Structural check
    assert "report_payload" in report
    assert "attestation_signature" in report
    assert report["provider_type"] == attestation.get_provider_type()

    payload = report["report_payload"]
    assert payload["task_id"] == "task_v"
    assert payload["validation_status"] == "PASSED_VERIFIED"
    assert "Run unit tests" in payload["actions_performed"]

    # 2. Cryptographic check
    assert attestation.verify(payload, report["attestation_signature"]) is True
