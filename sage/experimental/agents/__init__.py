"""SAGE Experimental Agent Communication Bridge (SAGE-ACT Milestone 7)."""

import os
import re
from typing import Any, Dict, List
from datetime import datetime, timezone


class AgentIdentity:
    """Represents an authorized experimental agent identity persona."""

    def __init__(self, agent_id: str, name: str, role: str, authorized_capabilities: List[str]):
        if not re.match(r"^agent_[a-zA-Z0-9_]{3,64}$", agent_id):
            raise ValueError(f"SAGE Agent Bridge Error: Invalid agent_id format: '{agent_id}'")
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.authorized_capabilities = list(authorized_capabilities)


class AgentIdentityRegistry:
    """Registry holding authorized experimental agent identities."""

    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self._seed_default_identities()

    def register_identity(self, identity: AgentIdentity) -> None:
        """Registers a new identity in the registry."""
        self.identities[identity.agent_id] = identity

    def get_identity(self, agent_id: str) -> AgentIdentity:
        """Retrieves an identity or raises ValueError if unauthorized."""
        if agent_id not in self.identities:
            raise ValueError(f"SAGE Agent Bridge Error: Unauthorized or unregistered agent identity: '{agent_id}'")
        return self.identities[agent_id]

    def _seed_default_identities(self) -> None:
        """Seeds the default coordinator, executor, analyst, and reviewer personas."""
        # Coordinator (ChatGPT)
        self.register_identity(AgentIdentity(
            agent_id="agent_chatgpt",
            name="ChatGPT-Coordinator",
            role="Coordinator",
            authorized_capabilities=["coordinate_workflow", "delegate_task", "verify_results"]
        ))
        # Executor (Jules)
        self.register_identity(AgentIdentity(
            agent_id="agent_jules",
            name="Jules-Executor",
            role="Executor",
            authorized_capabilities=["write_code", "run_tests", "generate_evidence"]
        ))
        # Analyst (Claude)
        self.register_identity(AgentIdentity(
            agent_id="agent_claude",
            name="Claude-Analyst",
            role="Analyst",
            authorized_capabilities=["analyze_trace", "assess_risks", "verify_compliance"]
        ))
        # Reviewer (Gemini)
        self.register_identity(AgentIdentity(
            agent_id="agent_gemini",
            name="Gemini-Reviewer",
            role="Reviewer",
            authorized_capabilities=["review_receipts", "sign_off_promotion"]
        ))


class AgentCommunicationEnvelope:
    """Standardized communication envelope for carrying multi-agent handoffs."""

    def __init__(
        self,
        sender_id: str,
        receiver_id: str,
        capability_id: str,
        evidence_reference: str,
        human_review_status: str,
        timestamp: str,
        execution_trace_reference: str,
    ):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.capability_id = capability_id
        self.evidence_reference = evidence_reference
        self.human_review_status = human_review_status
        self.timestamp = timestamp
        self.execution_trace_reference = execution_trace_reference


class AgentHandoffValidator:
    """Validation engine enforcing SAGE security and lineage requirements on transitions."""

    PROTECTED_ENCLAVES = [
        "sage/runtime/",
        "sage/core/",
        "sage/acr/",
        "sage/agents/",
    ]

    def __init__(self, registry: AgentIdentityRegistry):
        self.registry = registry

    def validate_handoff(self, envelope: AgentCommunicationEnvelope, target_paths: List[str] = None) -> bool:
        """Performs seven strict verification checks on a single transition envelope."""
        # 1. Sender Existence Check
        sender = self.registry.get_identity(envelope.sender_id)

        # 2. Receiver Existence Check
        self.registry.get_identity(envelope.receiver_id)

        # 3. Capability Authorization Check
        if envelope.capability_id not in sender.authorized_capabilities:
            raise ValueError(
                f"SAGE Handoff Violation: Sender '{envelope.sender_id}' is not authorized "
                f"to execute capability '{envelope.capability_id}'."
            )

        # 4. Evidence Reference Check
        if not envelope.evidence_reference or envelope.evidence_reference.strip() == "":
            raise ValueError(f"SAGE Handoff Violation: Missing required evidence reference in envelope.")

        # 5. Timestamp Parse Check
        try:
            datetime.fromisoformat(envelope.timestamp.replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"SAGE Handoff Violation: Invalid ISO 8601 timestamp: '{envelope.timestamp}'")

        # 6. Human Review Gate Check
        if envelope.human_review_status != "APPROVED":
            raise ValueError(
                f"SAGE Handoff Violation: Capability promotion requires explicit human review. "
                f"Status is currently '{envelope.human_review_status}'."
            )

        # 7. Protected Path Rejection Check
        if target_paths:
            for path in target_paths:
                for enclave in self.PROTECTED_ENCLAVES:
                    if path.startswith(enclave) or path == enclave:
                        raise PermissionError(
                            f"SAGE Security Violation: Autonomous handoff attempted to write to "
                            f"protected core enclave path '{path}'. Execution blocked."
                        )

        return True

    def validate_sequence_chronology(self, envelopes: List[AgentCommunicationEnvelope]) -> bool:
        """Enforces that sequential handoff dispatch timestamps are strictly monotonically increasing."""
        if not envelopes:
            return True

        last_time = None
        for idx, env in enumerate(envelopes):
            try:
                curr_time = datetime.fromisoformat(env.timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                raise ValueError(f"SAGE Handoff Violation: Invalid timestamp at index {idx}: '{env.timestamp}'")

            if last_time is not None and curr_time < last_time:
                raise ValueError(
                    f"SAGE Handoff Violation: Chronological discontinuity. "
                    f"Timestamp '{env.timestamp}' is earlier than previous timestamp."
                )
            last_time = curr_time

        return True
