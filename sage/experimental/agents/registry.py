"""SAGE Agent Identity Registry.

Manages registered identities, roles, and boundaries for experimental agents.
"""

from typing import Dict, Optional, List
from sage.experimental.agents.models import AgentIdentity


class AgentIdentityRegistry:
    """Central registry tracking active, authorized experimental agent identities."""

    def __init__(self, seed_defaults: bool = True):
        """Initialize the registry and optionally populate initial seed roles."""
        self._registry: Dict[str, AgentIdentity] = {}
        if seed_defaults:
            self._seed_initial_roles()

    def _seed_initial_roles(self) -> None:
        """Seeds the registry with standard SAGE agent personas, roles, and restrictions."""
        # 1. ChatGPT: Coordinator
        self.register_agent(
            AgentIdentity(
                agent_id="ChatGPT",
                role="Coordinator",
                permissions=["coordinate_missions", "delegate_tasks", "verify_evidence"],
                restrictions=["mutate_code", "execute_sandbox", "approve_promotions"],
            )
        )

        # 2. Jules: Engineering Executor
        self.register_agent(
            AgentIdentity(
                agent_id="Jules",
                role="Engineering Executor",
                permissions=["execute_sandbox", "write_experimental_code", "generate_evidence"],
                restrictions=["approve_promotions", "coordinate_missions", "direct_review"],
            )
        )

        # 3. Gemini: Independent Analyst
        self.register_agent(
            AgentIdentity(
                agent_id="Gemini",
                role="Independent Analyst",
                permissions=["analyze_metrics", "read_logs", "compile_readiness"],
                restrictions=["mutate_code", "execute_sandbox", "direct_review"],
            )
        )

        # 4. Claude: Adversarial Reviewer
        self.register_agent(
            AgentIdentity(
                agent_id="Claude",
                role="Adversarial Reviewer",
                permissions=["adversarial_audit", "review_receipts", "sign_human_reviews"],
                restrictions=["mutate_code", "execute_sandbox", "delegate_tasks"],
            )
        )

    def register_agent(self, identity: AgentIdentity) -> None:
        """Registers a new agent identity in the registry.

        Args:
            identity: The AgentIdentity instance to register.

        Raises:
            ValueError: If agent_id is invalid or already registered.
        """
        if not identity.agent_id or not identity.agent_id.strip():
            raise ValueError("Registry Violation: agent_id must be a non-empty string.")

        if identity.agent_id in self._registry:
            raise ValueError(f"Registry Violation: Agent ID '{identity.agent_id}' is already registered.")

        self._registry[identity.agent_id] = identity

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Retrieves an agent identity from the registry.

        Args:
            agent_id: The identifier of the target agent.

        Returns:
            The AgentIdentity instance if found, or None.
        """
        return self._registry.get(agent_id)

    def is_registered(self, agent_id: str) -> bool:
        """Checks if a given agent identifier is registered."""
        return agent_id in self._registry

    def list_agents(self) -> List[AgentIdentity]:
        """Returns all registered agent identities."""
        return list(self._registry.values())
