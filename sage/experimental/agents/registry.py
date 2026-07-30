"""SAGE Experimental Agent Identity Registry."""

from typing import Any, Dict, List, Optional


class AgentIdentity:
    """Represents a validated, registered agent identity in the SAGE sandbox ecosystem."""

    def __init__(self, agent_id: str, role: str, permissions: List[str], restrictions: List[str]):
        self.agent_id = agent_id
        self.role = role
        self.permissions = permissions
        self.restrictions = restrictions


class AgentIdentityRegistry:
    """Registry maintaining seeded and dynamically validated agent identities."""

    def __init__(self):
        self._identities: Dict[str, AgentIdentity] = {}
        self._seed_default_identities()

    def register_agent(self, identity: AgentIdentity) -> None:
        """Register a new agent identity in the sandbox registry."""
        self._identities[identity.agent_id] = identity

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Look up and return an agent identity from the registry."""
        return self._identities.get(agent_id)

    def contains(self, agent_id: str) -> bool:
        """Check if an agent identity exists in the registry."""
        return agent_id in self._identities

    def _seed_default_identities(self) -> None:
        """Seed the 4 required participant personas as defined by governance order."""
        self.register_agent(
            AgentIdentity(
                agent_id="chatgpt-coordinator",
                role="coordinator",
                permissions=["cap_cmaps_validation", "simulate_handoff"],
                restrictions=["no_production_mutation", "no_network_access"],
            )
        )
        self.register_agent(
            AgentIdentity(
                agent_id="jules-engineer",
                role="executor",
                permissions=["cap_cmaps_validation", "execute_sandbox_tests"],
                restrictions=["no_production_mutation", "no_network_access"],
            )
        )
        self.register_agent(
            AgentIdentity(
                agent_id="gemini-analyst",
                role="analyst",
                permissions=["cap_cmaps_validation", "traverse_knowledge_graph"],
                restrictions=["no_production_mutation", "no_network_access"],
            )
        )
        self.register_agent(
            AgentIdentity(
                agent_id="claude-reviewer",
                role="reviewer",
                permissions=["cap_cmaps_validation", "human_review_gate_assist"],
                restrictions=["no_production_mutation", "no_network_access"],
            )
        )
