"""SAGE Agent Continuity Tree Read-Only Interface Contracts - Milestone 2."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class SessionTaskTreeLinker:
    """Enforces read-only schema mapping and validation for Session-to-Task lineage.

    In Milestone 2, this linker connects directly to SAGE's existing SessionStateManager
    and AgentTaskRouter, detecting missing lineage links and orphan states without writing.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize linker contract."""
        self.validation_mode = validation_mode

    def link_session_to_tasks(self, session_id: str, task_ids: List[str]) -> Dict[str, Any]:
        """Perform legacy format check and return a simple read-only tree.

        Maintains backwards compatibility with Milestone 1 signatures.
        """
        if not session_id or not session_id.startswith("session_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid session_id format: '{session_id}'")

        for t_id in task_ids:
            if not t_id or not t_id.startswith("task_"):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{t_id}'")

        return {
            "session_id": session_id,
            "mapped_tasks": list(task_ids),
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }

    def validate_session_and_tasks(
        self,
        session_id: str,
        task_ids: List[str],
        session_manager: Optional[Any] = None,
        task_router: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Validate relationships between session and tasks, generating a Continuity Truth Report.

        Performs deep verification of lineage link completeness and orphan states.
        No database or production mutations are executed.
        """
        # Ensure structural formatting matches standard
        self.link_session_to_tasks(session_id, task_ids)

        anomalies = []
        session_obj = None

        # 1. Access existing SessionState data
        if session_manager is not None:
            if hasattr(session_manager, "retrieve_session"):
                session_obj = session_manager.retrieve_session(session_id)
            elif hasattr(session_manager, "get"):
                session_obj = session_manager.get(session_id)

            if not session_obj:
                anomalies.append({
                    "type": "session_not_found",
                    "target": session_id,
                    "details": f"The session {session_id} does not exist in the active SessionState storage.",
                })

        # 2. Access existing AgentTaskRouter/Tasks data
        if task_router is not None:
            router_tasks = getattr(task_router, "tasks", {})

            for t_id in task_ids:
                # Trace individual task existence
                if t_id not in router_tasks:
                    anomalies.append({
                        "type": "task_not_found",
                        "target": t_id,
                        "details": f"The task {t_id} is missing from the active task router registry.",
                    })
                    continue

                task = router_tasks[t_id]

                # Detect Orphan States: Task with no assigned agent
                assigned_agent = getattr(task, "assigned_agent_id", None)
                if not assigned_agent:
                    anomalies.append({
                        "type": "orphan_task_no_agent",
                        "target": t_id,
                        "details": f"The task {t_id} is in state '{getattr(task, 'state', 'unknown')}' but has no assigned agent.",
                    })

                # Check objective alignment
                if session_obj:
                    active_objectives = getattr(session_obj, "active_objectives", [])
                    task_obj_id = getattr(task, "objective_id", None)
                    if task_obj_id and task_obj_id not in active_objectives:
                        anomalies.append({
                            "type": "objective_alignment_mismatch",
                            "target": t_id,
                            "details": f"The task {t_id} objective '{task_obj_id}' is not linked to active session objectives: {active_objectives}.",
                        })

            # Detect Missing Lineage Links: Router tasks claiming to belong to this session but omitted from task_ids
            for r_tid, r_task in router_tasks.items():
                if r_tid not in task_ids:
                    # Check metadata or objective associations indicating link to this session
                    r_meta = getattr(r_task, "metadata", {})
                    r_obj_id = getattr(r_task, "objective_id", None)

                    belongs_to_session = False
                    if r_meta.get("session_id") == session_id:
                        belongs_to_session = True
                    elif session_obj and r_obj_id in getattr(session_obj, "active_objectives", []):
                        belongs_to_session = True

                    if belongs_to_session:
                        anomalies.append({
                            "type": "missing_lineage_link",
                            "target": r_tid,
                            "details": f"Task {r_tid} is associated with session {session_id} but was omitted from the verified task list.",
                        })

        return {
            "session_id": session_id,
            "task_lineage_tree": {
                "session_id": session_id,
                "mapped_tasks": list(task_ids),
                "active_objectives": getattr(session_obj, "active_objectives", []) if session_obj else [],
            },
            "anomalies": anomalies,
            "valid_continuity": len(anomalies) == 0,
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status": "CONTINUITY_TRUTH_REPORT_COMPILED",
            "read_only_assertion": True,
        }


class TaskDecisionBinder:
    """Enforces read-only schema mapping and validation for Task-to-Decision lineage.

    In Milestone 2, this binder connects directly to SAGE's existing DecisionTracker,
    performing temporal causality audits and identifying missing links.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize binder contract."""
        self.validation_mode = validation_mode

    def bind_task_to_decisions(self, task_id: str, decision_ids: List[str]) -> Dict[str, Any]:
        """Perform simple legacy format check and return simple mapping.

        Maintains backwards compatibility with Milestone 1 signatures.
        """
        if not task_id or not task_id.startswith("task_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

        for dec_id in decision_ids:
            if not dec_id or not (dec_id.startswith("decision_") or dec_id.startswith("proposal_")):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid decision/proposal ID format: '{dec_id}'")

        return {
            "task_id": task_id,
            "bound_decisions": list(decision_ids),
            "bound_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }

    def validate_task_and_decisions(
        self,
        task_id: str,
        decision_ids: List[str],
        task_router: Optional[Any] = None,
        decision_tracker: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Validate task-to-decision causal mapping, generating a Decision Continuity Map.

        Performs strict temporal audits and detects detached or missing references.
        No database or production mutations are executed.
        """
        # Formally check structural formats
        self.bind_task_to_decisions(task_id, decision_ids)

        anomalies = []
        task_obj = None

        # 1. Retrieve the Task instance
        if task_router is not None:
            router_tasks = getattr(task_router, "tasks", {})
            if task_id in router_tasks:
                task_obj = router_tasks[task_id]
            else:
                anomalies.append({
                    "type": "task_not_found",
                    "target": task_id,
                    "details": f"The task {task_id} does not exist in the active task router.",
                })

        # 2. Retrieve decisions and execute Temporal Causality Audit
        if decision_tracker is not None:
            for dec_id in decision_ids:
                dec_entry = None
                if hasattr(decision_tracker, "retrieve_decision"):
                    dec_entry = decision_tracker.retrieve_decision(dec_id)
                elif hasattr(decision_tracker, "decisions"):
                    dec_entry = decision_tracker.decisions.get(dec_id)

                if not dec_entry:
                    anomalies.append({
                        "type": "decision_not_found",
                        "target": dec_id,
                        "details": f"The decision {dec_id} is missing from the DecisionTracker storage.",
                    })
                    continue

                # Parse temporal metadata to ensure timeline order (Causality Validation)
                if task_obj:
                    try:
                        # Extract and parse timestamps safely
                        task_created_str = getattr(task_obj, "created_at", None)
                        dec_timestamp_obj = getattr(dec_entry, "timestamp", None)

                        task_created = None
                        if task_created_str:
                            task_created = datetime.fromisoformat(task_created_str)
                            if task_created.tzinfo is None:
                                task_created = task_created.replace(tzinfo=timezone.utc)

                        dec_timestamp = None
                        if isinstance(dec_timestamp_obj, datetime):
                            dec_timestamp = dec_timestamp_obj
                        elif isinstance(dec_timestamp_obj, str):
                            dec_timestamp = datetime.fromisoformat(dec_timestamp_obj)

                        if dec_timestamp and dec_timestamp.tzinfo is None:
                            dec_timestamp = dec_timestamp.replace(tzinfo=timezone.utc)

                        # Audit: Decision timestamp cannot be older than task creation date
                        if task_created and dec_timestamp and dec_timestamp < task_created:
                            anomalies.append({
                                "type": "temporal_causality_violation",
                                "target": dec_id,
                                "details": (
                                    f"The decision {dec_id} timestamp '{dec_timestamp.isoformat()}' "
                                    f"pre-dates task {task_id} creation time '{task_created.isoformat()}'."
                                ),
                            })
                    except Exception as e:
                        # Add a parsing anomaly
                        anomalies.append({
                            "type": "timestamp_parse_error",
                            "target": dec_id,
                            "details": f"Failed to parse time causality metrics for decision {dec_id}: {e}",
                        })

            # Detect unlinked decision references (decisions referencing task in evidence but not in list)
            all_tracker_decisions = []
            if hasattr(decision_tracker, "list_all"):
                all_tracker_decisions = decision_tracker.list_all()
            elif hasattr(decision_tracker, "decisions"):
                all_tracker_decisions = list(decision_tracker.decisions.values())

            for tracker_dec in all_tracker_decisions:
                dec_entry_id = getattr(tracker_dec, "id", None)
                if dec_entry_id and dec_entry_id not in decision_ids:
                    evidence_list = getattr(tracker_dec, "evidence", []) or []
                    if task_id in evidence_list:
                        anomalies.append({
                            "type": "unlinked_decision_reference",
                            "target": dec_entry_id,
                            "details": f"Decision {dec_entry_id} references task {task_id} as evidence but was omitted from the binding list.",
                        })

        return {
            "task_id": task_id,
            "bound_decisions": list(decision_ids),
            "anomalies": anomalies,
            "valid_causality": len(anomalies) == 0,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status": "DECISION_CAUSALITY_MAP_COMPILED",
            "read_only_assertion": True,
        }
