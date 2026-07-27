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
