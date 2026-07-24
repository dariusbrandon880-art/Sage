"""Coordinated Task Router for SAGE Multi-Agent Coordination Layer."""

from typing import Dict, List, Optional
import uuid

from sage.agents.coordination.registry import CoordinatedAgentProfile
from sage.agents.models import AgentTask, AgentTaskState, TaskEvent


class CoordinatedTask(AgentTask):
    """Schema representing a task coordinated under SAGE multi-agent rules."""

    task_type: str  # "research", "engineering", "validation", "documentation"
    required_validation_level: str = "low"  # "low", "medium", "high"


class CoordinatedTaskRouter:
    """Routes coordinated research, engineering, validation, and documentation tasks to agents."""

    def __init__(self):
        """Initialize CoordinatedTaskRouter."""
        self.coordinated_tasks: Dict[str, CoordinatedTask] = {}

    def create_coordinated_task(
        self,
        objective_id: str,
        title: str,
        task_type: str,
        required_validation_level: str = "low",
    ) -> CoordinatedTask:
        """Create a new coordinated task with explicit type and validation gates.

        Args:
            objective_id: Active objective ID.
            title: Title/narrative of the task.
            task_type: Type of task ("research", "engineering", "validation", "documentation").
            required_validation_level: Validation level required to action this task.

        Returns:
            The created CoordinatedTask.
        """
        if task_type not in ("research", "engineering", "validation", "documentation"):
            raise ValueError(f"Coordination Error: Invalid task type '{task_type}'.")

        task_id = f"coord_task_{uuid.uuid4().hex[:12]}"
        task = CoordinatedTask(
            task_id=task_id,
            objective_id=objective_id,
            title=title,
            task_type=task_type,
            required_validation_level=required_validation_level,
            state=AgentTaskState.PENDING,
        )

        event = TaskEvent(
            action="initialize_coordinated_task",
            actor="CoordinatedTaskRouter",
            details=f"Coordinated task of type '{task_type}' created.",
            status=AgentTaskState.PENDING,
        )
        task.history.append(event)
        self.coordinated_tasks[task_id] = task
        return task

    def route_coordinated_task(self, task_id: str, agent_profile: CoordinatedAgentProfile) -> CoordinatedTask:
        """Assign and route a coordinated task to an agent if their validation level matches.

        Args:
            task_id: Target task ID.
            agent_profile: Profile of the agent being assigned.

        Returns:
            The routed CoordinatedTask.
        """
        if task_id not in self.coordinated_tasks:
            raise KeyError(f"Task not found: {task_id}")

        task = self.coordinated_tasks[task_id]

        # Authority Check: Verify agent has equal or higher validation level than required
        level_hierarchy = {"low": 1, "medium": 2, "high": 3}
        agent_level = level_hierarchy.get(agent_profile.validation_level.lower(), 1)
        required_level = level_hierarchy.get(task.required_validation_level.lower(), 1)

        if agent_level < required_level:
            raise PermissionError(
                f"Authority Rejection: Agent {agent_profile.agent_id} has validation level "
                f"'{agent_profile.validation_level}', but task {task_id} requires level "
                f"'{task.required_validation_level}'."
            )

        task.assigned_agent_id = agent_profile.agent_id
        task.state = AgentTaskState.ROUTED

        event = TaskEvent(
            action="route_coordinated_task",
            actor="CoordinatedTaskRouter",
            details=f"Task routed to coordinated agent: {agent_profile.agent_id} (Type: {agent_profile.agent_type}).",
            status=AgentTaskState.ROUTED,
        )
        task.history.append(event)
        return task
