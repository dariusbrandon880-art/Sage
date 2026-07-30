"""SAGE Experimental Agent Models."""

from typing import Any, Dict, List, Optional


class AgentCommunicationEnvelope:
    """Represents a validated structured envelope for multi-agent task context handoffs."""

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
        """Convert envelope to a dictionary representation."""
        return {
            "mission_id": self.mission_id,
            "sender_identity": self.sender_identity,
            "receiver_identity": self.receiver_identity,
            "task_objective": self.task_objective,
            "authorized_capability": self.authorized_capability,
            "constraints": self.constraints,
            "expected_artifact": self.expected_artifact,
            "evidence_reference": self.evidence_reference,
            "review_status": self.review_status,
        }
