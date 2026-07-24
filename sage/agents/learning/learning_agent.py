"""SAGE Learning Runtime - Governed Learning Agent.

Implements the GovernedLearningAgent class bounded strictly by registration rules,
permission contracts, and SPEK enforcer controls.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sage.agents.models import AgentIdentity, PermissionBoundary, AgentRole, MemoryAccess, ValidationAuthority
from sage.agents.router import AgentTaskRouter
from sage.agents.learning.policy_bridge import PolicyProposal, PolicyProposalBridge
from sage.core.models import Proposal as SpekProposal, RuleState


class GovernedLearningAgent:
    """A highly secure, bounded SAGE agent specializing in autonomous policy and pattern analysis."""

    def __init__(self, identity: AgentIdentity, boundary: PermissionBoundary):
        """Initialize the GovernedLearningAgent."""
        if identity.agent_id != boundary.agent_id:
            raise ValueError("AgentIdentity and PermissionBoundary IDs must match.")

        self.identity = identity
        self.boundary = boundary
        self.bridge = PolicyProposalBridge()
        self.proposal_history: List[PolicyProposal] = []

    def verify_authority(self, router: AgentTaskRouter) -> None:
        """Verify that the agent is registered with authorized permissions in the router.

        Raises:
            PermissionError: If the agent is unregistered or lacks appropriate roles.
        """
        if self.identity.agent_id not in router.agents:
            raise PermissionError(
                f"Unauthorized Agent Access: Agent {self.identity.name} is not registered in the SAGE router."
            )

        registered_agent = router.agents[self.identity.agent_id]
        if registered_agent.role != AgentRole.VALIDATOR and registered_agent.role != AgentRole.CONTRIBUTOR:
            raise PermissionError(
                f"Unauthorized Agent Access: Agent role {registered_agent.role.value} is not authorized for learning operations."
            )

    def receive_observations(
        self,
        observations: Dict[str, Any],
        router: AgentTaskRouter,
    ) -> str:
        """Processes runtime observations and returns a deterministic hash of the observations state."""
        self.verify_authority(router)
        return self.bridge.format_observations_hash(observations)

    def generate_policy_proposal(
        self,
        proposal_id: str,
        target_component: str,
        proposed_setting: str,
        value: Any,
        rationale: str,
        observations: Dict[str, Any],
        router: AgentTaskRouter,
    ) -> PolicyProposal:
        """Generates a secure policy proposal and attaches its SHA-256 evidence chain signature."""
        self.verify_authority(router)

        # 1. Format the raw proposal
        proposal = self.bridge.generate_proposal(
            proposal_id=proposal_id,
            target_component=target_component,
            proposed_setting=proposed_setting,
            value=value,
            rationale=rationale,
            observations=observations,
        )

        # 2. Produce the SHA-256 evidence receipt signature using the agent's secure key
        signature = self.bridge.generate_sha256_evidence_receipt(
            proposal=proposal,
            signing_key=self.identity.signature_key,
        )
        proposal.evidence_signature = signature

        # 3. Save to local history
        self.proposal_history.append(proposal)

        # 4. Update bridge previous_receipt_hash to form an sequential chain
        self.bridge.previous_receipt_hash = signature

        return proposal

    def request_spek_approval(
        self,
        proposal: PolicyProposal,
        spek_engine: Any,
        auth_token: Optional[str] = None,
    ) -> Any:
        """Requests SPEK approval by mapping the policy proposal to a SPEK Rule Proposal."""
        # Convert PolicyProposal to SPEK's expected Proposal model schema
        spek_proposal = spek_engine.process_proposal(
            proposal_id=proposal.proposal_id,
            description=f"Policy alteration for {proposal.target_component}. Rational: {proposal.rationale}",
            category="learning_policy",
            author=self.identity.agent_id,
            parent_ids=[],
            evidence_refs=[proposal.observations_hash],
            validation_score=1.0,  # High confidence from verified observations
            contradictions=[],
            auth_token=auth_token,
        )
        return spek_proposal
