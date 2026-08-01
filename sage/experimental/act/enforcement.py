"""SAGE Experimental Capability Enforcement Hypervisor.

Implements SAGE-CPC Phase 3: Capability Enforcement Hypervisor under experimental isolation.
Acts as SAGE's active validation gateway during simulated agent execution.
"""

from typing import Dict, Any, List, Optional
from sage.experimental.agents.models import AgentCommunicationEnvelope
from sage.experimental.agents.validation import AgentHandoffValidator


class CapabilityEnforcementHypervisor:
    """Enforces active validation gates and blocks handoffs violating SAGE-CPC policies."""

    def __init__(self, handoff_validator: AgentHandoffValidator):
        """Initialize the hypervisor with an active handoff validator."""
        self.handoff_validator = handoff_validator
        self._passport_registry: Dict[str, Dict[str, Any]] = {}

    def register_passport(self, passport: Dict[str, Any]) -> None:
        """Registers a verified Capability Passport in SAGE-CPC.

        Args:
            passport: Capability Passport document dictionary.
        """
        cap_id = passport.get("capability_id")
        if not cap_id:
            raise ValueError("Enforcement Violation: Passport must contain a valid capability_id.")
        self._passport_registry[cap_id] = passport

    def get_passport(self, cap_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a registered passport."""
        return self._passport_registry.get(cap_id)

    def enforce_handoff_gate(
        self,
        envelope: AgentCommunicationEnvelope,
        execution_result: Dict[str, Any],
        human_approved: bool = False,
    ) -> Dict[str, Any]:
        """Intercepts, evaluates, and enforces safety gates on an active multi-agent handoff.

        Args:
            envelope: The active communication envelope being evaluated.
            execution_result: Task execution output payload.
            human_approved: Explicit human supervisor override flag.

        Returns:
            A dictionary containing validated execution results and audit trails.

        Raises:
            ValueError: If capability lacks a valid, human-approved passport or violates policies.
        """
        cap_id = envelope.authorized_capability

        # 1. Non-Bypassable Passport Check
        if cap_id not in self._passport_registry:
            raise ValueError(
                f"Enforcement Gate Blocked: Capability '{cap_id}' lacks a registered Capability Passport "
                f"(SAGE-CPC Boundary Violation). All active tasks must map to a documented capability."
            )

        passport = self._passport_registry[cap_id]

        # 2. Human Sign-Off Verification on Passport State
        signoff = passport.get("human_signoff", {})
        if not signoff.get("approved", False):
            raise ValueError(
                f"Enforcement Gate Blocked: Registered passport for capability '{cap_id}' is not human-approved. "
                f"SAGE 'No Orphan Capability' rule is active."
            )

        # 3. Handoff Validator Core Check
        # Enforces identity exists, receiver has capability permissions, and constraints are respected
        evidence_record = self.handoff_validator.validate_and_execute_handoff(
            envelope=envelope,
            execution_result=execution_result,
            human_approved=human_approved,
        )

        # 4. Generate Enforcement Trace
        return {
            "status": "AUTHORIZED_EXECUTION",
            "capability_id": cap_id,
            "evidence_record": evidence_record.to_dict(),
            "enforcement_telemetry": {
                "passport_verified": True,
                "identities_authorized": True,
                "constraints_respected": True,
                "human_gate_applied": True,
            }
        }
