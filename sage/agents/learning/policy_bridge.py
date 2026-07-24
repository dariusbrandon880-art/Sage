"""SAGE Agent Policy Bridge under Phase 4.2 SAGE Learning Runtime Activation."""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Set
from sage.core.version import SPEK_VERSION


class AgentPolicyBridge:
    """SPEK Policy Bridge managing verification of learning agent proposals."""

    def __init__(self, authorized_agents: Set[str] = None):
        # Default authorized learning agents
        self.authorized_agents = authorized_agents or {
            "SAGE_LEARNING_AGENT_001",
            "SAGE_COGNITIVE_LEARNER_v1",
        }

    def evaluate_proposal(
        self,
        agent_id: str,
        proposed_delta: Dict[str, Any],
        evidence_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluates a proposed learning delta from an agent and generates a SPEK validation receipt.

        Args:
            agent_id: The identifier of the agent proposing the change.
            proposed_delta: Dictionary of proposed architectural or parameter modifications.
            evidence_metadata: Metadata verifying observations and performance indices.

        Returns:
            A validation receipt dict matching the SAGE 2 SPEK contract.
        """
        # 1. Deterministic SHA-256 hash generation of proposed delta
        serialized_delta = json.dumps(proposed_delta, sort_keys=True)
        proposal_hash = hashlib.sha256(serialized_delta.encode("utf-8")).hexdigest()

        # 2. Agent Authorization Check
        if agent_id not in self.authorized_agents:
            status = "REJECTED"
        else:
            # If the evidence validates requirements, status can be AUTHORIZED or PENDING_VALIDATION
            # For authorized agents with a valid evidence trace, we mark as AUTHORIZED
            if evidence_metadata.get("requires_manual_gate", False):
                status = "PENDING_VALIDATION"
            else:
                status = "AUTHORIZED"

        receipt = {
            "agent_id": agent_id,
            "proposal_hash": proposal_hash,
            "spek_version": SPEK_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }
        return receipt
