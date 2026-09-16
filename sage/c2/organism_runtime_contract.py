"""SAGE Organism Stateful Station Identity & Playable Turn Contract Engine.

Operationalizes the complete 10-step playable organism interaction loop:
SENSE -> REHYDRATE -> IDENTITY LOCK -> MISSION RESOLUTION -> MOVE AUTHORIZATION ->
ACTION -> EVIDENCE -> REWARD -> STATE UPDATE -> REHYDRATED HUD.

All transitions are real, persisted, evidence-backed, and rehydratable across sessions.
Obeys the SAGE One-Way Import Law by dynamically resolving experimental airspace packages.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from sage.c2.agent_identity import AgentBoundaryIdentity, CHATGPT_AGENT_NAMEPLATE, JULES_AGENT_NAMEPLATE
from sage.c2.hub_presentation_boundary import HubSurface


ORGANISM_ID_MAIN = "SAGE_ORGANISM_MAIN"
DEFAULT_CHATGPT_STATION = "[SAGE::C2::CHATGPT]"
CONTRACT_VERSION = "1.0"

_STATION_MAP = {
    "[SAGE::C2::CHATGPT]": "MISSION_CONTROL",
    "[SAGE::ENGINEER::JULES]": "ENGINEERING_FLIGHT",
    "[SAGE::INTEL::GEMINI]": "INTEL_STATION",
    "[SAGE::DIRECTOR]": "MISSION_DIRECTOR",
    "MISSION_CONTROL": "MISSION_CONTROL",
    "ENGINEERING_FLIGHT": "ENGINEERING_FLIGHT",
    "INTEL_STATION": "INTEL_STATION",
    "MISSION_DIRECTOR": "MISSION_DIRECTOR",
}


def resolve_station_enum(station_id_str: str) -> Any:
    """Resolve a station enum from either nameplate string or StationID enum string."""
    models_mod = importlib.import_module("sage.experimental.airspace.models")
    StationID = models_mod.StationID
    canonical_key = _STATION_MAP.get(str(station_id_str).strip())
    if not canonical_key:
        try:
            return StationID(str(station_id_str).strip())
        except ValueError as exc:
            raise ValueError(f"Unknown or unverified station_id: '{station_id_str}'") from exc
    return StationID(canonical_key)


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
    evidence_refs: tuple[str, ...]
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
            "evidence_refs": list(self.evidence_refs),
            "xp_minted": self.xp_minted,
            "points_awarded": self.points_awarded,
            "rank_level_before": self.rank_level_before,
            "rank_level_after": self.rank_level_after,
            "rank_title_after": self.rank_title_after,
            "total_xp_after": self.total_xp_after,
            "hud_projection": self.hud_projection,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class PlayableTurnResult:
    """Immutable result of executing a complete playable organism turn."""

    turn_id: str
    sequence_number: int
    station_id: str
    agent_name: str
    action_name: str
    verified: bool
    points_awarded: int
    xp_minted: int
    rank_level: int
    rank_title: str
    evidence_digest: str
    git_head_sha: str
    rehydrated_hud: str
    turn_resolution: Any
    rehydrated_state: Any


def handshake_station_identity(
    runtime: Any = None,
    *,
    manager: Any = None,
    session_id: str = "session-001",
    station_id: str = DEFAULT_CHATGPT_STATION,
    c2_context: dict[str, Any] | None = None,
) -> OrganismStationState:
    """Step 1 & 2: Handshake and resolve stateful station identity from canonical state."""
    st_enum = resolve_station_enum(station_id)

    # Strict Git HEAD resolution
    engine = OrganismRuntimeContractEngine()
    git_sha = engine.sense_environment()["git_head_sha"]

    mgr = manager
    if mgr is None:
        mgr_cls = importlib.import_module("sage.experimental.airspace.manager").AirspaceManager
        mgr = mgr_cls()

    airspace = mgr.reconstruct_airspace_state()
    if st_enum not in airspace.stations:
        raise KeyError(f"Station '{st_enum.value}' is not registered in Airspace state.")

    station_obj = airspace.stations[st_enum]
    cql = station_obj.current_cql
    sql = station_obj.current_sql
    total_xp = airspace.game_progression.get_total_xp_for_station(st_enum)
    total_points = airspace.game_progression.get_total_airspace_xp()

    active_mission = airspace.active_mission.mission_id if airspace.active_mission else "SAGE_ORGANISM_CONTINUITY"

    rank_mod = importlib.import_module("sage.experimental.airspace.rank_system")
    rank_def = rank_mod.rank_for_xp(total_xp)

    authorized_moves = resolve_authorized_moves(cql, sql)
    context = dict(c2_context or {})
    objective = context.get("active_objective") or active_mission

    return OrganismStationState(
        organism_id=ORGANISM_ID_MAIN,
        station_id=station_id,
        station_name=station_obj.agent_name,
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
    """Orchestrates the 10-step persistent playable organism interaction loop."""

    def __init__(self, runtime: Any = None, manager: Any = None, ledger_path: Optional[str | Path] = None):
        self.runtime = runtime
        self.manager = manager
        self.ledger_path = Path(ledger_path or "evidence_capture/airspace_ledger.json")

    # Dynamic imports for One-Way Import Law compliance
    @staticmethod
    def _get_airspace_manager_cls() -> Any:
        mod = importlib.import_module("sage.experimental.airspace.manager")
        return mod.AirspaceManager

    @staticmethod
    def _get_models_mod() -> Any:
        return importlib.import_module("sage.experimental.airspace.models")

    @staticmethod
    def _get_turn_engine_mod() -> Any:
        return importlib.import_module("sage.experimental.airspace.turn_engine")

    @staticmethod
    def _get_projection_mod() -> Any:
        return importlib.import_module("sage.experimental.airspace.organism_projection")

    @staticmethod
    def _get_rank_system_mod() -> Any:
        return importlib.import_module("sage.experimental.airspace.rank_system")

    @staticmethod
    def _get_points_xp_mod() -> Any:
        return importlib.import_module("sage.experimental.airspace.points_xp_economy")

    # STAGE 1: SENSE
    def sense_environment(self, exact_git_head: Optional[str] = None) -> Dict[str, Any]:
        """Senses active environment state and validates canonical Git HEAD SHA."""
        if exact_git_head:
            sha = exact_git_head.strip()
        else:
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
                )
                sha = res.stdout.strip()
            except Exception as exc:
                raise RuntimeError("Failed to resolve canonical Git HEAD SHA") from exc

        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError(f"Invalid git HEAD commit SHA: '{sha}'")

        return {
            "git_head_sha": sha,
            "timestamp": time.time(),
            "ledger_path": str(self.ledger_path),
        }

    # STAGE 2: REHYDRATE
    def get_manager(self) -> Any:
        if self.manager is not None:
            return self.manager
        manager_cls = self._get_airspace_manager_cls()
        return manager_cls(self.ledger_path)

    def rehydrate_state(self) -> Any:
        """Reconstructs current AirspaceState from historical event ledger."""
        mgr = self.get_manager()
        return mgr.reconstruct_airspace_state()

    # STAGE 3: IDENTITY LOCK
    def lock_identity(self, station_id_str: str, session_id: str) -> Tuple[Any, AgentBoundaryIdentity]:
        """Locks station identity and verifies boundary identity provenance."""
        st_enum = resolve_station_enum(station_id_str)

        state = self.rehydrate_state()
        if st_enum not in state.stations:
            raise KeyError(f"Station '{st_enum.value}' is not registered in Airspace state.")

        station = state.stations[st_enum]
        if not station.active_status:
            raise PermissionError(f"Station '{st_enum.value}' is inactive.")

        nameplate = JULES_AGENT_NAMEPLATE if st_enum.value == "ENGINEERING_FLIGHT" else CHATGPT_AGENT_NAMEPLATE
        identity = AgentBoundaryIdentity(
            agent=station.agent_name,
            session_id=session_id,
            nameplate=nameplate,
        )
        return station, identity

    # STAGE 4: MISSION RESOLUTION
    def resolve_mission(
        self,
        manager: Any,
        mission_id: str = "MISSION-PLAYABLE-001",
        objective: str = "Execute persistent playable organism turns",
        target: str = "AIRSPACE_C2",
    ) -> Tuple[Any, Any]:
        """Resolves active mission and active sortie, creating baseline entities if missing."""
        models = self._get_models_mod()
        state = manager.reconstruct_airspace_state()

        mission = state.active_mission
        if mission is None or mission.mission_id != mission_id:
            mission = models.Mission(
                mission_id=mission_id,
                mission_name=f"Playable Mission {mission_id}",
                theater="Airspace/C2",
                priority="P0",
                objective=objective,
                authorized_scope=["Airspace", "C2", "Progression"],
                assigned_stations=list(models.StationID),
                status="ACTIVE",
                evidence_requirements=[f"evidence/{mission_id}.json"],
                current_frontier=target,
            )
            manager.create_mission(actor="MISSION_CONTROL", mission=mission)

        sortie_id = f"sortie_{mission_id}_{hashlib.sha256(target.encode('utf-8')).hexdigest()[:8]}"
        sortie = next((s for s in state.active_sorties if s.sortie_id == sortie_id), None)
        if sortie is None:
            sortie = models.Sortie(
                sortie_id=sortie_id,
                mission_id=mission_id,
                station=models.StationID.ENGINEERING_FLIGHT,
                objective=objective,
                target=target,
                status=models.SortieState.CREATED,
            )
            manager.create_sortie(actor="MISSION_CONTROL", sortie=sortie)

        return mission, sortie

    # STAGE 5: MOVE AUTHORIZATION
    def authorize_move(
        self,
        station_id_str: str,
        action_name: str,
        required_cql: int = 1,
        required_sql: int = 0,
    ) -> bool:
        """Evaluates CQL/SQL qualification requirements for station move authorization."""
        st_enum = resolve_station_enum(station_id_str)

        state = self.rehydrate_state()
        reg = state.qualification_registry

        station_cql = reg.cql_levels.get(st_enum, 0)
        station_sql = reg.sql_levels.get(st_enum, 0)

        if station_cql < required_cql:
            raise PermissionError(
                f"Move '{action_name}' rejected for station '{st_enum.value}': "
                f"Requires CQL-{required_cql}, station has CQL-{station_cql}."
            )
        if station_sql < required_sql:
            raise PermissionError(
                f"Move '{action_name}' rejected for station '{st_enum.value}': "
                f"Requires SQL-{required_sql}, station has SQL-{station_sql}."
            )

        return True

    # STAGE 6: ACTION
    def record_action(
        self,
        manager: Any,
        sortie_id: str,
        target_state_str: str,
        reason: str = "Playable turn action execution",
        artifacts: Optional[List[str]] = None,
        tests: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None,
    ) -> Any:
        """Records action outcome by transitioning sortie state adhering to predecessor rules."""
        models = self._get_models_mod()
        SortieState = models.SortieState

        try:
            target_state = SortieState(target_state_str)
        except ValueError as exc:
            raise ValueError(f"Invalid SortieState target '{target_state_str}'") from exc

        return manager.transition_sortie(
            actor="MISSION_CONTROL",
            sortie_id=sortie_id,
            target_state=target_state,
            reason=reason,
            artifacts=artifacts,
            tests=tests,
            evidence=evidence,
        )

    # STAGE 7: EVIDENCE
    def validate_evidence(
        self,
        evidence_refs: Tuple[str, ...],
        verified_event_ref: str,
        git_head_sha: str,
    ) -> str:
        """Validates evidence presence and generates deterministic evidence proof digest."""
        if not evidence_refs or not any(str(ref).strip() for ref in evidence_refs):
            raise ValueError("Evidence Validation Failed: evidence_refs cannot be empty.")
        if not verified_event_ref or not verified_event_ref.strip():
            raise ValueError("Evidence Validation Failed: verified_event_ref cannot be empty.")
        if not git_head_sha or not re.fullmatch(r"[0-9a-fA-F]{40}", git_head_sha):
            raise ValueError("Evidence Validation Failed: valid 40-character git_head_sha required.")

        payload = f"{verified_event_ref}:{git_head_sha}:{','.join(sorted(map(str, evidence_refs)))}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # STAGE 8 & 9: REWARD & STATE UPDATE
    def settle_reward_and_update_state(
        self,
        manager: Any,
        turn_id: str,
        station_id_str: str,
        action_name: str,
        verified_event_ref: str,
        evidence_refs: Tuple[str, ...],
        difficulty: int = 2,
        verification_quality: int = 5,
        impact: int = 3,
        reuse: int = 2,
    ) -> Tuple[Any, Any]:
        """Opens and resolves turn through TurnEngine, awarding points/XP and updating persistent state."""
        turn_mod = self._get_turn_engine_mod()
        points_xp_mod = self._get_points_xp_mod()

        PointEventType = points_xp_mod.PointEventType
        TurnContribution = turn_mod.TurnContribution
        TurnEngine = turn_mod.TurnEngine

        st_enum = resolve_station_enum(station_id_str)
        engine = TurnEngine(manager)

        input_ref = evidence_refs[0] if evidence_refs else f"input:{turn_id}"
        engine.open_turn(
            actor="MISSION_CONTROL",
            turn_id=turn_id,
            input_ref=input_ref,
        )

        contribution = TurnContribution(
            contribution_id=f"contrib_{st_enum.value.lower()}_{turn_id}",
            station_id=st_enum,
            role=action_name,
            evidence_refs=evidence_refs,
        )

        resolution = engine.resolve_turn(
            actor="MISSION_CONTROL",
            turn_id=turn_id,
            event_type=PointEventType.BUILD,
            verified_event_ref=verified_event_ref,
            evidence_refs=evidence_refs,
            contributions=(contribution,),
            reason=f"Verified playable turn {action_name}",
            difficulty=difficulty,
            verification_quality=verification_quality,
            impact=impact,
            reuse=reuse,
        )

        updated_state = manager.reconstruct_airspace_state()
        return resolution, updated_state

    # STAGE 10: REHYDRATED HUD
    def render_rehydrated_hud(
        self,
        manager: Any,
        immersion_state: Any = None,
        hub_surface: HubSurface = HubSurface.COMPOSITE,
        body: str = "",
    ) -> str:
        """Renders canonical visual HUD surface reflecting freshly updated persistent state."""
        if immersion_state is None:
            state = manager.reconstruct_airspace_state()
            git_head = self.sense_environment()["git_head_sha"]
            immersion_state_mod = importlib.import_module("sage.c2.immersion_state")
            immersion_state = immersion_state_mod.ImmersionState(
                station_identity="[SAGE::C2::CHATGPT]",
                mission=state.active_mission.objective if state.active_mission else "Persistent Organism Loop",
                phase=immersion_state_mod.ExecutionPhase.EXECUTE,
                flight_id="C2:REHYDRATION",
                flight_status=immersion_state_mod.FlightStatus.ACTIVE,
                trust_status=immersion_state_mod.TrustStatus.VERIFIED,
                frontier="AIRSPACE_C2",
                gate="GOVERNED_PLAYABLE_TURN",
                next_move="REHYDRATE_HUD",
                provenance_head=git_head[:8],
            )
        chatgpt_runtime_mod = importlib.import_module("sage.c2.chatgpt_runtime")
        return chatgpt_runtime_mod.render_chatgpt_c2_response(
            immersion_state,
            body=body,
            organism_manager=manager,
            force_hud=True,
            hub_surface=hub_surface,
        )

    # 10-STEP PLAYABLE TURN EXECUTION
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
        executor: Callable[[], Any] | None = None,
    ) -> OrganismTurnReceipt:
        """Execute one complete 10-step playable turn with verified progression."""
        verified = True

        # Step 1: SENSE - Identify station & handshake
        station_state = handshake_station_identity(
            self.runtime,
            manager=self.get_manager(),
            session_id=session_id,
            station_id=station_id,
            c2_context=c2_context,
        )

        # Step 2 & 3: REHYDRATE & IDENTITY LOCK
        if not station_state.provenance_sha or len(station_state.provenance_sha) != 40:
            raise ValueError("Identity lock failed: canonical 40-character provenance SHA required.")

        # Step 4: MISSION RESOLUTION
        if not station_state.active_mission:
            raise ValueError("Mission resolution failed: active mission required.")

        # Step 5: CHALLENGE / MOVE AUTHORIZATION
        requested_move = action_name.strip().upper()
        if not station_state.is_move_authorized(requested_move):
            raise ValueError(
                f"SAGE move rejection: '{requested_move}' is not authorized for "
                f"station '{station_state.station_id}' at qualification level CQL-{station_state.cql}. "
                f"Authorized move set: {station_state.authorized_moves}"
            )

        # Step 6: ACTION EXECUTION (with optional real executor)
        action_summary = task.strip() or f"Executed authorized move {requested_move}"
        if executor is not None:
            try:
                action_result = executor()
                if isinstance(action_result, str) and action_result.strip():
                    action_summary = action_result.strip()
            except Exception as exc:
                verified = False
                raise RuntimeError(f"Playable turn action execution failed: {exc}") from exc

        # Step 7: EVIDENCE CAPTURE
        refs_tuple = tuple(sorted(map(str, evidence_refs)))
        if not refs_tuple:
            refs_tuple = (f"ev_{session_id}_{hashlib.sha256(action_summary.encode('utf-8')).hexdigest()[:8]}",)

        raw_evidence = f"{session_id}:{requested_move}:{action_summary}:{','.join(refs_tuple)}"
        evidence_digest = hashlib.sha256(raw_evidence.encode("utf-8")).hexdigest()

        # Step 8: REWARD RECONCILIATION & DURABLE SETTLEMENT
        minted_xp = max(0, xp_award)
        awarded_points = max(0, points_award)

        mgr = self.get_manager()
        st_id_enum = resolve_station_enum(station_id)
        models_mod = self._get_models_mod()
        XPCategory = models_mod.XPCategory

        if minted_xp > 0:
            try:
                mgr.award_xp(
                    actor=station_id,
                    station_id=st_id_enum,
                    category=XPCategory.MISSION_XP,
                    amount=minted_xp,
                    reason=f"Playable turn verified action: {requested_move}",
                    verified_event_ref=evidence_digest,
                )
            except Exception as exc:
                verified = False
                raise RuntimeError(f"Durable XP award settlement failed: {exc}") from exc

        if awarded_points > 0:
            try:
                points_xp_mod = self._get_points_xp_mod()
                PointsXPEconomy = points_xp_mod.PointsXPEconomy
                PointEventType = points_xp_mod.PointEventType

                PointsXPEconomy.award_verified_event(
                    mgr,
                    event_id=f"evt_pt_{session_id}_{evidence_digest[:8]}",
                    actor=station_id,
                    station_id=st_id_enum,
                    event_type=PointEventType.BUILD,
                    reason=f"Playable turn verified points: {requested_move}",
                    verified_event_ref=evidence_digest,
                    evidence_refs=list(refs_tuple),
                )
            except Exception as exc:
                verified = False
                raise RuntimeError(f"Durable points award settlement failed: {exc}") from exc

        # Step 9: POST-RECONSTRUCTION STATE UPDATE (Read from reconstructed AirspaceState, NOT arithmetic)
        reconstructed_airspace = mgr.reconstruct_airspace_state()
        total_xp_after = reconstructed_airspace.game_progression.get_total_xp_for_station(st_id_enum)
        rank_mod = self._get_rank_system_mod()
        rank_after = rank_mod.rank_for_xp(total_xp_after)

        # Step 10: REHYDRATED C2 HUD & GAME FEEDBACK
        immersion_mod = importlib.import_module("sage.experimental.airspace.immersion")
        hud_projection = immersion_mod.render_four_layer_hud_from_manager(mgr)

        turn_id = f"TURN_{session_id}_{evidence_digest[:8]}"

        return OrganismTurnReceipt(
            turn_id=turn_id,
            session_id=session_id,
            station_id=station_id,
            provenance_sha=station_state.provenance_sha,
            action_executed=requested_move,
            authorized_moves=station_state.authorized_moves,
            evidence_digest=evidence_digest,
            evidence_refs=refs_tuple,
            xp_minted=minted_xp,
            points_awarded=awarded_points,
            rank_level_before=station_state.rank_level,
            rank_level_after=rank_after.level,
            rank_title_after=rank_after.title,
            total_xp_after=total_xp_after,
            hud_projection=hud_projection,
            verified=verified,
        )

    # COMPLETE 10-STEP PLAYABLE TURN EXECUTION
    def execute_playable_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
        station_id_str: str,
        action_name: str,
        evidence_refs: Tuple[str, ...],
        verified_event_ref: str,
        mission_id: str = "MISSION-PLAYABLE-001",
        objective: str = "Execute persistent playable organism turn",
        target: str = "AIRSPACE_C2",
        exact_git_head: Optional[str] = None,
        required_cql: int = 1,
        required_sql: int = 0,
        hub_surface: HubSurface = HubSurface.COMPOSITE,
        body_summary: str = "",
        executor: Callable[[], Any] | None = None,
    ) -> PlayableTurnResult:
        """Executes the complete 10-step playable turn interaction loop end-to-end."""
        # 1. SENSE
        sensed = self.sense_environment(exact_git_head=exact_git_head)
        git_head_sha = sensed["git_head_sha"]

        # 2. REHYDRATE
        manager = self.get_manager()

        # 3. IDENTITY LOCK
        station, identity = self.lock_identity(station_id_str, session_id)

        # 4. MISSION RESOLUTION
        mission, sortie = self.resolve_mission(
            manager, mission_id=mission_id, objective=objective, target=target
        )

        # 5. MOVE AUTHORIZATION
        self.authorize_move(
            station_id_str,
            action_name,
            required_cql=required_cql,
            required_sql=required_sql,
        )

        # 6. ACTION
        models = self._get_models_mod()
        SortieState = models.SortieState

        next_state_map = {
            SortieState.CREATED: SortieState.BRIEFED,
            SortieState.BRIEFED: SortieState.CLEARED,
            SortieState.CLEARED: SortieState.ACTIVE,
            SortieState.ACTIVE: SortieState.EVIDENCE_CAPTURE,
            SortieState.EVIDENCE_CAPTURE: SortieState.DEBRIEF,
            SortieState.DEBRIEF: SortieState.VERIFIED,
            SortieState.VERIFIED: SortieState.CLOSED,
            SortieState.CLOSED: SortieState.CLOSED,
        }
        target_state_obj = next_state_map.get(sortie.status, SortieState.BRIEFED)

        if executor is not None:
            executor()

        if sortie.status != target_state_obj:
            self.record_action(
                manager,
                sortie_id=sortie.sortie_id,
                target_state_str=target_state_obj.value,
                reason=f"Playable turn {action_name} executed ({sortie.status.value} -> {target_state_obj.value})",
                evidence=list(evidence_refs),
            )

        # 7. EVIDENCE
        evidence_digest = self.validate_evidence(evidence_refs, verified_event_ref, git_head_sha)

        # 8 & 9. REWARD & STATE UPDATE
        resolution, updated_state = self.settle_reward_and_update_state(
            manager,
            turn_id=turn_id,
            station_id_str=station_id_str,
            action_name=action_name,
            verified_event_ref=verified_event_ref,
            evidence_refs=evidence_refs,
        )

        # 10. REHYDRATED HUD
        immersion_state_mod = importlib.import_module("sage.c2.immersion_state")
        ImmersionState = immersion_state_mod.ImmersionState
        ExecutionPhase = immersion_state_mod.ExecutionPhase
        FlightStatus = immersion_state_mod.FlightStatus
        TrustStatus = immersion_state_mod.TrustStatus

        immersion_state = ImmersionState(
            station_identity=identity.nameplate,
            mission=objective,
            phase=ExecutionPhase.EXECUTE,
            flight_id=f"C2:{session_id}",
            flight_status=FlightStatus.ACTIVE,
            trust_status=TrustStatus.VERIFIED,
            frontier=target,
            gate="GOVERNED_PLAYABLE_TURN",
            next_move=action_name,
            evidence_refs=evidence_refs,
            provenance_head=git_head_sha[:8],
        )

        rehydrated_hud = self.render_rehydrated_hud(
            manager,
            immersion_state,
            hub_surface=hub_surface,
            body=body_summary or f"Turn '{turn_id}' closed and verified. Progression updated.",
        )

        # Reconcile projections
        projection_mod = self._get_projection_mod()
        rank_mod = self._get_rank_system_mod()

        st_enum = resolve_station_enum(station_id_str)
        proj = projection_mod.OrganismProjection.project_station(
            manager, updated_state, st_enum
        )
        total_xp = proj.career_xp
        rank_info = rank_mod.rank_for_xp(total_xp)

        return PlayableTurnResult(
            turn_id=turn_id,
            sequence_number=resolution.sequence_number,
            station_id=station_id_str,
            agent_name=station.agent_name,
            action_name=action_name,
            verified=resolution.verified,
            points_awarded=resolution.total_verified_points,
            xp_minted=resolution.total_xp_minted,
            rank_level=rank_info.level,
            rank_title=rank_info.title,
            evidence_digest=evidence_digest,
            git_head_sha=git_head_sha,
            rehydrated_hud=rehydrated_hud,
            turn_resolution=resolution,
            rehydrated_state=updated_state,
        )


__all__ = [
    "CQL_MOVE_SETS",
    "DEFAULT_CHATGPT_STATION",
    "ORGANISM_ID_MAIN",
    "OrganismRuntimeContractEngine",
    "OrganismStationState",
    "OrganismTurnReceipt",
    "PlayableTurnResult",
    "handshake_station_identity",
    "resolve_authorized_moves",
]
