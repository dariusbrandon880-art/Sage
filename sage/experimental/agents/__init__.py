"""SAGE Experimental Agent Communication Layer."""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class AgentCommunicationEnvelope:
    """Represents a validated agent-to-agent communication envelope."""

    def __init__(
        self,
        mission_id: str,
        sender_identity: str,
        receiver_identity: str,
        task_objective: str,
        authorized_capability: str,
        constraints: List[str],
        expected_artifact: str,
        evidence_reference: str,
        review_status: str,
    ):
        self.mission_id = mission_id
        self.sender_identity = sender_identity
        self.receiver_identity = receiver_identity
        self.task_objective = task_objective
        self.authorized_capability = authorized_capability
        self.constraints = constraints
        self.expected_artifact = expected_artifact
        self.evidence_reference = evidence_reference
        self.review_status = review_status

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to serializable dictionary."""
        return {
            "mission_id": self.mission_id,
            "sender_identity": self.sender_identity,
            "receiver_identity": self.receiver_identity,
            "task_objective": self.task_objective,
            "authorized_capability": self.authorized_capability,
            "constraints": list(self.constraints),
            "expected_artifact": self.expected_artifact,
            "evidence_reference": self.evidence_reference,
            "review_status": self.review_status,
        }


class ExperimentalAgentRegistry:
    """Tracks experimental agent identities, roles, capabilities, and restrictions."""

    def __init__(self):
        # Initialize default experimental identities
        self._registry = {
            "chatgpt-coordinator": {
                "agent_id": "chatgpt-coordinator",
                "role": "Coordinator",
                "allowed_capability": "CAP-ACT-001",
                "restrictions": ["No direct code modifications", "Sandbox only"],
            },
            "jules-engineer": {
                "agent_id": "jules-engineer",
                "role": "Engineer",
                "allowed_capability": "CAP-SCR-003",
                "restrictions": ["Sandbox writes only", "No production core modifications"],
            },
            "gemini-analyst": {
                "agent_id": "gemini-analyst",
                "role": "Analyst",
                "allowed_capability": "CAP-ANA-002",
                "restrictions": ["Read-only access"],
            },
            "claude-reviewer": {
                "agent_id": "claude-reviewer",
                "role": "Reviewer",
                "allowed_capability": "CAP-REV-004",
                "restrictions": ["Validation receipt auditing only"],
            },
        }

    def register_agent(self, agent_id: str, role: str, allowed_capability: str, restrictions: List[str]) -> None:
        """Register a new experimental agent identity."""
        self._registry[agent_id] = {
            "agent_id": agent_id,
            "role": role,
            "allowed_capability": allowed_capability,
            "restrictions": list(restrictions),
        }

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent registration details."""
        return self._registry.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self._registry.keys())


class EnvelopeValidator:
    """Validates Agent Communication Envelopes against registry rules and safety boundaries."""

    def __init__(self, registry: ExperimentalAgentRegistry):
        self.registry = registry

    def validate_envelope(self, envelope: AgentCommunicationEnvelope) -> Dict[str, Any]:
        """Validates the structure and safety invariants of an Agent Communication Envelope.

        Verifies:
        - Sender exists in registry
        - Receiver exists in registry
        - Capability is authorized for the sender
        - Protected paths are rejected in expected_artifact or constraints
        - Evidence reference is required and non-empty
        - Human review state exists in review_status
        """
        # 1. Sender validation
        sender = self.registry.get_agent(envelope.sender_identity)
        if not sender:
            raise ValueError(f"Envelope Validation Failure: Sender identity '{envelope.sender_identity}' is not registered.")

        # 2. Receiver validation
        receiver = self.registry.get_agent(envelope.receiver_identity)
        if not receiver:
            raise ValueError(f"Envelope Validation Failure: Receiver identity '{envelope.receiver_identity}' is not registered.")

        # 3. Capability authorization validation
        if sender["allowed_capability"] != envelope.authorized_capability:
            raise ValueError(
                f"Envelope Validation Failure: Capability '{envelope.authorized_capability}' "
                f"is not authorized for sender '{envelope.sender_identity}'."
            )

        # 4. Protected path rejection (sage/runtime/, sage/core/, sage/acr/)
        protected_patterns = [
            r"sage/runtime/.*",
            r"sage/core/.*",
            r"sage/acr/.*",
            r"^sage/runtime/?$",
            r"^sage/core/?$",
            r"^sage/acr/?$",
        ]

        def check_path_leak(value: str) -> None:
            for pattern in protected_patterns:
                if re.search(pattern, value):
                    raise ValueError(f"Envelope Validation Failure: Protected path access attempt detected: '{value}'")

        check_path_leak(envelope.expected_artifact)
        for constraint in envelope.constraints:
            check_path_leak(constraint)

        # 5. Evidence reference requirement
        if not envelope.evidence_reference or not envelope.evidence_reference.strip():
            raise ValueError("Envelope Validation Failure: Evidence reference is required and cannot be empty.")

        # 6. Human review state check
        valid_review_states = [
            "PENDING_MANUAL_AUDIT",
            "APPROVED_BY_GOVERNANCE",
            "REJECTED_BY_GOVERNANCE",
        ]
        if envelope.review_status not in valid_review_states:
            raise ValueError(
                f"Envelope Validation Failure: Invalid review_status '{envelope.review_status}'. "
                f"Must be one of {valid_review_states}."
            )

        return {
            "mission_id": envelope.mission_id,
            "validation_status": "ENVELOPE_VALIDATED",
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "read_only_assertion": True,
        }
