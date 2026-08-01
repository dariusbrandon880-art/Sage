"""SAGE Agent Activation Readiness Pilot Simulation Scaffolding."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AgentPilotSimulation:
    """Manages governed agent activation, execution, and revocation in a sandbox."""

    def __init__(self) -> None:
        self.state: str = "PROPOSED"
        self.agent_id: Optional[str] = None
        self.capability_id: Optional[str] = None
        self.identity_verified: bool = False
        self.capability_authorized: bool = False
        self.execution_trace: Optional[str] = None
        self.receipt: Optional[Dict[str, Any]] = None
        self.review_record: Optional[Dict[str, Any]] = None
        self.revoked: bool = False

    def reset(self) -> None:
        """Resets the simulator state."""
        self.state = "PROPOSED"
        self.agent_id = None
        self.capability_id = None
        self.identity_verified = False
        self.capability_authorized = False
        self.execution_trace = None
        self.receipt = None
        self.review_record = None
        self.revoked = False

    def register_agent(self, agent_id: str, capability_id: str) -> Dict[str, Any]:
        """Registers a mock agent identity and moves status to PROPOSED."""
        if not agent_id or not agent_id.startswith("agent_"):
            raise ValueError("Failure Validation: Invalid identity format.")
        if not capability_id or not capability_id.startswith("cap_"):
            raise ValueError("Failure Validation: Unauthorized capability format.")

        self.agent_id = agent_id
        self.capability_id = capability_id
        self.state = "PROPOSED"

        return {
            "state": self.state,
            "agent_id": self.agent_id,
            "capability_id": self.capability_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def activate_sandbox(self, sender: str, receiver: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Validates agent identities, capability, and task envelope to move to SANDBOX_ACTIVE."""
        if self.revoked:
            raise PermissionError("Failure Validation: Revoked capability prevents activation.")
        if self.state != "PROPOSED":
            raise ValueError("Lifecycle Violation: Can only activate sandbox from PROPOSED state.")

        # Identity validation
        valid_identities = ["chatgpt_coordinator", "jules_executor", "gemini_analyst", "claude_reviewer"]
        if sender not in valid_identities or receiver not in valid_identities:
            raise ValueError("Failure Validation: Invalid identity check.")

        # Task envelope validation
        required_fields = ["mission_id", "sender_identity", "receiver_identity", "task_objective", "authorized_capability"]
        for field in required_fields:
            if field not in envelope:
                raise ValueError("Failure Validation: Malformed envelope.")

        if envelope["authorized_capability"] != self.capability_id:
            raise ValueError("Failure Validation: Unauthorized capability requested.")

        self.identity_verified = True
        self.capability_authorized = True
        self.state = "SANDBOX_ACTIVE"

        return {
            "state": self.state,
            "envelope": envelope,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute_sandbox_task(self, target_path: str, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates constrained sandbox task execution and moves status to EVALUATED."""
        if self.state != "SANDBOX_ACTIVE":
            raise ValueError("Lifecycle Violation: Can only execute task from SANDBOX_ACTIVE state.")

        # Boundary violation check
        allowed_prefix = "sage/experimental/"
        if not target_path.startswith(allowed_prefix):
            raise PermissionError("Failure Validation: Boundary violation. Write attempts outside sage/experimental/ are blocked.")

        # Expired permission simulation
        if task_payload.get("expired_token", False):
            raise PermissionError("Failure Validation: Expired permission token.")

        self.execution_trace = f"Execution output trace at {target_path} for action {task_payload.get('action', 'unknown')}"
        self.receipt = {
            "receipt_id": f"receipt_{uuid.uuid4().hex[:12]}",
            "capability_id": self.capability_id,
            "validator_id": self.agent_id,
            "validation_result": "PASSED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "review_status": "PENDING",
            "archive_destination": "Main Archive/",
        }
        self.state = "EVALUATED"

        return {
            "state": self.state,
            "execution_trace": self.execution_trace,
            "receipt": self.receipt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def approve_capability(self, reviewer: str, decision: str, reference: str) -> Dict[str, Any]:
        """Runs the human review gate to promote the capability status to AUTHORIZED_EXPERIMENTAL."""
        if self.state != "EVALUATED":
            raise ValueError("Lifecycle Violation: Can only approve capability from EVALUATED state.")

        if decision == "REJECTED":
            self.state = "REVOKED"
            raise ValueError("Failure Validation: Capability rejected by human supervisor.")

        if decision != "APPROVED":
            raise ValueError("Failure Validation: Invalid human review decision.")

        self.review_record = {
            "review_id": f"rev_{uuid.uuid4().hex[:12]}",
            "reviewer_identity": reviewer,
            "review_decision": decision,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status": "VALIDATED_EXPERIMENTAL",
            "approval_reference": reference,
        }
        self.state = "AUTHORIZED_EXPERIMENTAL"

        return {
            "state": self.state,
            "review_record": self.review_record,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def revoke_capability(self) -> Dict[str, Any]:
        """Revokes capability status to REVOKED, blocking any future sandbox execution."""
        self.revoked = True
        self.state = "REVOKED"

        return {
            "state": self.state,
            "revocation_timestamp": datetime.now(timezone.utc).isoformat(),
            "block_future_activation": True,
        }
