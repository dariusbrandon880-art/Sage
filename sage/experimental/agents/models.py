"""SAGE Experimental Agent Communication Models.

Defines the Agent Identity Registry models and the structured Agent Communication Envelope.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentIdentity:
    """Represents an agent's registered identity within the experimental framework."""
    agent_id: str
    role: str
    permissions: List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert identity model to dictionary format."""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "permissions": list(self.permissions),
            "restrictions": list(self.restrictions),
        }


@dataclass
class AgentCommunicationEnvelope:
    """The formal message envelope exchanged during multi-agent handoffs.

    Enforces the 9-field SAGE Agent Communication Envelope standard.
    """
    mission_id: str
    sender_identity: str
    receiver_identity: str
    task_objective: str
    authorized_capability: str
    constraints: List[str]
    expected_artifact: str
    evidence_reference: str
    review_status: str  # "pending", "approved", "rejected"

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary representation."""
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


@dataclass
class HandoffEvidenceRecord:
    """Captured evidence from a completed agent-to-agent handoff."""
    envelope: Dict[str, Any]
    execution_result: Dict[str, Any]
    artifact_reference: str
    review_status: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence record to dictionary representation."""
        return {
            "envelope": self.envelope,
            "execution_result": self.execution_result,
            "artifact_reference": self.artifact_reference,
            "review_status": self.review_status,
            "timestamp": self.timestamp,
        }
