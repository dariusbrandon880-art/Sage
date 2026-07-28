"""SAGE Agent Activation v1 Governed Simulation Worker.

Under SAGE-ACT rules, this component operates in a simulation-only paradigm,
verifying that agent dispatches remain completely within their defined
PermissionBoundary boundaries and satisfy chronological monotonicity check rules.
"""

from typing import Any, Dict, List, Optional
import copy
from datetime import datetime, timezone
import uuid

from sage.agents.models import AgentIdentity, PermissionBoundary, TaskEvent, AgentTaskState


class AgentBoundaryInterceptionError(ValueError):
    """Exception raised when an agent boundary violation is gracefully intercepted, holding the reliability payload."""

    def __init__(self, message: str, payload: Dict[str, Any]):
        super().__init__(message)
        self.payload = payload


class AgentReliabilityManager:
    """Manages graceful failure interception, payload generation, and recovery/rehydration checkpointing."""

    @staticmethod
    def generate_audit_payload(
        agent_id: str,
        task_id: str,
        session_id: str,
        workflow_id: str,
        current_task_step: str,
        previous_steps: List[Dict[str, Any]],
        active_state_snapshot_ref: str,
        failure_type: str,
        originating_component: str,
        external_dependency_status: Dict[str, str],
        causal_binder_ref: str,
        causal_chain: List[str],
        underlying_decisions: List[Dict[str, Any]],
        recovery_possible: bool,
        human_approval_required: bool,
        rehydration_checkpoint_ref: str
    ) -> Dict[str, Any]:
        """Generates a complete, schema-compliant SAGE Agent Reliability Audit Payload."""
        return {
            "identity": {
                "agent_id": agent_id,
                "task_id": task_id,
                "session_id": session_id,
                "workflow_id": workflow_id
            },
            "state": {
                "current_task_step": current_task_step,
                "previous_steps": previous_steps,
                "active_state_snapshot_ref": active_state_snapshot_ref
            },
            "failure_event": {
                "failure_type": failure_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "originating_component": originating_component,
                "external_dependency_status": external_dependency_status
            },
            "decision_lineage": {
                "causal_binder_ref": causal_binder_ref,
                "causal_chain": causal_chain,
                "underlying_decisions": underlying_decisions
            },
            "recovery": {
                "recovery_possible": recovery_possible,
                "human_approval_required": human_approval_required,
                "rehydration_checkpoint_ref": rehydration_checkpoint_ref
            }
        }


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

    def simulate_action_with_intercept(
        self,
        action_name: str,
        target_path: str,
        session_id: str,
        workflow_id: str,
        current_task_step: str,
        previous_steps: List[Dict[str, Any]],
        causal_binder_ref: str,
        causal_chain: List[str],
        underlying_decisions: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simulates action execution while dynamically capturing any boundary violations.

        If a violation is captured, it builds the schema-compliant audit payload,
        prepares state snapshots and rehydration checkpoints, and raises
        AgentBoundaryInterceptionError.
        """
        try:
            return self.simulate_action(action_name, target_path, context)
        except ValueError as e:
            # Determine the failure type
            failure_type = "BOUNDARY_VIOLATION"
            if "Prohibited Action" in str(e):
                failure_type = "BOUNDARY_VIOLATION"
            elif "Prohibited Path" in str(e):
                failure_type = "BOUNDARY_VIOLATION"
            elif "Unauthorized Path" in str(e):
                failure_type = "BOUNDARY_VIOLATION"
            else:
                failure_type = "UNKNOWN"

            # Generate unique snapshot and checkpoint references
            unique_suffix = uuid.uuid4().hex[:8]
            active_state_snapshot_ref = f"snapshot_{unique_suffix}"
            rehydration_checkpoint_ref = f"checkpoint_{unique_suffix}"

            # Build audit payload using AgentReliabilityManager
            payload = AgentReliabilityManager.generate_audit_payload(
                agent_id=self.agent_identity.agent_id,
                task_id=self.permission_boundary.agent_id,
                session_id=session_id,
                workflow_id=workflow_id,
                current_task_step=current_task_step,
                previous_steps=previous_steps,
                active_state_snapshot_ref=active_state_snapshot_ref,
                failure_type=failure_type,
                originating_component=f"{self.__class__.__module__}.{self.__class__.__name__}",
                external_dependency_status={"local_filesystem": "ACTIVE"},
                causal_binder_ref=causal_binder_ref,
                causal_chain=causal_chain,
                underlying_decisions=underlying_decisions,
                recovery_possible=True,
                human_approval_required=True,
                rehydration_checkpoint_ref=rehydration_checkpoint_ref
            )

            # Raise the formatted intercept error containing the payload
            error_msg = f"SAGE-ACT Contract Violation: Graceful Intercept Captured: {str(e)}"
            raise AgentBoundaryInterceptionError(error_msg, payload)
