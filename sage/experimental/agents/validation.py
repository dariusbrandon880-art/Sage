"""SAGE Experimental Agent Handoff Validation.

Enforces SAGE's multi-agent coordination boundaries, schema integrity, and evidence capture rules.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from sage.experimental.agents.models import (
    AgentCommunicationEnvelope,
    HandoffEvidenceRecord,
)
from sage.experimental.agents.registry import AgentIdentityRegistry


class AgentHandoffValidator:
    """Enforces boundaries, permissions, and evidence standards for multi-agent communication."""

    def __init__(self, registry: AgentIdentityRegistry):
        """Initialize the validator with an active identity registry."""
        self.registry = registry

    def validate_and_execute_handoff(
        self,
        envelope: AgentCommunicationEnvelope,
        execution_result: Dict[str, Any],
        human_approved: bool = False,
    ) -> HandoffEvidenceRecord:
        """Validates an agent-to-agent communication envelope and outputs a signed evidence record.

        Args:
            envelope: The formal communication envelope.
            execution_result: The result payload of the delegated task.
            human_approved: Explicit flag indicating manual supervisor sign-off.

        Returns:
            A HandoffEvidenceRecord capturing the handoff trace.

        Raises:
            ValueError: If identity, capability, task boundaries, or evidence constraints are violated.
        """
        # 1. Structural Validation of the 9 envelope fields
        env_dict = envelope.to_dict()
        required_fields = [
            "mission_id",
            "sender_identity",
            "receiver_identity",
            "task_objective",
            "authorized_capability",
            "constraints",
            "expected_artifact",
            "evidence_reference",
            "review_status",
        ]
        for field in required_fields:
            if field not in env_dict or env_dict[field] is None:
                raise ValueError(f"Handoff Violation: Missing required envelope field '{field}'.")

        # Non-empty string checks
        for field in ["mission_id", "sender_identity", "receiver_identity", "task_objective", "authorized_capability", "expected_artifact", "evidence_reference"]:
            val = env_dict[field]
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"Handoff Violation: Envelope field '{field}' must be a non-empty string.")

        if not isinstance(envelope.constraints, list):
            raise ValueError("Handoff Violation: Envelope 'constraints' must be a list of strings.")

        # 2. Identity Existence Check
        sender = self.registry.get_agent(envelope.sender_identity)
        receiver = self.registry.get_agent(envelope.receiver_identity)

        if not sender:
            raise ValueError(f"Handoff Violation: Sender identity '{envelope.sender_identity}' is not registered.")
        if not receiver:
            raise ValueError(f"Handoff Violation: Receiver identity '{envelope.receiver_identity}' is not registered.")

        # 3. Capability Authorization Check
        # Verify that the receiver possesses the appropriate permissions to handle the authorized capability
        needed_permission = None
        if envelope.authorized_capability == "cap_sdr_sim_engine":
            needed_permission = "execute_sandbox"
        elif envelope.authorized_capability == "cap_coordination":
            needed_permission = "coordinate_missions"
        elif envelope.authorized_capability == "cap_adversarial_audit":
            needed_permission = "adversarial_audit"
        elif envelope.authorized_capability == "cap_metrics_compilation":
            needed_permission = "analyze_metrics"

        if needed_permission and needed_permission not in receiver.permissions:
            raise ValueError(
                f"Handoff Violation: Receiver '{receiver.agent_id}' lacks required permission "
                f"'{needed_permission}' for capability '{envelope.authorized_capability}'."
            )

        # 4. Task Boundary and Constraints Check
        # If 'no-code-mutation' is defined as a constraint, verify receiver is restricted or doesn't have mutate permission
        if "no-code-mutation" in envelope.constraints:
            if "mutate_code" in receiver.permissions:
                raise ValueError(
                    f"Handoff Violation: Task constraint violation. Receiver '{receiver.agent_id}' has permission "
                    f"'mutate_code' which violates the 'no-code-mutation' task constraint."
                )

        # 5. Evidence Output Check
        # Expected artifact and evidence reference must point to valid documentation/evidence capture paths
        if not envelope.expected_artifact.endswith(".json") and not envelope.expected_artifact.endswith(".md"):
            raise ValueError(
                f"Handoff Violation: Invalid expected_artifact format: '{envelope.expected_artifact}'. "
                f"Must end with .json or .md."
            )
        if not envelope.evidence_reference.startswith("docs/") and not envelope.evidence_reference.startswith("evidence_capture/"):
            raise ValueError(
                f"Handoff Violation: Evidence reference must point to docs/ or evidence_capture/, got: '{envelope.evidence_reference}'"
            )

        # 6. Human Approval Validation
        # Human approval remains the final authority. If False, the review status remains "pending"
        review_status = "approved" if human_approved else "pending"

        # Generate and return evidence record
        return HandoffEvidenceRecord(
            envelope=env_dict,
            execution_result=execution_result,
            artifact_reference=envelope.expected_artifact,
            review_status=review_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
