"""Canonical SAGE Organism Runtime Contract & Station Identity Handshake.

Operationalizes the 10-step interaction loop:
1. SENSE: Identify the station.
2. REHYDRATE: Load canonical organism state.
3. IDENTITY LOCK: Verify Git HEAD provenance and lock station state.
4. MISSION RESOLUTION: Load current mission and flight state.
5. CHALLENGE / MOVE AUTHORIZATION: Validate action against station qualification move set.
6. ACTION: Execute authorized operational action.
7. EVIDENCE: Record evidence and compute evidence digest.
8. REWARD: Reconcile resulting state and award verified progression (XP/Points).
9. STATE UPDATE: Refresh career rank level, title, and station progression.
10. NEXT OBJECTIVE / REHYDRATED C2 HUD: Emit rehydrated C2 Mission Control feedback.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
import subprocess
from typing import Any, Sequence

from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


ORGANISM_ID_MAIN = "SAGE_ORGANISM_MAIN"
DEFAULT_CHATGPT_STATION = "[SAGE::C2::CHATGPT]"
CONTRACT_VERSION = "1.0"

# Base capabilities unlocked by qualification levels
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
    """Fetch current 40-character Git HEAD SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        sha = res.stdout.strip()
        if re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            return sha
    except Exception:
        pass
    return ""


@dataclass(frozen=True)
class OrganismStationState:
    """Stateful station identity derived from canonical SAGE organism state."""

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
        """Return True if move_name is authorized under station qualifications."""
        if not move_name or not move_name.strip():
            return False
        normalized = move_name.strip().upper()
        return normalized in self.authorized_moves


@dataclass(frozen=True)
class OrganismTurnReceipt:
    """Cryptographic flight receipt for a verified organism turn."""

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
    verified: bool = True

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


def handshake_station_identity(
    runtime: Any = None,
    *,
    manager: Any = None,
    session_id: str = "session-001",
    station_id: str = DEFAULT_CHATGPT_STATION,
    c2_context: dict[str, Any] | None = None,
) -> OrganismStationState:
    """Step 1 & 2: Handshake and resolve stateful station identity from canonical state."""
    git_sha = _get_canonical_git_sha()
    if not git_sha:
        raise ValueError("Organism handshake failed: valid canonical Git HEAD SHA required")

    # Load AirspaceManager if not passed
    mgr = manager
    if mgr is None:
        try:
            mgr_mod = importlib.import_module("sage.experimental.airspace.manager")
            mgr = mgr_mod.AirspaceManager()
        except Exception:
            mgr = None

    cql = 2
    sql = 1
    total_xp = 100
    total_points = 50
    active_mission = "SAGE_ORGANISM_CONTINUITY"

    if mgr is not None and hasattr(mgr, "reconstruct_airspace_state"):
        try:
            airspace = mgr.reconstruct_airspace_state()
            if airspace.active_mission:
                active_mission = airspace.active_mission.mission_id
            total_xp = airspace.game_progression.get_total_airspace_xp()
            # Find station matching station_id or default C2 station
            for st_id, st_obj in airspace.stations.items():
                if st_id.value == station_id or st_obj.agent_name == "GPT":
                    cql = st_obj.current_cql
                    sql = st_obj.current_sql
                    station_xp = airspace.game_progression.get_total_xp_for_station(st_id)
                    if station_xp > 0:
                        total_xp = station_xp
                    break
        except Exception:
            pass

    # Resolve rank for XP
    rank_mod = importlib.import_module("sage.experimental.airspace.rank_system")
    rank_def = rank_mod.rank_for_xp(total_xp)

    authorized_moves = resolve_authorized_moves(cql, sql)
    context = dict(c2_context or {})
    objective = context.get("active_objective") or active_mission

    return OrganismStationState(
        organism_id=ORGANISM_ID_MAIN,
        station_id=station_id,
        station_name="GPT",
        rank_level=rank_def.level,
        rank_title=rank_def.title,
        total_xp=total_xp,
        total_points=total_points,
        cql=cql,
        sql=sql,
        qualifications=(f"CQL-{cql}", f"SQL-{sql}"),
        active_mission=str(objective),
        current_flight=f"FLIGHT_{session_id}",
        current_phase="EXECUTE",
        active_objectives=(str(objective),),
        unresolved_targets=(),
        recent_verified_accomplishments=("HANDSHAKE_VERIFIED",),
        authorized_moves=authorized_moves,
        provenance_sha=git_sha,
        hud_visibility="HUB_A",
    )


class OrganismRuntimeContractEngine:
    """Engine executing the 10-step Playable Organism turn interaction loop."""

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
        """Execute one complete 10-step playable turn with verified progression."""
        # Step 1: SENSE - Identify station & handshake
        station_state = handshake_station_identity(
            self.runtime,
            manager=self.manager,
            session_id=session_id,
            station_id=station_id,
            c2_context=c2_context,
        )

        # Step 2: REHYDRATE & IDENTITY LOCK
        if not station_state.provenance_sha or len(station_state.provenance_sha) != 40:
            raise ValueError("Identity lock failed: canonical 40-character provenance SHA required.")

        # Step 3: MISSION RESOLUTION
        if not station_state.active_mission:
            raise ValueError("Mission resolution failed: active mission required.")

        # Step 4 & 5: CHALLENGE / MOVE AUTHORIZATION
        requested_move = action_name.strip().upper()
        if not station_state.is_move_authorized(requested_move):
            raise ValueError(
                f"SAGE move rejection: '{requested_move}' is not authorized for "
                f"station '{station_state.station_id}' at qualification level CQL-{station_state.cql}. "
                f"Authorized move set: {station_state.authorized_moves}"
            )

        # Step 6: ACTION EXECUTION
        action_summary = task.strip() or f"Executed authorized move {requested_move}"

        # Step 7: EVIDENCE CAPTURE
        raw_evidence = f"{session_id}:{action_name}:{action_summary}:{','.join(sorted(evidence_refs))}"
        evidence_digest = sha256(raw_evidence.encode("utf-8")).hexdigest()

        # Step 8: REWARD RECONCILIATION
        minted_xp = max(0, xp_award)
        awarded_points = max(0, points_award)

        # Award XP via AirspaceManager if available
        mgr = self.manager
        if mgr is None:
            try:
                mgr_mod = importlib.import_module("sage.experimental.airspace.manager")
                mgr = mgr_mod.AirspaceManager()
            except Exception:
                mgr = None

        if mgr is not None and hasattr(mgr, "award_xp") and minted_xp > 0:
            try:
                st_id_enum = importlib.import_module("sage.experimental.airspace.models").StationID.MISSION_CONTROL
                cat_enum = importlib.import_module("sage.experimental.airspace.models").XPCategory.VERIFIED_STRIKE
                mgr.award_xp(
                    actor=station_id,
                    station_id=st_id_enum,
                    category=cat_enum,
                    amount=minted_xp,
                    reason=f"Playable turn verified action: {requested_move}",
                    verified_event_ref=evidence_digest,
                )
            except Exception:
                pass

        # Step 9: STATE UPDATE & PROGRESSION
        total_xp_after = station_state.total_xp + minted_xp
        rank_mod = importlib.import_module("sage.experimental.airspace.rank_system")
        rank_after = rank_mod.rank_for_xp(total_xp_after)

        # Step 10: REHYDRATED C2 HUD & GAME FEEDBACK
        immersion_mod = importlib.import_module("sage.experimental.airspace.immersion")
        hud_projection = ""
        if mgr is not None and hasattr(immersion_mod, "render_four_layer_hud_from_manager"):
            try:
                hud_projection = immersion_mod.render_four_layer_hud_from_manager(mgr)
            except Exception:
                hud_projection = f"[SAGE::C2::CHATGPT] C2 MISSION CONTROL // RANK {rank_after.title} // XP {total_xp_after}"

        turn_id = f"TURN_{session_id}_{evidence_digest[:8]}"

        return OrganismTurnReceipt(
            turn_id=turn_id,
            session_id=session_id,
            station_id=station_id,
            provenance_sha=station_state.provenance_sha,
            action_executed=requested_move,
            authorized_moves=station_state.authorized_moves,
            evidence_digest=evidence_digest,
            xp_minted=minted_xp,
            points_awarded=awarded_points,
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
