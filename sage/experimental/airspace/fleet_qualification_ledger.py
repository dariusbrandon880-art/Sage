"""Governed fleet qualification and persistent agent career progression.

This subsystem turns the existing verified-evidence/qualification substrate into a
persistent career engine. Mission Points are immediate performance accounting;
Career XP is durable progression and can only be minted from verified Points.

The module remains in ``experimental`` until its integration and promotion gates
are proven by the repository's validation workflows. Presentation layers must
consume the resulting state read-only.
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CareerRank(str, Enum):
    CADET = "Cadet"
    FLIGHT_CAPTAIN = "Flight Captain"
    SQUADRON_LEADER = "Squadron Leader"
    FLEET_COMMANDER = "Fleet Commander"


class CareerPointEvent(BaseModel):
    """Verified mission-performance points; not yet career XP."""

    event_id: str
    agent_id: str
    points: int
    base_points: int
    verification_quality: float = Field(ge=0.0, le=2.0)
    difficulty: float = Field(ge=0.0, le=2.0)
    impact: float = Field(ge=0.0, le=2.0)
    reuse: float = Field(ge=0.0, le=2.0)
    verified_event_ref: str
    evidence_refs: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class CareerPromotionEvent(BaseModel):
    """Durable promotion decision with explicit qualification evidence."""

    event_id: str
    agent_id: str
    previous_rank: CareerRank
    new_rank: CareerRank
    career_xp: int
    required_xp: int
    cql_level: int
    sql_level: int
    evidence_refs: List[str] = Field(default_factory=list)
    reason: str
    timestamp: float = Field(default_factory=time.time)


class FleetRankState(BaseModel):
    """Canonical career snapshot for one SAGE agent."""

    agent_id: str
    rank_title: str = CareerRank.CADET.value
    total_xp: int = 0
    verified_points: int = 0
    cql_qualified: bool = False
    sql_qualified: bool = False
    cql_level: int = 0
    sql_level: int = 0
    verification_badges: List[str] = Field(default_factory=list)
    promotion_eligible: bool = False
    last_promotion_reason: Optional[str] = None
    last_updated: float = Field(default_factory=time.time)


class FleetQualificationLedger:
    """Append-only career ledger with governed promotion evaluation.

    The XP economy is deliberately conservative: 10 verified Points mint 1
    Career XP. Points are deduplicated by verified-event reference, while the
    promotion engine requires both progression and demonstrated qualification.
    """

    POINTS_PER_XP = 10

    # These are policy defaults, not authority. Promotion still requires the
    # qualification/evidence gates below and the policy can evolve later.
    RANK_XP_REQUIREMENTS = {
        CareerRank.CADET: 0,
        CareerRank.FLIGHT_CAPTAIN: 100,
        CareerRank.SQUADRON_LEADER: 500,
        CareerRank.FLEET_COMMANDER: 1000,
    }

    RANK_QUALIFICATION_REQUIREMENTS = {
        CareerRank.FLIGHT_CAPTAIN: (2, 0),
        CareerRank.SQUADRON_LEADER: (3, 1),
        CareerRank.FLEET_COMMANDER: (4, 2),
    }

    def __init__(self):
        self._states: Dict[str, FleetRankState] = {}
        self._point_events: List[CareerPointEvent] = []
        self._promotion_events: List[CareerPromotionEvent] = []

    def get_or_create_state(self, agent_id: str) -> FleetRankState:
        """Retrieves or initializes persistent career state for an agent."""
        if not agent_id:
            raise ValueError("Agent career state requires a non-empty agent_id.")
        if agent_id not in self._states:
            self._states[agent_id] = FleetRankState(agent_id=agent_id)
        return self._states[agent_id]

    def record_verified_points(
        self,
        agent_id: str,
        base_points: int,
        *,
        verification_quality: float = 1.0,
        difficulty: float = 1.0,
        impact: float = 1.0,
        reuse: float = 1.0,
        verified_event_ref: str,
        evidence_refs: Optional[List[str]] = None,
        badge: Optional[str] = None,
    ) -> CareerPointEvent:
        """Record verified performance points and mint no XP outside the ledger."""
        if base_points <= 0:
            raise ValueError("Verified points must be positive.")
        if not verified_event_ref or not verified_event_ref.strip():
            raise ValueError("Verified points require a verified_event_ref.")
        if any(e.verified_event_ref == verified_event_ref for e in self._point_events):
            raise ValueError("Duplicate verified_event_ref rejected; points cannot be farmed by replay.")
        refs = list(evidence_refs or [])
        if not refs:
            raise ValueError("Verified points require at least one evidence reference.")

        multiplier = verification_quality * difficulty * impact * reuse
        points = max(1, int(round(base_points * multiplier)))
        state = self.get_or_create_state(agent_id)
        state.verified_points += points
        if badge and badge not in state.verification_badges:
            state.verification_badges.append(badge)
        state.last_updated = time.time()

        event = CareerPointEvent(
            event_id=f"pts_{hashlib.sha256(f'{agent_id}:{verified_event_ref}'.encode()).hexdigest()[:12]}",
            agent_id=agent_id,
            points=points,
            base_points=base_points,
            verification_quality=verification_quality,
            difficulty=difficulty,
            impact=impact,
            reuse=reuse,
            verified_event_ref=verified_event_ref,
            evidence_refs=refs,
        )
        self._point_events.append(event)
        return event

    def convert_points_to_xp(self, agent_id: str) -> int:
        """Convert only the unconverted verified-point balance into Career XP."""
        state = self.get_or_create_state(agent_id)
        earned_xp = state.verified_points // self.POINTS_PER_XP
        already_accounted = state.total_xp
        delta = max(0, earned_xp - already_accounted)
        if delta:
            state.total_xp += delta
            state.last_updated = time.time()
        return delta

    def evaluate_promotion(
        self,
        agent_id: str,
        *,
        cql_level: int,
        sql_level: int,
        evidence_refs: Optional[List[str]] = None,
        reason: str = "Verified career progression",
    ) -> FleetRankState:
        """Evaluate promotion eligibility; never promote on XP alone."""
        state = self.get_or_create_state(agent_id)
        state.cql_level = max(state.cql_level, cql_level)
        state.sql_level = max(state.sql_level, sql_level)
        state.cql_qualified = state.cql_level > 0
        state.sql_qualified = state.sql_level > 0
        refs = list(evidence_refs or [])

        current = CareerRank(state.rank_title)
        ordered = list(CareerRank)
        next_rank = ordered[min(ordered.index(current) + 1, len(ordered) - 1)]
        if next_rank == current:
            state.promotion_eligible = False
            return state

        required_xp = self.RANK_XP_REQUIREMENTS[next_rank]
        req_cql, req_sql = self.RANK_QUALIFICATION_REQUIREMENTS[next_rank]
        state.promotion_eligible = (
            state.total_xp >= required_xp
            and state.cql_level >= req_cql
            and state.sql_level >= req_sql
            and bool(refs)
        )

        if state.promotion_eligible:
            previous = current
            state.rank_title = next_rank.value
            state.last_promotion_reason = reason
            state.promotion_eligible = False
            event = CareerPromotionEvent(
                event_id=f"promo_{hashlib.sha256(f'{agent_id}:{next_rank.value}:{state.total_xp}:{len(self._promotion_events)}'.encode()).hexdigest()[:12]}",
                agent_id=agent_id,
                previous_rank=previous,
                new_rank=next_rank,
                career_xp=state.total_xp,
                required_xp=required_xp,
                cql_level=state.cql_level,
                sql_level=state.sql_level,
                evidence_refs=refs,
                reason=reason,
            )
            self._promotion_events.append(event)
            state.last_updated = time.time()
        return state

    def record_xp_event(self, agent_id: str, xp_gained: int, badge: Optional[str] = None) -> FleetRankState:
        """Compatibility path: retain legacy callers but do not bypass verification.

        Legacy direct-XP callers are intentionally rejected unless the caller
        supplies a verified-point event through ``record_verified_points``.
        """
        raise ValueError(
            "Direct XP awards are retired. Record verified Points, convert them to Career XP, "
            "then evaluate governed promotion."
        )

    def export_snapshot(self) -> str:
        """Exports career state plus immutable point/promotion history."""
        snapshot_data = {
            "timestamp": time.time(),
            "economy": {"points_per_xp": self.POINTS_PER_XP},
            "agents": {agent_id: state.model_dump() for agent_id, state in self._states.items()},
            "point_events": [event.model_dump() for event in self._point_events],
            "promotion_events": [event.model_dump() for event in self._promotion_events],
        }
        return json.dumps(snapshot_data, indent=2)

    def recover_from_snapshot(self, snapshot_json: str) -> int:
        """Restores career state and event history from a persisted snapshot."""
        data = json.loads(snapshot_json)
        self._states.clear()
        self._point_events.clear()
        self._promotion_events.clear()
        for agent_id, agent_dict in data.get("agents", {}).items():
            self._states[agent_id] = FleetRankState(**agent_dict)
        self._point_events = [CareerPointEvent(**item) for item in data.get("point_events", [])]
        self._promotion_events = [CareerPromotionEvent(**item) for item in data.get("promotion_events", [])]
        return len(self._states)

    def get_promotion_history(self) -> List[CareerPromotionEvent]:
        return list(self._promotion_events)
