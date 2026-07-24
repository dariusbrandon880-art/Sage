"""SAGE Learning Agent under Phase 4.2 Learning Agent Boundary."""

import hashlib
import json
from typing import Dict, Any, List
from sage.agents.learning.policy_bridge import AgentPolicyBridge


class SAGELearningAgent:
    """A bounded learning agent that observes runtime execution and proposes improvements.

    Strict Observer Principle: Learning agents can only observe runtime events and
    request SPEK authorization via policy bridge. They are programmatically restricted
    from directly mutating runtime state, production configurations, or system files.
    """

    def __init__(self, agent_id: str, policy_bridge: AgentPolicyBridge):
        self.agent_id = agent_id
        self.policy_bridge = policy_bridge
        self.observed_events: List[Dict[str, Any]] = []

    def observe_runtime_event(self, event: Dict[str, Any]) -> None:
        """Observes and logs a runtime system telemetry or performance event.

        This is a read-only operation. No state mutations on the runtime are allowed.
        """
        if not isinstance(event, dict):
            raise TypeError("Event data must be a dictionary.")
        # Store event observer-side only
        self.observed_events.append(event)

    def propose_improvement(
        self,
        target: str,
        current_value: Any,
        proposed_value: Any,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates a structured improvement proposal and requests SPEK authorization.

        Enforces that proposals are formally authorized via the Policy Bridge before
        they can be applied to any system variables.
        """
        # Ensure learning agent does not attempt direct disk or config mutation
        # Reject any direct modifications of protected files or configurations
        for key in ["config_file_path", "runtime_state_path", "system_file_path"]:
            if key in evidence or key in proposed_value if isinstance(proposed_value, dict) else False:
                raise PermissionError("Security Boundary Violation: Direct system file mutations are prohibited.")

        proposed_delta = {
            "target": target,
            "current_value": current_value,
            "proposed_value": proposed_value,
        }

        # Request SPEK authorization through the authorized policy bridge
        receipt = self.policy_bridge.evaluate_proposal(
            agent_id=self.agent_id,
            proposed_delta=proposed_delta,
            evidence_metadata=evidence
        )

        return {
            "proposed_delta": proposed_delta,
            "receipt": receipt
        }
