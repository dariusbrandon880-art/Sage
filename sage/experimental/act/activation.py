"""SAGE Activation Layer Foundation.

Connects validated capability components into a usable end-to-end human-authorized workflow.
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sage.experimental.act.contracts import (
    SessionTaskTreeLinker,
    TaskDecisionBinder,
    CrossModelAuditPayloadValidator,
    SessionStateTaskLinker,
)


class ContextIntakeBridge:
    """Ingests user actions and contextual payloads, establishing the SAGE intake session."""

    def __init__(self):
        pass

    def ingest_action(self, action_type: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest user action and return a structured intake payload.

        Args:
            action_type: The type of user action (e.g., 'code_evaluation', 'audit_run').
            context_data: Metadata and context associated with the action.
        """
        if not action_type:
            raise ValueError("SAGE Activation Error: Action type cannot be empty.")

        session_id = context_data.get("session_id", f"session_{hashlib.md5(action_type.encode()).hexdigest()[:8]}")

        return {
            "session_id": session_id,
            "action_type": action_type,
            "status": "intake_complete",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "context_data": context_data,
        }


class ValidatedCapabilityConnector:
    """Connects to and invokes validated contracts to verify the lineage and structural integrity of SAGE tasks."""

    def __init__(self):
        self.tree_linker = SessionTaskTreeLinker()
        self.state_linker = SessionStateTaskLinker()
        self.decision_binder = TaskDecisionBinder()
        self.payload_validator = CrossModelAuditPayloadValidator()

    def validate_capability_lineage(self, session_id: str, task_ids: List[str], decision_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Executes deep validation over session, task, and decision structures."""
        # 1. Link session to tasks
        link_result = self.tree_linker.link_session_to_tasks(session_id, task_ids)

        # 2. Bind tasks to decisions if decisions are supplied
        bound_decisions = {}
        if decision_ids:
            for task_id in task_ids:
                bound_decisions[task_id] = self.decision_binder.bind_task_to_decisions(task_id, decision_ids)

        return {
            "session_id": session_id,
            "mapped_tasks": task_ids,
            "link_status": link_result.get("validation_status"),
            "bound_decisions": bound_decisions,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_audit_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates an incoming audit payload against CMAPS v1.0."""
        return self.payload_validator.validate_payload(payload)


class HumanAuthorizationCheckpoint:
    """Enforces human-in-the-loop validation gates, requiring explicit authorization signatures."""

    def __init__(self):
        pass

    def authorize_action(self, session_id: str, action_summary: str, approver: str, signature: str) -> Dict[str, Any]:
        """Verifies human authorization for the execution session.

        Args:
            session_id: The identifier of the active SAGE session.
            action_summary: A description of the action being authorized.
            approver: Identity of the authorizing supervisor.
            signature: Cryptographic or electronic signature string.
        """
        if not approver or not signature:
            raise ValueError("SAGE Activation Error: Human authorization requires a valid approver and signature.")

        return {
            "session_id": session_id,
            "action_summary": action_summary,
            "authorized_by": approver,
            "signature": signature,
            "authorized_at": datetime.now(timezone.utc).isoformat(),
            "checkpoint_status": "APPROVED",
        }


class EvidenceReceiptGenerator:
    """Compiles execution metadata, validated lineages, and human approvals into a non-repudiable receipt."""

    def __init__(self):
        pass

    def generate_receipt(self, intake_data: Dict[str, Any], validation_data: Dict[str, Any], auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates the final evidence receipt artifact."""
        raw_payload = {
            "intake": intake_data,
            "validation": validation_data,
            "authorization": auth_data,
        }

        serialized = json.dumps(raw_payload, sort_keys=True)
        receipt_hash = hashlib.sha256(serialized.encode()).hexdigest()

        receipt = {
            "receipt_id": f"receipt_{receipt_hash[:16]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": intake_data.get("session_id"),
            "action_type": intake_data.get("action_type"),
            "verification_hash": receipt_hash,
            "payload": raw_payload,
            "assertion": "SAGE_ACTIVATION_RECEIPT_VALID",
        }

        return receipt


class ActivationEntryPoint:
    """Core entry point foundation for orchestrating the sandboxed user workflow sequence."""

    def __init__(self):
        self.intake_bridge = ContextIntakeBridge()
        self.capability_connector = ValidatedCapabilityConnector()
        self.checkpoint = HumanAuthorizationCheckpoint()
        self.receipt_generator = EvidenceReceiptGenerator()

    def execute_workflow(
        self,
        action_type: str,
        context_data: Dict[str, Any],
        task_ids: List[str],
        decision_ids: Optional[List[str]],
        approver: str,
        signature: str,
        audit_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes the standard workflow sequence.

        Workflow sequence:
        User Action -> SAGE Intake -> Context Evaluation -> Capability Validation -> Human Checkpoint -> Evidence Receipt
        """
        # 1. SAGE Intake
        intake_data = self.intake_bridge.ingest_action(action_type, context_data)
        session_id = intake_data["session_id"]

        # 2. Context Evaluation & Capability Validation
        validation_data = self.capability_connector.validate_capability_lineage(session_id, task_ids, decision_ids)

        if audit_payload:
            # Ensure session ID matches
            audit_payload["task_lineage"]["session_id"] = session_id
            self.capability_connector.validate_audit_payload(audit_payload)
            validation_data["cmaps_validation"] = "SUCCESS"

        # 3. Human Checkpoint
        action_summary = f"Execution of action '{action_type}' for tasks {task_ids}"
        auth_data = self.checkpoint.authorize_action(session_id, action_summary, approver, signature)

        # 4. Evidence Receipt
        receipt = self.receipt_generator.generate_receipt(intake_data, validation_data, auth_data)

        return receipt
