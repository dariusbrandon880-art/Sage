"""Canonical SAGE Organism Runtime Contract & Station Identity Handshake.

Operationalizes the 10-step interaction loop:
1. SENSE: Identify the station.
2. REHYDRATE: Load canonical organism state.
3. IDENTITY LOCK: Verify governed Git provenance and lock station state.
4. MISSION RESOLUTION: Load current mission and flight state.
5. CHALLENGE / MOVE AUTHORIZATION: Validate action against station qualification move set.
6. ACTION: Record the authorized operational action.
7. EVIDENCE: Persist evidence and compute evidence digest.
8. REWARD: Persist verified progression (XP/Points).
9. STATE UPDATE: Reconstruct post-settlement canonical progression.
10. NEXT OBJECTIVE / REHYDRATED C2 HUD: Emit the canonical Hub projection.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from hashlib import sha256
import os
import re
from typing import Any, Sequence

from sage.c2.immersion_state import ImmersionState


ORGANISM_ID_MAIN = "SAGE_ORGANISM_MAIN"
DEFAULT_CHATGPT_STATION = "MISSION_CONTROL"
CONTRACT_VERSION = "1.0"

CQL_MOVE_SETS: dict[int, tuple[str, ...]] = {
    0: ("RECON", "HUD_PROJECTION", "ANALYZE"),
    1: ("RECON", "HUD_PROJECTION", "ANALYZE", "DELEGATION", "STRIKE_FEED"),
    2: ("RECON", "HUD_PROJECTION", "ANALYZE", "DELEGATION", "STRIKE_FEED", "VERIFY", "MISSION_CONTROL", "HANDSHAKE"),
    3: ("RECON", "HUD_PROJECTION", "ANALYZE", "DELEGATION", "STRIKE_FEED", "VERIFY", "MISSION_CONTROL", "HANDSHAKE", "EXECUTE_ACTION", "ADJUDICATE_PROGRESSION", "FULL_OPERATIONAL"),
}


def resolve_authorized_moves(cql: int, sql: int = 0) -> tuple[str, ...]:
    """Resolve authorized operational move set from station qualification levels."""
    level = max(0, min(3, cql))
    base_moves = list(CQL_MOVE_SETS[level])
    if sql > 0:
        base_moves.append("MULTI_STATION_COORDINATION")
    if sql >= 2:
        base_moves.append("FRONTIER_DISPATCH")
    return tuple(dict.fromkeys(base_moves))


def _get_canonical_git_sha() -> str:
    """Return explicitly governed repository provenance; never invent it from local HEAD."""
    for key in ("SAGE_CANONICAL_GIT_SHA", "GITHUB_SHA"):
        sha = os.environ.get(key, "").strip()
        if re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            return sha
    raise ValueError(
        "Organism identity lock failed: governed SAGE_CANONICAL_GIT_SHA or GITHUB_SHA is required."
    )


@dataclass(frozen=True)
class OrganismStationState:
    """Stateful station identity derived only from reconstructed canonical state."""

    organism_id: str
    station_id: str
    station_name: str
    rank_level: int
    rank_title: str
    total_xp: int
    total_points: int
    cql: int
    sql: int
    qualifications: tuple[str, ...]
    active_mission: str
    current_flight: str
    current_phase: str
    active_objectives: tuple[str, ...]
    unresolved_targets: tuple[str, ...]
    recent_verified_accomplishments: tuple[str, ...]
    authorized_moves: tuple[str, ...]
    provenance_sha: str
    hud_visibility: str = "HUB_A"

    def is_move_authorized(self, move_name: str) -> bool:
        if not move_name or not move_name.strip():
            return False
        return move_name.strip().upper() in self.authorized_moves


@dataclass(frozen=True)
class OrganismTurnReceipt:
    """Cryptographic flight receipt for a fully reconciled organism turn."""

    turn_id: str
    session_id: str
    station_id: str
    provenance_sha: str
    action_executed: str
    authorized_moves: tuple[str, ...]
    evidence_digest: str
    xp_minted: int
    points_awarded: int
    rank_level_before: int
    rank_level_after: int
    rank_title_after: str
    total_xp_after: int
    hud_projection: str
    verified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "station_id": self.station_id,
            "provenance_sha": self.provenance_sha,
            "action_executed": self.action_executed,
            "authorized_moves": list(self.authorized_moves),
            "evidence_digest": self.evidence_digest,
            "xp_minted": self.xp_minted,
            "points_awarded": self.points_awarded,
            "rank_level_before": self.rank_level_before,
            "rank_level_after": self.rank_level_after,
            "rank_title_after": self.rank_title_after,
            "total_xp_after": self.total_xp_after,
            "hud_projection": self.hud_projection,
            "verified": self.verified,
        }


def _station_enum(station_id: str) -> Any:
    models_mod = importlib.import_module("sage.experimental.airspace.models")
    try:
        return models_mod.StationID(station_id)
    except ValueError as exc:
        raise ValueError(f"Unknown canonical SAGE station: {station_id}") from exc


def handshake_station_identity(
    runtime: Any = None,
    *,
    manager: Any = None,
    session_id: str = "session-001",
    station_id: str = DEFAULT_CHATGPT_STATION,
    c2_context: dict[str, Any] | None = None,
) -> OrganismStationState:
    """Sense + rehydrate + identity-lock against reconstructed canonical state."""
    git_sha = _get_canonical_git_sha()
    mgr = manager
    if mgr is None:
        mgr_mod = importlib.import_module("sage.experimental.airspace.manager")
        mgr = mgr_mod.AirspaceManager()

    airspace = mgr.reconstruct_airspace_state()
    station_enum = _station_enum(station_id)
    station = airspace.stations.get(station_enum)
    if station is None or not station.active_status:
        raise ValueError(f"Canonical station state unavailable or inactive: {station_id}")

    rank_mod = importlib.import_module("sage.experimental.airspace.rank_system")
    station_xp = airspace.game_progression.get_total_xp_for_station(station_enum)
    rank_def = rank_mod.rank_for_xp(station_xp)
    active_mission = airspace.active_mission
    objective = (c2_context or {}).get("active_objective")
    if active_mission is not None:
        objective = objective or active_mission.mission_id
    if not objective:
        raise ValueError("Mission resolution failed: canonical active mission required.")

    authorized_moves = resolve_authorized_moves(station.current_cql, station.current_sql)
    return OrganismStationState(
        organism_id=ORGANISM_ID_MAIN,
        station_id=station_enum.value,
        station_name=station.agent_name,
        rank_level=rank_def.level,
        rank_title=rank_def.title,
        total_xp=station_xp,
        total_points=0,
        cql=station.current_cql,
        sql=station.current_sql,
        qualifications=(f"CQL-{station.current_cql}", f"SQL-{station.current_sql}"),
        active_mission=str(objective),
        current_flight=f"FLIGHT_{session_id}",
        current_phase="EXECUTE",
        active_objectives=(str(objective),),
        unresolved_targets=tuple(airspace.current_frontiers),
        recent_verified_accomplishments=tuple(airspace.recent_evidence[-10:]),
        authorized_moves=authorized_moves,
        provenance_sha=git_sha,
        hud_visibility="HUB_A",
    )


class OrganismRuntimeContractEngine:
    """Engine executing the governed 10-step Playable Organism turn interaction loop."""

    def __init__(self, runtime: Any = None, manager: Any = None) -> None:
        self.runtime = runtime
        self.manager = manager

    def execute_turn(
        self,
        *,
        session_id: str,
        action_name: str,
        task: str = "",
        evidence_refs: Sequence[str] = (),
        station_id: str = DEFAULT_CHATGPT_STATION,
        c2_context: dict[str, Any] | None = None,
        xp_award: int = 50,
        points_award: int = 25,
    ) -> OrganismTurnReceipt:
        """Execute one turn; verification is earned only after durable reconciliation."""
        if xp_award <= 0 or points_award <= 0:
            raise ValueError("Reward reconciliation requires positive XP and Points awards.")
        if not evidence_refs:
            raise ValueError("Evidence capture requires at least one evidence reference.")

        station_state = handshake_station_identity(
            self.runtime,
            manager=self.manager,
            session_id=session_id,
            station_id=station_id,
            c2_context=c2_context,
        )
        if len(station_state.provenance_sha) != 40:
            raise ValueError("Identity lock failed: canonical 40-character provenance SHA required.")
        requested_move = action_name.strip().upper()
        if not station_state.is_move_authorized(requested_move):
            raise ValueError(
                f"SAGE move rejection: '{requested_move}' is not authorized for station "
                f"'{station_state.station_id}' at qualification level CQL-{station_state.cql}. "
                f"Authorized move set: {station_state.authorized_moves}"
            )

        mgr = self.manager
        if mgr is None:
            mgr_mod = importlib.import_module("sage.experimental.airspace.manager")
            mgr = mgr_mod.AirspaceManager()

        action_summary = task.strip() or f"Executed authorized move {requested_move}"
        raw_evidence = f"{session_id}:{station_state.station_id}:{requested_move}:{action_summary}:{','.join(sorted(evidence_refs))}"
        evidence_digest = sha256(raw_evidence.encode("utf-8")).hexdigest()

        # Step 6: persist the authorized action before any reward is minted.
        action_event = mgr.record_event(
            event_type="ORGANISM_ACTION_EXECUTED",
            actor=station_state.station_id,
            mission_id=station_state.active_mission,
            payload={
                "turn_session_id": session_id,
                "action": requested_move,
                "summary": action_summary,
                "provenance_sha": station_state.provenance_sha,
            },
            evidence_refs=list(evidence_refs),
        )

        # Step 7: persist the evidence digest as governed evidence.
        evidence_event = mgr.record_event(
            event_type="ORGANISM_EVIDENCE_CAPTURED",
            actor=station_state.station_id,
            mission_id=station_state.active_mission,
            payload={
                "turn_session_id": session_id,
                "action_event_id": action_event.event_id,
                "evidence_digest": evidence_digest,
            },
            evidence_refs=list(evidence_refs),
        )

        # Step 8: persist both progression awards against the evidence event.
        models_mod = importlib.import_module("sage.experimental.airspace.models")
        mgr.award_xp(
            actor=station_state.station_id,
            station_id=_station_enum(station_state.station_id),
            category=models_mod.XPCategory.VERIFIED_STRIKE,
            amount=xp_award,
            reason=f"Playable turn verified action: {requested_move}",
            verified_event_ref=evidence_event.event_id,
        )
        mgr.record_event(
            event_type="POINTS_AWARDED",
            actor=station_state.station_id,
            mission_id=station_state.active_mission,
            payload={
                "station_id": station_state.station_id,
                "amount": points_award,
                "action": requested_move,
                "verified_event_ref": evidence_event.event_id,
                "evidence_digest": evidence_digest,
            },
            evidence_refs=[evidence_event.event_id, *evidence_refs],
        )

        # Step 9: reconstruct after settlement; never arithmetic-guess post-state.
        post_state = mgr.reconstruct_airspace_state()
        station_enum = _station_enum(station_state.station_id)
        total_xp_after = post_state.game_progression.get_total_xp_for_station(station_enum)
        rank_mod = importlib.import_module("sage.experimental.airspace.rank_system")
        rank_after = rank_mod.rank_for_xp(total_xp_after)

        # Step 10: render only the canonical Hub; any rendering failure invalidates verification.
        immersion_mod = importlib.import_module("sage.experimental.airspace.immersion")
        hud_projection = immersion_mod.render_hub_a_from_manager(mgr)
        if not hud_projection.strip():
            raise ValueError("Canonical Hub projection failed: empty projection.")

        turn_id = f"TURN_{session_id}_{evidence_digest[:8]}"
        return OrganismTurnReceipt(
            turn_id=turn_id,
            session_id=session_id,
            station_id=station_state.station_id,
            provenance_sha=station_state.provenance_sha,
            action_executed=requested_move,
            authorized_moves=station_state.authorized_moves,
            evidence_digest=evidence_digest,
            xp_minted=xp_award,
            points_awarded=points_award,
            rank_level_before=station_state.rank_level,
            rank_level_after=rank_after.level,
            rank_title_after=rank_after.title,
            total_xp_after=total_xp_after,
            hud_projection=hud_projection,
            verified=True,
        )


__all__ = [
    "CQL_MOVE_SETS",
    "DEFAULT_CHATGPT_STATION",
    "ORGANISM_ID_MAIN",
    "OrganismRuntimeContractEngine",
    "OrganismStationState",
    "OrganismTurnReceipt",
    "handshake_station_identity",
    "resolve_authorized_moves",
]
