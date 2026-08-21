"""Default SAGE operating roster for persistent progression/nameplate surfaces."""

from __future__ import annotations

from sage.experimental.agent_nameplate import AgentNameplate, build_nameplate
from sage.experimental.agent_progression import AgentProgression


DEFAULT_ROSTER: tuple[tuple[str, str, str], ...] = (
    ("mission_director", "Mission Director", "Mission Director"),
    ("agent_c2", "C2", "Mission Control / C2"),
    ("agent_gemini", "Gemini", "Intel / Recon"),
    ("agent_jules", "Jules", "Engineering Flight"),
    ("sensor_super_search", "Super Search", "External Intelligence Sensor"),
)


def build_default_roster() -> dict[str, AgentProgression]:
    """Create a fail-closed roster; every station starts at CQL-0 until evidence exists."""
    return {
        agent_id: AgentProgression(agent_id=agent_id, station=station)
        for agent_id, _display_name, station in DEFAULT_ROSTER
    }


def build_roster_nameplates(
    roster: dict[str, AgentProgression] | None = None,
) -> tuple[AgentNameplate, ...]:
    """Render persistent identity badges from the supplied progression state."""
    state = roster or build_default_roster()
    return tuple(
        build_nameplate(state[agent_id], display_name=display_name)
        for agent_id, display_name, _station in DEFAULT_ROSTER
    )
