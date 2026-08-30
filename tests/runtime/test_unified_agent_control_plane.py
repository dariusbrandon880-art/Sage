import pytest

from sage.agents.contract import AgentExecutionContract
from sage.agents.models import AgentIdentity, AgentTask, PermissionBoundary
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


def task():
    return AgentTask(task_id="task-1", objective_id="objective-1", title="governed task", assigned_agent_id="agent-1")


def verified_state(**overrides):
    values = {
        "station_identity": "[SAGE::C2::JULES]",
        "mission": "control-plane",
        "phase": ExecutionPhase.EXECUTE,
        "flight_id": "F3",
        "flight_status": FlightStatus.ACTIVE,
        "trust_status": TrustStatus.VERIFIED,
        "frontier": "unified-control-plane",
        "gate": "GOVERNED_EXECUTION",
        "next_move": "VERIFY",
        "provenance_head": "abc123",
    }
    values.update(overrides)
    return ImmersionState(**values)


def test_invalid_immersion_state_is_rejected_before_agent_execution():
    contract = AgentExecutionContract()
    with pytest.raises(ValueError, match="canonical ImmersionState"):
        contract.validate_task_inputs(task(), {"objective_id": "objective-1", "immersion_state": "forged"})


def test_unverified_immersion_state_is_rejected():
    contract = AgentExecutionContract()
    with pytest.raises(ValueError, match="VERIFIED"):
        contract.validate_task_inputs(task(), {"objective_id": "objective-1", "immersion_state": verified_state(trust_status=TrustStatus.HOLD)})


def test_missing_provenance_is_rejected():
    contract = AgentExecutionContract()
    with pytest.raises(ValueError, match="provenance_head"):
        contract.validate_task_inputs(task(), {"objective_id": "objective-1", "immersion_state": verified_state(provenance_head="")})


def test_task_agent_identity_cannot_be_cross_bound():
    contract = AgentExecutionContract()
    with pytest.raises(ValueError, match="task agent identity mismatch"):
        contract.validate_task_inputs(task(), {"objective_id": "objective-1", "agent_id": "attacker", "immersion_state": verified_state()})


def test_permission_boundary_cannot_be_cross_bound_to_agent():
    contract = AgentExecutionContract()
    agent = AgentIdentity(agent_id="agent-1", name="Jules")
    boundary = PermissionBoundary(agent_id="agent-2")
    with pytest.raises(PermissionError, match="permission boundary identity mismatch"):
        contract.validate_action(agent, boundary, "read")


def test_valid_canonical_context_passes():
    contract = AgentExecutionContract()
    contract.validate_task_inputs(task(), {"objective_id": "objective-1", "agent_id": "agent-1", "immersion_state": verified_state()})
