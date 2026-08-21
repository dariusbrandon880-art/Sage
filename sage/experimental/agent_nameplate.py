"""Persistent agent identity/nameplate for SAGE-facing response surfaces.

The nameplate is a truthful status surface, not an authority token. It exposes
only progression state supplied by SAGE and defaults to the lowest rank when
no verified progression evidence is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sage.experimental.agent_progression import AgentProgression


@dataclass(frozen=True)
class AgentNameplate:
    """Compact identity/progression payload for every SAGE response surface."""

    agent_id: str
    display_name: str
    station: str
    rank: str
    xp: int
    missions: int
    status: str = "ACTIVE"

    def as_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "station": self.station,
            "rank": self.rank,
            "xp": self.xp,
            "missions": self.missions,
            "status": self.status,
        }

    def compact(self) -> str:
        """Human-readable badge suitable for a persistent chat/status header."""
        return (
            f"[{self.display_name} · {self.rank} · {self.xp} XP · "
            f"{self.station} · {self.status}]"
        )


def build_nameplate(
    agent: AgentProgression,
    *,
    display_name: str,
    status: str = "ACTIVE",
) -> AgentNameplate:
    """Build a nameplate from canonical progression state without self-attestation."""
    if not display_name.strip():
        raise ValueError("display_name is required")
    if not status.strip():
        raise ValueError("status is required")

    return AgentNameplate(
        agent_id=agent.agent_id,
        display_name=display_name,
        station=agent.station,
        rank=agent.rank.value,
        xp=agent.xp,
        missions=agent.mission_count,
        status=status,
    )


def build_default_c2_nameplate() -> AgentNameplate:
    """Return the fail-closed C2 identity before verified progression is loaded."""
    return build_nameplate(
        AgentProgression(agent_id="agent_c2", station="Mission Control / C2"),
        display_name="C2",
    )
