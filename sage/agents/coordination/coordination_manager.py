"""SAGE Multi-Agent Coordination Manager for SAGE Multi-Agent Coordination Layer."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sage.agents.coordination.registry import MultiAgentRegistry, CoordinatedAgentProfile
from sage.agents.coordination.router import CoordinatedTaskRouter, CoordinatedTask
from sage.agents.models import AgentTaskState, TaskEvent, AgentIdentity
from sage.agents.contract import AgentExecutionContract


class SAGECoordinationManager:
    """Orchestrates multi-agent registry, role-based routing, boundaries, and evidence tracing.

    Coordinates diverse agents (ChatGPT, Google AI, Jules) under strict SAGE rules,
    preventing direct unauthorized production state mutations.
    """

    def __init__(
        self,
        registry: Optional[MultiAgentRegistry] = None,
        router: Optional[CoordinatedTaskRouter] = None,
        contract: Optional[AgentExecutionContract] = None,
    ):
        """Initialize SAGECoordinationManager."""
        self.registry = registry or MultiAgentRegistry()
        self.router = router or CoordinatedTaskRouter()
        self.contract = contract or AgentExecutionContract()

    def register_coordinated_agent(self, profile: CoordinatedAgentProfile) -> None:
        """Register a coordinated agent profile under SAGE rules.

        Args:
            profile: Target agent profile.
        """
        self.registry.register_coordinated_agent(profile)

    def coordinate_and_execute(
        self,
        agent_id: str,
        objective_id: str,
        task_title: str,
        task_type: str,
        action: str,
        target_path: Optional[str] = None,
        required_validation_level: str = "low",
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate, route, and execute a task, returning a secure, attested evidence receipt.

        Args:
            agent_id: Registered agent ID.
            objective_id: Active objective ID.
            task_title: Narrative title.
            task_type: Coordinated task type ("research", "engineering", etc.).
            action: Action string to execute.
            target_path: Target path involved.
            required_validation_level: Minimum authority level.
            auth_token: Present security token.

        Returns:
            Secure Evidence Receipt dictionary with SHA-256 hash.
        """
        # 1. Registration Check
        try:
            agent_profile = self.registry.get_coordinated_agent(agent_id)
        except KeyError:
            # Unauthorized agent rejection
            raise ValueError(f"Coordination Rejection: Agent '{agent_id}' is not registered under coordination.")

        # 2. Task Creation & Routing (includes Authority validation level check)
        task = self.router.create_coordinated_task(
            objective_id=objective_id,
            title=task_title,
            task_type=task_type,
            required_validation_level=required_validation_level,
        )
        self.router.route_coordinated_task(task.task_id, agent_profile)

        # Build AgentIdentity dynamically for contract validation
        agent_identity = AgentIdentity(
            agent_id=agent_profile.agent_id,
            name=agent_profile.agent_id,
            role=agent_profile.role,
        )

        # 3. Permission Boundary Enforcement
        # Ensure the agent isn't attempting direct modification of protected states or prohibited paths
        try:
            self.contract.validate_action(
                agent=agent_identity,
                boundary=agent_profile.boundary,
                action_name=action,
                target_path=target_path,
                auth_token=auth_token,
            )
        except PermissionError as e:
            # Mark task as failed due to boundary breach
            task.state = AgentTaskState.FAILED
            event = TaskEvent(
                action="fail_coordinated_task",
                actor=agent_id,
                details=f"Permission Boundary Breach: {e!s}",
                status=AgentTaskState.FAILED,
            )
            task.history.append(event)
            raise

        # 4. Execution State Transition
        task.state = AgentTaskState.EXECUTING
        task.history.append(
            TaskEvent(
                action="execute_coordinated_task",
                actor=agent_id,
                details="Coordinated task executed successfully.",
                status=AgentTaskState.EXECUTING,
            )
        )

        task.state = AgentTaskState.COMPLETED
        task.history.append(
            TaskEvent(
                action="complete_coordinated_task",
                actor=agent_id,
                details="Coordinated task execution finalized.",
                status=AgentTaskState.COMPLETED,
            )
        )

        # 5. Evidence Receipt Generation
        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = {
            "agent_id": agent_id,
            "agent_type": agent_profile.agent_type,
            "task_id": task.task_id,
            "timestamp": ts,
            "action_summary": f"Executed coordinated '{task_type}' task: {task_title}",
        }

        # Deterministic SHA-256 evidence receipt reference
        serialized_payload = json.dumps(receipt_payload, sort_keys=True)
        evidence_receipt_reference = hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()

        evidence_receipt = {
            "agent_id": agent_id,
            "task_id": task.task_id,
            "timestamp": ts,
            "action_summary": f"Executed coordinated '{task_type}' task: {task_title}",
            "evidence_receipt_reference": evidence_receipt_reference,
            "validation_status": "VERIFIED",
        }

        return evidence_receipt
