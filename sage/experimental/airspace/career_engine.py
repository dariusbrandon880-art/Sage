"""Read-only career reconciliation over canonical SAGE Airspace state.

AirspaceState remains authoritative for XP, qualifications, stations, and evidence.
This module projects those facts into attributable agent career records without
creating a second source of truth or mutating canonical state.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field

from sage.experimental.airspace.models import AirspaceState, StationID


class AgentIdentity(str, Enum):
    """Canonical SAGE execution identities represented by Airspace stations."""

    DIRECTOR = "Human Director"
    CHATGPT = "GPT"
    GEMINI = "Gemini"
    JULES = "Jules"


class CareerProjection(BaseModel):
    """Read-only career-facing projection of canonical station state."""

    agent_id: AgentIdentity
    station_id: StationID
    role_description: str
    career_xp: int = 0
    cql_level: int = 0
    sql_level: int = 0
    evidence_count: int = 0
    qualification_evidence: list[str] = Field(default_factory=list)
    rank: str | None = None


class CareerEngine:
    """Reconcile agent career facts without mutating canonical Airspace state."""

    STATION_AGENT_IDS: Dict[StationID, AgentIdentity] = {
        StationID.MISSION_DIRECTOR: AgentIdentity.DIRECTOR,
        StationID.MISSION_CONTROL: AgentIdentity.CHATGPT,
        StationID.INTEL_STATION: AgentIdentity.GEMINI,
        StationID.ENGINEERING_FLIGHT: AgentIdentity.JULES,
    }

    def project_station(self, state: AirspaceState, station_id: StationID) -> CareerProjection:
        """Project one agent from canonical Airspace progression and qualification state."""
        station = state.stations[station_id]
        agent_id = self.STATION_AGENT_IDS.get(station_id)
        if agent_id is None:
            raise ValueError(f"Unsupported career station: {station_id}")

        return CareerProjection(
            agent_id=agent_id,
            station_id=station_id,
            role_description=station.role_description,
            career_xp=state.game_progression.get_total_xp_for_station(station_id),
            cql_level=state.qualification_registry.cql_levels.get(station_id, station.current_cql),
            sql_level=state.qualification_registry.sql_levels.get(station_id, station.current_sql),
            evidence_count=len(state.recent_evidence),
            qualification_evidence=list(state.recent_evidence),
        )

    def reconcile(self, state: AirspaceState) -> Dict[AgentIdentity, CareerProjection]:
        """Return projections for every canonical SAGE agent currently in Airspace."""
        return {
            agent_id: self.project_station(state, station_id)
            for station_id, agent_id in self.STATION_AGENT_IDS.items()
            if station_id in state.stations
        }
