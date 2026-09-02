"""Career projection over the canonical Airspace progression substrate.

The career engine is intentionally an adapter, not a second event authority.  The
canonical event/state seams remain ``AirspaceManager`` + ``AirspaceState``:
missions/sorties/evidence are persisted as Airspace events, qualifications live in
``QualificationRegistry``, and verified XP lives in ``GameProgression``.

This module reconciles those existing facts into a durable career-facing view. It
does not award XP, mutate qualification levels, or promote ranks.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

from sage.experimental.airspace.models import AirspaceState, StationID


class CareerRank(str, Enum):
    CADET = "Cadet"
    FLIGHT_CAPTAIN = "Flight Captain"
    SQUADRON_LEADER = "Squadron Leader"
    FLEET_COMMANDER = "Fleet Commander"


class CareerProjection(BaseModel):
    """Read-only career state reconciled from canonical Airspace state."""

    agent_id: str
    rank: CareerRank = CareerRank.CADET
    career_xp: int = 0
    cql_level: int = 0
    sql_level: int = 0
    evidence_count: int = 0
    promotion_eligible: bool = False
    qualification_evidence: list[str] = Field(default_factory=list)


class CareerEngine:
    """Reconcile career state without creating a parallel source of truth."""

    RANK_XP_REQUIREMENTS: Dict[CareerRank, int] = {
        CareerRank.CADET: 0,
        CareerRank.FLIGHT_CAPTAIN: 100,
        CareerRank.SQUADRON_LEADER: 500,
        CareerRank.FLEET_COMMANDER: 1000,
    }

    RANK_QUALIFICATION_REQUIREMENTS: Dict[CareerRank, tuple[int, int]] = {
        CareerRank.FLIGHT_CAPTAIN: (2, 0),
        CareerRank.SQUADRON_LEADER: (3, 1),
        CareerRank.FLEET_COMMANDER: (4, 2),
    }

    STATION_AGENT_IDS = {
        StationID.MISSION_DIRECTOR: "Human Director",
        StationID.MISSION_CONTROL: "GPT",
        StationID.INTEL_STATION: "Gemini",
        StationID.ENGINEERING_FLIGHT: "Jules",
    }

    def project_station(
        self,
        state: AirspaceState,
        station_id: StationID,
        *,
        current_rank: CareerRank = CareerRank.CADET,
    ) -> CareerProjection:
        """Project one station's career state from canonical progression/qualification data."""
        station = state.stations[station_id]
        agent_id = self.STATION_AGENT_IDS.get(station_id, station.agent_name)
        xp = state.game_progression.get_total_xp_for_station(station_id)
        cql = state.qualification_registry.cql_levels.get(station_id, station.current_cql)
        sql = state.qualification_registry.sql_levels.get(station_id, station.current_sql)

        next_rank: Optional[CareerRank] = None
        ordered = list(CareerRank)
        try:
            idx = ordered.index(current_rank)
            if idx + 1 < len(ordered):
                next_rank = ordered[idx + 1]
        except ValueError:
            next_rank = CareerRank.FLIGHT_CAPTAIN

        eligible = False
        if next_rank is not None:
            required_xp = self.RANK_XP_REQUIREMENTS[next_rank]
            required_cql, required_sql = self.RANK_QUALIFICATION_REQUIREMENTS[next_rank]
            eligible = xp >= required_xp and cql >= required_cql and sql >= required_sql

        evidence = list(state.recent_evidence)
        return CareerProjection(
            agent_id=agent_id,
            rank=current_rank,
            career_xp=xp,
            cql_level=cql,
            sql_level=sql,
            evidence_count=len(evidence),
            promotion_eligible=eligible,
            qualification_evidence=evidence,
        )

    def reconcile(self, state: AirspaceState) -> Dict[str, CareerProjection]:
        """Return career projections for all canonical Airspace stations."""
        return {
            self.STATION_AGENT_IDS[station_id]: self.project_station(state, station_id)
            for station_id in StationID
            if station_id in state.stations
        }
