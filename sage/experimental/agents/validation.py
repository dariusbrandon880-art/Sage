"""SAGE Experimental Agent Handoff Validation."""

from typing import Any, Dict
from sage.experimental.agents.models import AgentCommunicationEnvelope
from sage.experimental.agents.registry import AgentIdentityRegistry


class AgentHandoffValidator:
    """Validator implementing 6 strict governance checks for multi-agent envelope handoffs."""

    def __init__(self, registry: AgentIdentityRegistry):
        self.registry = registry

    def validate_handoff(self, envelope: AgentCommunicationEnvelope) -> Dict[str, Any]:
        """Validate an AgentCommunicationEnvelope against SAGE governance rules.

        Raises:
            ValueError: If any validation checks fail.
        """
        # 1. Sender exists
        if not self.registry.contains(envelope.sender_identity):
            raise ValueError(f"Handoff Violation: Sender '{envelope.sender_identity}' is not registered.")

        # 2. Receiver exists
        if not self.registry.contains(envelope.receiver_identity):
            raise ValueError(f"Handoff Violation: Receiver '{envelope.receiver_identity}' is not registered.")

        # 3. Capability is allowed
        sender_identity = self.registry.get_agent(envelope.sender_identity)
        if envelope.authorized_capability not in sender_identity.permissions:
            raise ValueError(
                f"Handoff Violation: Sender '{envelope.sender_identity}' "
                f"lacks permission for capability '{envelope.authorized_capability}'."
            )

        # 4. Protected paths are rejected
        protected_patterns = ["sage/runtime/", "sage/core/", "sage/acr/", "sage/agents/"]
        for path in [envelope.expected_artifact, envelope.evidence_reference]:
            for pattern in protected_patterns:
                if pattern in path:
                    raise ValueError(f"Handoff Violation: Access to protected directory pattern '{pattern}' is strictly rejected.")

        # 5. Evidence reference is required
        if not envelope.evidence_reference or envelope.evidence_reference.strip() == "":
            raise ValueError("Handoff Violation: Missing required field 'evidence_reference'.")

        # 6. Human review is required
        if envelope.review_status != "HUMAN_APPROVAL_REQUIRED":
            raise ValueError("Handoff Violation: review_status must be set to 'HUMAN_APPROVAL_REQUIRED'.")

        return {
            "validation_status": "APPROVED_BY_VALIDATOR",
            "read_only_assertion": True,
        }
