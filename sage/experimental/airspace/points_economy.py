"""Verified Points -> Career XP economy for SAGE career progression.

Points are event-level performance accounting. Career XP is durable progression.
Both require evidence-backed, unique verified events. Point values are explicit,
deterministic, replay-protected, and attached to verification-quality metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable


class PointEventType(str, Enum):
    RECON = "RECON"
    ANALYSIS = "ANALYSIS"
    BUILD = "BUILD"
    REPAIR = "REPAIR"
    VERIFICATION = "VERIFICATION"
    BREAKTHROUGH = "BREAKTHROUGH"
    CAPABILITY_CAPTURE = "CAPABILITY_CAPTURE"
    BOSS_KILL = "BOSS_KILL"
    BOSS_CAPTURE = "BOSS_CAPTURE"
    COLLABORATION = "COLLABORATION"
    REUSE = "REUSE"
    RECOVERY = "RECOVERY"


from sage.experimental.airspace.points_xp_economy import (
    BASE_POINTS as BASE_POINT_VALUES,
    PointEventType,
    PointsXPEconomy,
    VerifiedPointAward as PointAward,
)


def base_points_for(event_type: PointEventType) -> int:
    return BASE_POINT_VALUES[event_type]


class PointsLedger:
    """Append-only point ledger with replay protection and deterministic XP conversion."""

    POINTS_PER_XP = 10

    def __init__(self, awards: Iterable[PointAward] = ()) -> None:
        self._awards: Dict[str, PointAward] = {}
        for award in awards:
            self.record(award)

    def record(self, award: PointAward) -> PointAward:
        existing = self._awards.get(award.verified_event_ref)
        if existing is not None:
            if existing != award:
                raise ValueError("Point award rejected: verified_event_ref already belongs to a different award.")
            return existing
        self._awards[award.verified_event_ref] = award
        return award

    def awards(self) -> tuple[PointAward, ...]:
        return tuple(self._awards.values())

    def verified_points_for_agent(self, agent_id: str) -> int:
        def _match(award: PointAward) -> bool:
            st = getattr(award, "station_id", None)
            st_str = st.value if hasattr(st, "value") else str(st or "")
            ag_str = str(getattr(award, "agent_id", ""))
            target = agent_id.value if hasattr(agent_id, "value") else str(agent_id)
            return st_str == target or ag_str == target

        return sum(a.points for a in self._awards.values() if _match(a))

    def verified_points_total(self) -> int:
        return sum(a.points for a in self._awards.values())

    def career_xp_for_agent(self, agent_id: str) -> int:
        return self.verified_points_for_agent(agent_id) // self.POINTS_PER_XP

    def career_xp_total(self) -> int:
        return self.verified_points_total() // self.POINTS_PER_XP

    def unconverted_points_for_agent(self, agent_id: str) -> int:
        return self.verified_points_for_agent(agent_id) % self.POINTS_PER_XP


__all__ = [
    "PointEventType",
    "BASE_POINT_VALUES",
    "base_points_for",
    "PointAward",
    "PointsLedger",
    "PointsXPEconomy",
]
