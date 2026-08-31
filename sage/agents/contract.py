"""Agent Execution Contract for SAGE Agent Workflow Layer v1."""

from typing import Any, Dict, Optional
from pathlib import Path

from sage.agents.models import AgentIdentity, PermissionBoundary, AgentTask
from sage.core.boundary import BoundaryEnforcer
from sage.c2.immersion_state import ImmersionState


class AgentExecutionContract:
    """Enforces boundaries, prohibited actions, and validation constraints on SAGE agents.

    Binds agent executions to constitutional limits, ensuring full alignment with
    SAGE's core security boundaries and SPEK enforcer controls.
    """

    def __init__(self, boundary_enforcer: Optional[BoundaryEnforcer] = None):
        self.enforcer = boundary_enforcer or BoundaryEnforcer()

    def validate_action(self, agent: AgentIdentity, boundary: PermissionBoundary, action_name: str, target_path: Optional[str | Path] = None, auth_token: Optional[str] = None) -> None:
        """Enforce bounds on agent actions, paths, and protected mutations."""
        if boundary.agent_id != agent.agent_id:
            raise PermissionError("Agent Contract Violation: permission boundary identity mismatch.")
        if action_name in boundary.prohibited_actions:
            raise PermissionError(f"Agent Contract Violation: Action '{action_name}' is strictly prohibited for agent: {agent.name} (ID: {agent.agent_id}).")
        if target_path:
            target_resolved = Path(target_path).resolve()
            for prohibited in boundary.prohibited_paths:
                p_abs = Path(prohibited).resolve()
                try:
                    if target_resolved == p_abs or p_abs in target_resolved.parents:
                        raise PermissionError(f"Agent Contract Violation: Agent {agent.name} is prohibited from accessing path: {target_path}.")
                except ValueError:
                    pass
            if boundary.allowed_paths:
                allowed_match = False
                for allowed in boundary.allowed_paths:
                    a_abs = Path(allowed).resolve()
                    try:
                        if target_resolved == a_abs or a_abs in target_resolved.parents:
                            allowed_match = True
                            break
                    except ValueError:
                        pass
                if not allowed_match:
                    raise PermissionError(f"Agent Contract Violation: Target path '{target_path}' is outside the allowed boundary paths for agent: {agent.name}.")
            if self.enforcer.is_protected(target_path):
                self.enforcer.validate_mutation(target_path, auth_token)

    def validate_task_inputs(self, task: AgentTask, inputs: Dict[str, Any]) -> None:
        """Fail closed unless task context is structurally and canonically valid."""
        if not inputs:
            raise ValueError(f"Agent Contract Violation: Task {task.task_id} requires non-empty inputs.")
        if "session_id" not in inputs and "objective_id" not in inputs:
            raise ValueError("Agent Contract Violation: Missing context credentials. SAGE tasks must specify either 'session_id' or 'objective_id' for operational continuity tracking.")
        immersion_state = inputs.get("immersion_state")
        if immersion_state is not None:
            if not isinstance(immersion_state, ImmersionState):
                raise ValueError("Agent Contract Violation: immersion_state must be canonical ImmersionState.")
            if not immersion_state.validate():
                raise ValueError("Agent Contract Violation: canonical ImmersionState failed validation.")
            if immersion_state.station_identity.strip() != immersion_state.station_identity:
                raise ValueError("Agent Contract Violation: station identity is not canonical.")
            if not immersion_state.provenance_head.strip():
                raise ValueError("Agent Contract Violation: canonical ImmersionState requires provenance_head.")
            if immersion_state.trust_status.value != "VERIFIED":
                raise ValueError("Agent Contract Violation: agent execution requires VERIFIED immersion state.")
        expected_agent_id = inputs.get("agent_id")
        if expected_agent_id is not None and expected_agent_id != task.assigned_agent_id:
            raise ValueError("Agent Contract Violation: task agent identity mismatch.")
        expected_objective = inputs.get("objective_id")
        if expected_objective is not None and expected_objective != task.objective_id:
            raise ValueError("Agent Contract Violation: task objective identity mismatch.")
