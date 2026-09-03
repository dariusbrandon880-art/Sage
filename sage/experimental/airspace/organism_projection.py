"""Single read-only organism projection for SAGE career/mission visibility.

The projection joins canonical AirspaceState with derived values reconstructed
from the same append-only AirspaceManager event ledger. It is intentionally a
presentation boundary: it never awards Points/XP, grants badges, changes rank,
or changes qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sage.experimental.airspace.boss_progression import BossProgression, BossProgressionAuthority
from sage.experimental.airspace.models import AirspaceState, StationID
from sage.experimental.airspace.points_xp_economy import PointsXPEconomy


@dataclass(frozen=True)
class OrganismAgentProjection:
    station_id: StationID
    agent_name: str
    role: str
    cql: int
    sql: int
    points: int
    career_xp: int
    boss: BossProgression
    status: str

    @property
    def badge_summary(self) -> str:
        return self.boss.badge_summary


class OrganismProjection:
    """Reconcile every participating SAGE agent from canonical state + ledger."""

    @staticmethod
    def project_station(
        manager, state: AirspaceState, station_id: StationID, *, status: str = "READY"
    ) -> OrganismAgentProjection:
        station = state.stations[station_id]
        return OrganismAgentProjection(
            station_id=station_id,
            agent_name=station.agent_name,
            role=station.role_description,
            cql=station.current_cql,
            sql=station.current_sql,
            points=PointsXPEconomy._historical_points(manager, station_id),
            career_xp=state.game_progression.get_total_xp_for_station(station_id),
            boss=BossProgressionAuthority.project_station(manager, station_id),
            status=status,
        )

    @classmethod
    def reconcile(
        cls, manager, state: AirspaceState, *, status: str = "READY"
    ) -> Mapping[StationID, OrganismAgentProjection]:
        return {
            station_id: cls.project_station(manager, state, station_id, status=status)
            for station_id in state.stations
        }

    @staticmethod
    def render_agent_tag(agent: OrganismAgentProjection) -> str:
        """Compact organism-wide tag; all values are read-only canonical projections."""
        sql = f" // SQL-{agent.sql}" if agent.sql > 0 else ""
        boss = agent.boss
        return (
            f"{agent.agent_name} // CQL-{agent.cql}{sql} // "
            f"POINTS {agent.points} // XP {agent.career_xp} // "
            f"BOSS ⭐×{boss.big_badges} ⭐⭐×{boss.major_badges} // "
            f"⚔️ {boss.total_kills} // ┃ {boss.total_captures} // {agent.status}"
        )

    @classmethod
    def render_roster(cls, manager, state: AirspaceState, *, status: str = "READY") -> str:
        projections = cls.reconcile(manager, state, status=status)
        lines = ["SAGE ORGANISM // AGENT PROJECTION", "━" * 64]
        lines.extend(cls.render_agent_tag(agent) for agent in projections.values())
        return "\n".join(lines)
