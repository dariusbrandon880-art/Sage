"""Agent Execution Contract for SAGE Agent Workflow Layer v1."""

from typing import Any, Dict, List, Optional
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
        """Initialize contract enforcer."""
        self.enforcer = boundary_enforcer or BoundaryEnforcer()

    def validate_action(
        self,
        agent: AgentIdentity,
        boundary: PermissionBoundary,
        action_name: str,
        target_path: Optional[str | Path] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        """Enforce bounds on agent actions, path mutations, and security rules.

        Args:
            agent: Executing agent's identity.
            boundary: The permission boundary defined for the agent.
            action_name: Action identifier string.
            target_path: Optional file/context path being affected.
            auth_token: Optional token for boundary enforcers.

        Raises:
            PermissionError: If action, target path, or parameters violate contract boundaries.
        """
        # 1. Prohibited Actions check
        if action_name in boundary.prohibited_actions:
            raise PermissionError(
                f"Agent Contract Violation: Action '{action_name}' is strictly prohibited "
                f"for agent: {agent.name} (ID: {agent.agent_id})."
            )

        # 2. Allowed Paths check
        if target_path:
            target_resolved = Path(target_path).resolve()

            # Ensure the agent isn't mutating a prohibited path
            for prohibited in boundary.prohibited_paths:
                p_abs = Path(prohibited).resolve()
                try:
                    if target_resolved == p_abs or p_abs in target_resolved.parents:
                        raise PermissionError(
                            f"Agent Contract Violation: Agent {agent.name} is prohibited "
                            f"from accessing path: {target_path}."
                        )
                except ValueError:
                    pass

            # If allowed paths list is populated, target must be under at least one allowed path
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
                    raise PermissionError(
                        f"Agent Contract Violation: Target path '{target_path}' is outside "
                        f"the allowed boundary paths for agent: {agent.name}."
                    )

            # 3. Coordinate with critical SPEK BoundaryEnforcer
            if self.enforcer.is_protected(target_path):
                # Critical SAGE governance files (like CONSTITUTION.md) require SYSTEM_TOKEN authority
                # and cannot be modified by CONTRIBUTOR level agents directly
                self.enforcer.validate_mutation(target_path, auth_token)

    def validate_task_inputs(self, task: AgentTask, inputs: Dict[str, Any]) -> None:
        """Verify that required inputs and metadata are present for governed task execution.

        Args:
            task: Task model.
            inputs: Dictionary of input arguments.

        Raises:
            ValueError: If inputs lack substance, required parameters, or structural validities.
        """
        if not inputs:
            raise ValueError(f"Agent Contract Violation: Task {task.task_id} requires non-empty inputs.")

        # Ensure that mandatory context keys are present
        if "session_id" not in inputs and "objective_id" not in inputs:
            raise ValueError(
                f"Agent Contract Violation: Missing context credentials. SAGE tasks must specify "
                f"either 'session_id' or 'objective_id' for operational continuity tracking."
            )

        immersion = inputs.get("immersion_state")
        if immersion is not None and isinstance(immersion, ImmersionState):
            if not immersion.validate():
                raise ValueError("Agent Contract Violation: Invalid canonical ImmersionState provided in task inputs.")
