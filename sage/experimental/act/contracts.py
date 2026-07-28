"""SAGE Agent Continuity Tree Read-Only Interface Contracts."""

from typing import Any, Dict, List
from datetime import datetime, timezone


class SessionTaskTreeLinker:
    """Enforces read-only schema mapping and validation for Session-to-Task lineage.

    Under Milestone 1 rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying structures and generating mapping lineage models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize linker contract."""
        self.validation_mode = validation_mode

    def link_session_to_tasks(self, session_id: str, task_ids: List[str]) -> Dict[str, Any]:
        """Perform schema validation and return a read-only mapped session-to-task tree.

        Args:
            session_id: The target session identifier.
            task_ids: A list of task identifiers to map.

        Returns:
            A dictionary representing the verified mapped lineage tree.

        Raises:
            ValueError: If session_id or task_ids fail structural format checks.
        """
        if not session_id or not session_id.startswith("session_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid session_id format: '{session_id}'")

        for task_id in task_ids:
            if not task_id or not task_id.startswith("task_"):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

        # Map and return the structured lineage without writing or mutating system files
        return {
            "session_id": session_id,
            "mapped_tasks": list(task_ids),
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }


class SessionStateTaskLinker:
    """Enforces deep read-only lineage validation mapping SessionState to AgentTasks.

    Under Milestone 2A rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying relationships and generating mapped lineage models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize session state task linker."""
        self.validation_mode = validation_mode

    def validate_session_task_lineage(
        self,
        session: Any,  # Expected: SessionState (or dictionary)
        tasks: List[Any],  # Expected: List[AgentTask] (or dictionaries)
    ) -> Dict[str, Any]:
        """Validates that all tasks belong logically to the given session.

        Raises:
            ValueError: On objective mismatch, invalid identifier format, duplicate task ID,
                        or other lineage violations.
        """
        # 1. Extract and validate session_id
        if hasattr(session, "session_id"):
            session_id = session.session_id
        elif isinstance(session, dict) and "session_id" in session:
            session_id = session["session_id"]
        else:
            raise ValueError("SAGE-ACT Contract Violation: Missing 'session_id' in session state.")

        if not isinstance(session_id, str) or not session_id.startswith("session_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid session_id format: '{session_id}'")

        # 2. Extract active_objectives
        if hasattr(session, "active_objectives"):
            active_objectives = session.active_objectives
        elif isinstance(session, dict) and "active_objectives" in session:
            active_objectives = session["active_objectives"]
        else:
            active_objectives = []

        # 3. Process and validate tasks
        seen_task_ids = set()
        mapped_tasks = []

        for task in tasks:
            # Extract task_id
            if hasattr(task, "task_id"):
                task_id = task.task_id
            elif isinstance(task, dict) and "task_id" in task:
                task_id = task["task_id"]
            else:
                raise ValueError("SAGE-ACT Contract Violation: Missing 'task_id' in task.")

            # Extract objective_id
            if hasattr(task, "objective_id"):
                objective_id = task.objective_id
            elif isinstance(task, dict) and "objective_id" in task:
                objective_id = task["objective_id"]
            else:
                raise ValueError("SAGE-ACT Contract Violation: Missing 'objective_id' in task.")

            # Validate task_id format
            if not isinstance(task_id, str) or not task_id.startswith("task_"):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

            # Duplicate task detection
            if task_id in seen_task_ids:
                raise ValueError(f"SAGE-ACT Contract Violation: Duplicate task ID detected: '{task_id}'")
            seen_task_ids.add(task_id)

            # Objective mismatch detection
            if objective_id not in active_objectives:
                raise ValueError(
                    f"SAGE-ACT Contract Violation: Objective mismatch. Task '{task_id}' maps to objective '{objective_id}', "
                    f"which is not present in session active objectives: {active_objectives}"
                )

            mapped_tasks.append(task_id)

        # Return structured lineage metadata
        return {
            "session_id": session_id,
            "mapped_tasks": mapped_tasks,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "LINEAGE_VALIDATED",
            "read_only_assertion": True,
        }


class TaskDecisionBinder:
    """Enforces read-only schema mapping and validation for Task-to-Decision lineage.

    Under Milestone 1 rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying structures and generating mapping decision models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize binder contract."""
        self.validation_mode = validation_mode

    def bind_task_to_decisions(self, task_id: str, decision_ids: List[str]) -> Dict[str, Any]:
        """Perform schema validation and return a read-only mapped task-to-decision lineage.

        Args:
            task_id: The target task identifier.
            decision_ids: A list of decision identifiers to bind.

        Returns:
            A dictionary representing the verified mapped decision lineage.

        Raises:
            ValueError: If task_id or decision_ids fail structural format checks.
        """
        if not task_id or not task_id.startswith("task_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

        for dec_id in decision_ids:
            if not dec_id or not (dec_id.startswith("decision_") or dec_id.startswith("proposal_")):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid decision/proposal ID format: '{dec_id}'")

        # Bind and return the structured lineage without writing or mutating system files
        return {
            "task_id": task_id,
            "bound_decisions": list(decision_ids),
            "bound_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }
