"""Agent Task Router for SAGE Agent Workflow Layer v1."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from sage.agents.models import (
    AgentIdentity,
    PermissionBoundary,
    AgentTask,
    AgentTaskState,
    TaskEvent,
    AgentRole,
)
from sage.agents.contract import AgentExecutionContract


class AgentTaskRouter:
    """Orchestrates governed task routing, agent role matching, and execution state tracking.

    Translates top-level objectives into tasks, validates boundaries, and manages
    the operational lifecycle of SAGE agents.
    """

    def __init__(self, contract: Optional[AgentExecutionContract] = None):
        """Initialize AgentTaskRouter."""
        self.contract = contract or AgentExecutionContract()
        self.agents: Dict[str, AgentIdentity] = {}
        self.boundaries: Dict[str, PermissionBoundary] = {}
        self.tasks: Dict[str, AgentTask] = {}

    def register_agent(self, agent: AgentIdentity, boundary: PermissionBoundary) -> None:
        """Register a new governed agent and its permission boundary.

        Args:
            agent: Agent identity profile.
            boundary: Permission boundary ruleset.
        """
        if agent.agent_id != boundary.agent_id:
            raise ValueError("Identity ID and Boundary ID must match for registration.")
        self.agents[agent.agent_id] = agent
        self.boundaries[agent.agent_id] = boundary

    def create_task(self, objective_id: str, title: str, metadata: Optional[Dict[str, Any]] = None) -> AgentTask:
        """Create a new unassigned task under an active SAGE objective.

        Args:
            objective_id: Target objective ID.
            title: Title/narrative of the task.
            metadata: Associated parameters.

        Returns:
            The initialized AgentTask.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = AgentTask(
            task_id=task_id,
            objective_id=objective_id,
            title=title,
            state=AgentTaskState.PENDING,
            metadata=metadata or {},
        )

        event = TaskEvent(
            action="initialize_task",
            actor="AgentTaskRouter",
            details="Task initialized under SAGE objective.",
            status=AgentTaskState.PENDING,
        )
        task.history.append(event)
        self.tasks[task_id] = task
        return task

    def route_task(self, task_id: str, agent_id: str) -> AgentTask:
        """Evaluate agent role permissions and assign a task to a registered agent.

        Args:
            task_id: Target task ID.
            agent_id: Target agent ID.

        Returns:
            The updated AgentTask.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")
        if agent_id not in self.agents:
            raise KeyError(f"Agent not registered: {agent_id}")

        task = self.tasks[task_id]
        agent = self.agents[agent_id]
        boundary = self.boundaries[agent_id]

        # Verify that task title or objective doesn't violate allowed/prohibited actions
        self.contract.validate_action(agent, boundary, "execute_task")

        task.assigned_agent_id = agent_id
        task.state = AgentTaskState.ROUTED

        event = TaskEvent(
            action="route_task",
            actor="AgentTaskRouter",
            details=f"Task routed and assigned to agent: {agent.name} (Role: {agent.role.value}).",
            status=AgentTaskState.ROUTED,
        )
        task.history.append(event)
        return task

    def start_execution(self, task_id: str) -> AgentTask:
        """Mark a routed task as actively executing.

        Args:
            task_id: Target task ID.

        Returns:
            The updated AgentTask.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")

        task = self.tasks[task_id]
        if task.state != AgentTaskState.ROUTED:
            raise ValueError(f"Cannot start execution on task in state: {task.state}")

        task.state = AgentTaskState.EXECUTING
        event = TaskEvent(
            action="start_execution",
            actor=task.assigned_agent_id or "unknown_agent",
            details="Agent execution begun.",
            status=AgentTaskState.EXECUTING,
        )
        task.history.append(event)
        return task

    def complete_task(self, task_id: str, validation_receipt_hashes: List[str]) -> AgentTask:
        """Mark an executing task as completed and attach validated validation receipts.

        Args:
            task_id: Target task ID.
            validation_receipt_hashes: List of generated SPEK/EAS receipts.

        Returns:
            The updated AgentTask.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")

        task = self.tasks[task_id]
        if task.state != AgentTaskState.EXECUTING:
            raise ValueError(f"Cannot complete task from state: {task.state}")

        task.state = AgentTaskState.COMPLETED
        task.validation_records = validation_receipt_hashes
        task.completed_at = datetime.now(timezone.utc).isoformat()

        event = TaskEvent(
            action="complete_task",
            actor=task.assigned_agent_id or "unknown_agent",
            details="Agent execution completed successfully. Validation evidence attached.",
            status=AgentTaskState.COMPLETED,
        )
        task.history.append(event)
        return task

    def fail_task(self, task_id: str, failure_reason: str) -> AgentTask:
        """Mark an executing task as failed, capturing diagnostic reason context.

        Args:
            task_id: Target task ID.
            failure_reason: Diagnostic reason string.

        Returns:
            The updated AgentTask.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")

        task = self.tasks[task_id]
        task.state = AgentTaskState.FAILED
        task.completed_at = datetime.now(timezone.utc).isoformat()

        event = TaskEvent(
            action="fail_task",
            actor=task.assigned_agent_id or "unknown_agent",
            details=f"Task execution failed: {failure_reason}",
            status=AgentTaskState.FAILED,
        )
        task.history.append(event)
        return task
