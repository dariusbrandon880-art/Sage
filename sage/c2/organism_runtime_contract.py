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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sage.c2.agent_identity import AgentBoundaryIdentity, CHATGPT_AGENT_NAMEPLATE, JULES_AGENT_NAMEPLATE
from sage.c2.hub_presentation_boundary import HubSurface


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


class OrganismRuntimeContractEngine:
    """Orchestrates the 10-step persistent playable organism interaction loop."""

    def __init__(self, ledger_path: Optional[str | Path] = None):
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
    def rehydrate_state(self) -> Any:
        """Reconstructs current AirspaceState from historical event ledger."""
        manager_cls = self._get_airspace_manager_cls()
        manager = manager_cls(self.ledger_path)
        return manager.reconstruct_airspace_state()

    # STAGE 3: IDENTITY LOCK
    def lock_identity(self, station_id_str: str, session_id: str) -> Tuple[Any, AgentBoundaryIdentity]:
        """Locks station identity and verifies boundary identity provenance."""
        models = self._get_models_mod()
        StationID = models.StationID
        try:
            st_enum = StationID(station_id_str)
        except ValueError as exc:
            raise ValueError(f"Unknown or invalid StationID '{station_id_str}'") from exc

        state = self.rehydrate_state()
        if st_enum not in state.stations:
            raise KeyError(f"Station '{st_enum.value}' is not registered in Airspace state.")

        station = state.stations[st_enum]
        if not station.active_status:
            raise PermissionError(f"Station '{st_enum.value}' is inactive.")

        nameplate = JULES_AGENT_NAMEPLATE if st_enum == StationID.ENGINEERING_FLIGHT else CHATGPT_AGENT_NAMEPLATE
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
        models = self._get_models_mod()
        StationID = models.StationID
        st_enum = StationID(station_id_str)

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
        if not evidence_refs or not any(ref.strip() for ref in evidence_refs):
            raise ValueError("Evidence Validation Failed: evidence_refs cannot be empty.")
        if not verified_event_ref or not verified_event_ref.strip():
            raise ValueError("Evidence Validation Failed: verified_event_ref cannot be empty.")
        if not git_head_sha or not re.fullmatch(r"[0-9a-fA-F]{40}", git_head_sha):
            raise ValueError("Evidence Validation Failed: valid git_head_sha required.")

        payload = f"{verified_event_ref}:{git_head_sha}:{','.join(sorted(evidence_refs))}"
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
        models = self._get_models_mod()
        turn_mod = self._get_turn_engine_mod()
        points_xp_mod = self._get_points_xp_mod()

        StationID = models.StationID
        PointEventType = points_xp_mod.PointEventType
        TurnContribution = turn_mod.TurnContribution
        TurnEngine = turn_mod.TurnEngine

        st_enum = StationID(station_id_str)
        engine = TurnEngine(manager)

        input_ref = evidence_refs[0] if evidence_refs else f"input:{turn_id}"
        engine.open_turn(
            actor="MISSION_CONTROL",
            turn_id=turn_id,
            input_ref=input_ref,
        )

        contribution = TurnContribution(
            contribution_id=f"contrib_{station_id_str.lower()}_{turn_id}",
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
    ) -> PlayableTurnResult:
        """Executes the complete 10-step playable turn interaction loop end-to-end."""
        # 1. SENSE
        sensed = self.sense_environment(exact_git_head=exact_git_head)
        git_head_sha = sensed["git_head_sha"]

        # 2. REHYDRATE
        manager_cls = self._get_airspace_manager_cls()
        manager = manager_cls(self.ledger_path)

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
        models = self._get_models_mod()
        projection_mod = self._get_projection_mod()
        rank_mod = self._get_rank_system_mod()

        st_enum = models.StationID(station_id_str)
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
    "OrganismRuntimeContractEngine",
    "PlayableTurnResult",
]
