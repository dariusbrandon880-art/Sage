"""Registry components for SAGE Multi-Agent Coordination Layer."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from sage.agents.models import AgentIdentity, PermissionBoundary, AgentRole


class CoordinatedAgentProfile(BaseModel):
    """Profile of an agent registered under SAGE Multi-Agent Coordination."""

    agent_id: str
    agent_type: str  # e.g., "CHATGPT", "GOOGLE_AI", "JULES", "SAGE_COGNITIVE"
    role: AgentRole
    permissions: List[str] = Field(default_factory=list)
    status: str = "active"  # "active", "suspended", "idle"
    validation_level: str = "low"  # "low", "medium", "high"
    boundary: PermissionBoundary


class MultiAgentRegistry:
    """Manages secure registration, tracking, and boundary profile retrievals of coordinated agents."""

    def __init__(self):
        """Initialize MultiAgentRegistry."""
        self.profiles: Dict[str, CoordinatedAgentProfile] = {}

    def register_coordinated_agent(self, profile: CoordinatedAgentProfile) -> None:
        """Register a coordinated agent profile under SAGE multi-agent rules.

        Args:
            profile: CoordinatedAgentProfile of the agent.
        """
        self.profiles[profile.agent_id] = profile

    def get_coordinated_agent(self, agent_id: str) -> CoordinatedAgentProfile:
        """Retrieve a registered agent's coordination profile.

        Args:
            agent_id: Target agent ID.

        Returns:
            CoordinatedAgentProfile of the agent.
        """
        if agent_id not in self.profiles:
            raise KeyError(f"Coordination Error: Agent '{agent_id}' is not registered under multi-agent coordination.")
        return self.profiles[agent_id]

    def list_agents_by_type(self, agent_type: str) -> List[CoordinatedAgentProfile]:
        """List all registered agents matching a specific type.

        Args:
            agent_type: Target agent type string.

        Returns:
            List of CoordinatedAgentProfile.
        """
        return [p for p in self.profiles.values() if p.agent_type.upper() == agent_type.upper()]
