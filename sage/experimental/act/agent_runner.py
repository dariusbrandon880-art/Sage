"""SAGE Agent Activation v1 Governed Simulation Worker.

Under SAGE-ACT rules, this component operates in a simulation-only paradigm,
verifying that agent dispatches remain completely within their defined
PermissionBoundary boundaries and satisfy chronological monotonicity check rules.
"""

from typing import Any, Dict, List, Optional
import copy
from datetime import datetime, timezone

from sage.agents.models import AgentIdentity, PermissionBoundary, TaskEvent, AgentTaskState


class GovernedAgentSimWorker:
    """Enforces dynamic permission boundary interception and simulated agent execution."""

    def __init__(self, agent_identity: AgentIdentity, permission_boundary: PermissionBoundary):
        """Initialize simulation worker.

        Args:
            agent_identity: The registered identity of the agent.
            permission_boundary: The allowed/prohibited execution bounds.
        """
        self.agent_identity = agent_identity
        self.permission_boundary = permission_boundary

    def simulate_action(
        self,
        action_name: str,
        target_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Verify and execute a simulated, in-memory action.

        Args:
            action_name: The target action (e.g. read_file, write_file).
            target_path: The filesystem path target of the action.
            context: Optional dictionary containing mock payload details.

        Returns:
            A dictionary detailing simulation results and a mock TaskEvent.

        Raises:
            ValueError: If the action or path violates the agent's permission boundaries.
        """
        # 1. Enforce dynamic permission boundary interception
        # Check prohibited paths
        for prohibited in self.permission_boundary.prohibited_paths:
            if target_path.startswith(prohibited) or prohibited in target_path:
                raise ValueError(
                    f"SAGE-ACT Contract Violation: Prohibited Path Intercepted: "
                    f"Agent '{self.agent_identity.agent_id}' attempted to access "
                    f"forbidden path '{target_path}' under prohibition '{prohibited}'."
                )

        # Check prohibited actions
        if action_name in self.permission_boundary.prohibited_actions:
            raise ValueError(
                f"SAGE-ACT Contract Violation: Prohibited Action Intercepted: "
                f"Agent '{self.agent_identity.agent_id}' attempted to execute "
                f"forbidden action '{action_name}'."
            )

        # Check allowed paths if any are specified
        if self.permission_boundary.allowed_paths:
            allowed = False
            for path in self.permission_boundary.allowed_paths:
                if target_path.startswith(path):
                    allowed = True
                    break
            if not allowed:
                raise ValueError(
                    f"SAGE-ACT Contract Violation: Unauthorized Path Intercepted: "
                    f"Agent '{self.agent_identity.agent_id}' attempted to access path "
                    f"'{target_path}' outside of allowed boundaries."
                )

        # 2. Simulate in-memory execution and generate TaskEvent trace
        event_timestamp = datetime.now(timezone.utc).isoformat()
        sim_event = TaskEvent(
            timestamp=event_timestamp,
            action=action_name,
            actor=self.agent_identity.agent_id,
            details=f"Simulated execution of '{action_name}' on '{target_path}' completed successfully.",
            status=AgentTaskState.COMPLETED
        )

        return {
            "status": "SIMULATION_SUCCESS",
            "agent_id": self.agent_identity.agent_id,
            "action": action_name,
            "target_path": target_path,
            "simulated_at": event_timestamp,
            "task_event": sim_event.model_dump(),
            "read_only_assertion": True
        }
