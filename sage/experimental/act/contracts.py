"""SAGE Agent Continuity Tree Read-Only Interface Contracts."""

import re
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


class CrossModelAuditPayloadValidator:
    """Enforces programmatic, read-only validation for the Cross-Model Audit Payload Schema.

    Strictly complies with the SAGE Cross-Model Audit Payload Schema v1.0, checking
    agent and model identity fields, execution state telemetry, hierarchical task
    lineages, chronological invariants, and relational uniqueness constraints.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize the cross-model audit payload validator."""
        self.validation_mode = validation_mode

    def validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates an incoming audit payload against SAGE CMAPS v1.0 rules.

        Args:
            payload: The dictionary representation of the audit payload.

        Returns:
            A metadata dictionary indicating successful validation and status.

        Raises:
            ValueError: If any structural, format, chronological, or relational checks fail.
        """
        if not isinstance(payload, dict):
            raise ValueError("CMAPS Violation: Payload must be a dictionary.")

        # 1. Structural Field Existence Checks
        required_top_level = [
            "audit_id",
            "timestamp",
            "agent_identity",
            "model_provider",
            "execution_state",
            "task_lineage",
            "decision_events",
            "failure_events",
            "recovery_checkpoints",
            "evidence_relationships",
            "attestation",
        ]
        for field in required_top_level:
            if field not in payload:
                raise ValueError(f"CMAPS Violation: Missing required top-level field '{field}'.")

        # 2. Check inner structures and required sub-fields
        # Agent Identity
        agent_id_data = payload["agent_identity"]
        if not isinstance(agent_id_data, dict):
            raise ValueError("CMAPS Violation: 'agent_identity' must be a dictionary.")
        required_agent = ["agent_id", "name", "role", "governance_tier"]
        for field in required_agent:
            if field not in agent_id_data:
                raise ValueError(f"CMAPS Violation: Missing 'agent_identity.{field}'.")

        # Model Provider
        provider_data = payload["model_provider"]
        if not isinstance(provider_data, dict):
            raise ValueError("CMAPS Violation: 'model_provider' must be a dictionary.")
        required_provider = ["provider", "model_name", "temperature"]
        for field in required_provider:
            if field not in provider_data:
                raise ValueError(f"CMAPS Violation: Missing 'model_provider.{field}'.")

        # Execution State
        exec_state = payload["execution_state"]
        if not isinstance(exec_state, dict):
            raise ValueError("CMAPS Violation: 'execution_state' must be a dictionary.")
        required_exec = ["run_id", "status", "step_counter", "started_at", "updated_at"]
        for field in required_exec:
            if field not in exec_state:
                raise ValueError(f"CMAPS Violation: Missing 'execution_state.{field}'.")

        # Task Lineage
        task_lineage = payload["task_lineage"]
        if not isinstance(task_lineage, dict):
            raise ValueError("CMAPS Violation: 'task_lineage' must be a dictionary.")
        required_lineage = ["session_id", "current_task_id", "subtask_ids"]
        for field in required_lineage:
            if field not in task_lineage:
                raise ValueError(f"CMAPS Violation: Missing 'task_lineage.{field}'.")

        # Attestation
        attestation = payload["attestation"]
        if not isinstance(attestation, dict):
            raise ValueError("CMAPS Violation: 'attestation' must be a dictionary.")
        required_attestation = ["nonce", "signature", "signer_identity"]
        for field in required_attestation:
            if field not in attestation:
                raise ValueError(f"CMAPS Violation: Missing 'attestation.{field}'.")

        # 3. Format and Pattern Verification
        # audit_id: ^audit_[a-fA-F0-9]{32}$
        if not re.match(r"^audit_[a-fA-F0-9]{32}$", payload["audit_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'audit_id': '{payload['audit_id']}'")

        # agent_identity.agent_id: ^agent_[a-zA-Z0-9_]{3,64}$
        if not re.match(r"^agent_[a-zA-Z0-9_]{3,64}$", agent_id_data["agent_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'agent_id': '{agent_id_data['agent_id']}'")

        # execution_state.run_id: ^run_[a-zA-Z0-9]{20,40}$
        if not re.match(r"^run_[a-zA-Z0-9]{20,40}$", exec_state["run_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'run_id': '{exec_state['run_id']}'")

        # task_lineage.session_id: ^session_[a-fA-F0-9]{8}$
        if not re.match(r"^session_[a-fA-F0-9]{8}$", task_lineage["session_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'session_id': '{task_lineage['session_id']}'")

        # task_lineage.current_task_id: ^task_[a-zA-Z0-9_]{3,128}$
        if not re.match(r"^task_[a-zA-Z0-9_]{3,128}$", task_lineage["current_task_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'current_task_id': '{task_lineage['current_task_id']}'")

        # task_lineage.parent_task_id: ^task_[a-zA-Z0-9_]{3,128}$ (if present)
        if "parent_task_id" in task_lineage and task_lineage["parent_task_id"] is not None:
            if not re.match(r"^task_[a-zA-Z0-9_]{3,128}$", task_lineage["parent_task_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'parent_task_id': '{task_lineage['parent_task_id']}'")

        # List fields checks
        if not isinstance(payload["decision_events"], list):
            raise ValueError("CMAPS Violation: 'decision_events' must be a list.")
        for dec in payload["decision_events"]:
            if not isinstance(dec, dict):
                raise ValueError("CMAPS Violation: Decision entry must be a dictionary.")
            for f in ["decision_id", "timestamp", "summary", "reasoning", "confidence"]:
                if f not in dec:
                    raise ValueError(f"CMAPS Violation: Decision missing required field '{f}'.")
            if not re.match(r"^(decision|proposal)_[a-zA-Z0-9_]{3,128}$", dec["decision_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'decision_id': '{dec['decision_id']}'")

        if not isinstance(payload["failure_events"], list):
            raise ValueError("CMAPS Violation: 'failure_events' must be a list.")
        for fail in payload["failure_events"]:
            if not isinstance(fail, dict):
                raise ValueError("CMAPS Violation: Failure entry must be a dictionary.")
            for f in ["failure_id", "timestamp", "error_type", "message", "severity"]:
                if f not in fail:
                    raise ValueError(f"CMAPS Violation: Failure missing required field '{f}'.")
            if not re.match(r"^fail_[a-zA-Z0-9_]{3,128}$", fail["failure_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'failure_id': '{fail['failure_id']}'")

        if not isinstance(payload["recovery_checkpoints"], list):
            raise ValueError("CMAPS Violation: 'recovery_checkpoints' must be a list.")
        for chk in payload["recovery_checkpoints"]:
            if not isinstance(chk, dict):
                raise ValueError("CMAPS Violation: Checkpoint entry must be a dictionary.")
            for f in ["checkpoint_id", "timestamp", "rehydration_token", "requires_human_approval"]:
                if f not in chk:
                    raise ValueError(f"CMAPS Violation: Checkpoint missing required field '{f}'.")
            if not re.match(r"^chk_[a-zA-Z0-9_]{3,128}$", chk["checkpoint_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'checkpoint_id': '{chk['checkpoint_id']}'")

        # 4. Chronological Invariants Checks
        try:
            started_at = datetime.fromisoformat(exec_state["started_at"].replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(exec_state["updated_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"CMAPS Violation: Invalid timestamp format in execution_state: {e}")

        # started_at <= updated_at
        if started_at > updated_at:
            raise ValueError(
                f"CMAPS Violation: Chronological mismatch. Run 'started_at' ({started_at}) "
                f"is strictly later than 'updated_at' ({updated_at})."
            )

        # decision timestamps >= started_at
        for dec in payload["decision_events"]:
            try:
                dec_time = datetime.fromisoformat(dec["timestamp"].replace("Z", "+00:00"))
            except (ValueError, TypeError) as e:
                raise ValueError(f"CMAPS Violation: Invalid timestamp format in decision '{dec['decision_id']}': {e}")
            if dec_time < started_at:
                raise ValueError(
                    f"CMAPS Violation: Chronological mismatch. Decision '{dec['decision_id']}' "
                    f"timestamp ({dec_time}) is strictly earlier than run start time ({started_at})."
                )

        # failure timestamps <= checkpoint timestamps
        for fail in payload["failure_events"]:
            try:
                fail_time = datetime.fromisoformat(fail["timestamp"].replace("Z", "+00:00"))
            except (ValueError, TypeError) as e:
                raise ValueError(f"CMAPS Violation: Invalid timestamp format in failure '{fail['failure_id']}': {e}")
            for chk in payload["recovery_checkpoints"]:
                try:
                    chk_time = datetime.fromisoformat(chk["timestamp"].replace("Z", "+00:00"))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"CMAPS Violation: Invalid timestamp format in checkpoint '{chk['checkpoint_id']}': {e}")
                if fail_time > chk_time:
                    raise ValueError(
                        f"CMAPS Violation: Chronological mismatch. Intercepted failure '{fail['failure_id']}' "
                        f"timestamp ({fail_time}) occurred after checkpoint snapshot '{chk['checkpoint_id']}' ({chk_time})."
                    )

        # 5. Relational and Multi-Set Uniqueness Constraints
        subtask_ids = task_lineage["subtask_ids"]
        if not isinstance(subtask_ids, list):
            raise ValueError("CMAPS Violation: 'subtask_ids' must be a list of strings.")
        current_task_id = task_lineage["current_task_id"]

        # current_task_id not in subtask_ids
        if current_task_id in subtask_ids:
            raise ValueError(
                f"CMAPS Violation: Relational loop detected. 'current_task_id' ('{current_task_id}') "
                f"is listed as one of its own 'subtask_ids'."
            )

        # Unique decision_id values
        seen_decision_ids = set()
        for dec in payload["decision_events"]:
            dec_id = dec["decision_id"]
            if dec_id in seen_decision_ids:
                raise ValueError(f"CMAPS Violation: Duplicate decision ID detected: '{dec_id}'.")
            seen_decision_ids.add(dec_id)

        # Unique rehydration tokens
        seen_tokens = set()
        for chk in payload["recovery_checkpoints"]:
            token = chk["rehydration_token"]
            if token in seen_tokens:
                raise ValueError(f"CMAPS Violation: Duplicate rehydration token detected: '{token}'.")
            seen_tokens.add(token)

        # 6. Read-only verification metadata response
        return {
            "audit_id": payload["audit_id"],
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "SCHEMA_VALIDATED",
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
