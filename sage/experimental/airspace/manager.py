"""Persistent Event & State Manager for SAGE Airspace.

Provides append-only event persistence to `evidence_capture/airspace_ledger.json`
and deterministic restart reconstruction of the `AirspaceState`.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.airspace.models import (
    AirspaceState,
    Mission,
    Sortie,
    SortieState,
    StationID,
    IntelTelemetry,
    IntelAssessment,
    QualificationRegistry,
    QualificationEvent,
    QualificationChallengeEvent,
    GameProgression,
    XPEvent,
    XPCategory,
)


class AirspaceEvent(BaseModel):
    """An immutable, append-only Airspace event."""
    event_id: str
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str
    mission_id: Optional[str] = None
    sortie_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)
    event_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.event_sha256:
            self.event_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        serialized = json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "mission_id": self.mission_id or "",
            "sortie_id": self.sortie_id or "",
            "payload": self.payload,
            "evidence_refs": sorted(self.evidence_refs),
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AirspaceManager:
    """Manages append-only event persistence and deterministic AirspaceState reconstruction."""

    def __init__(self, ledger_path: Optional[str | Path] = None):
        self.ledger_path = Path(ledger_path or "evidence_capture/airspace_ledger.json")

    def _load_raw_events(self) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    def _save_raw_events(self, events: List[Dict[str, Any]]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)

    def record_event(
        self,
        event_type: str,
        actor: str,
        payload: Dict[str, Any],
        evidence_refs: Optional[List[str]] = None,
        mission_id: Optional[str] = None,
        sortie_id: Optional[str] = None,
    ) -> AirspaceEvent:
        """Appends a new AirspaceEvent to the persistent ledger."""
        raw_events = self._load_raw_events()
        event_id = f"evt_airspace_{len(raw_events) + 1:04d}_{hashlib.sha256(f'{event_type}:{datetime.now(timezone.utc).isoformat()}'.encode('utf-8')).hexdigest()[:8]}"

        event = AirspaceEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            mission_id=mission_id,
            sortie_id=sortie_id,
            payload=payload,
            evidence_refs=evidence_refs or [],
        )

        raw_events.append(event.model_dump())
        self._save_raw_events(raw_events)
        return event

    def reconstruct_airspace_state(self) -> AirspaceState:
        """Reconstructs current AirspaceState from historical event ledger."""
        state = AirspaceState()
        raw_events = self._load_raw_events()

        sorties_map: Dict[str, Sortie] = {}

        for raw in raw_events:
            evt_type = raw.get("event_type")
            payload = raw.get("payload", {})
            ev_refs = raw.get("evidence_refs", [])

            if evt_type == "MISSION_CREATED":
                mission = Mission(**payload)
                state.active_mission = mission
                if mission.current_frontier and mission.current_frontier not in state.current_frontiers:
                    state.current_frontiers.append(mission.current_frontier)

            elif evt_type == "SORTIE_CREATED":
                sortie = Sortie(**payload)
                sorties_map[sortie.sortie_id] = sortie

            elif evt_type == "SORTIE_TRANSITIONED":
                sortie_id = raw.get("sortie_id")
                target_state_str = payload.get("target_state")
                reason = payload.get("reason", "")
                if sortie_id in sorties_map and target_state_str:
                    target_state = SortieState(target_state_str)
                    sorties_map[sortie_id].transition_to(target_state, reason=reason)
                    if payload.get("artifacts"):
                        sorties_map[sortie_id].artifacts.extend(payload.get("artifacts", []))
                    if payload.get("tests"):
                        sorties_map[sortie_id].tests.extend(payload.get("tests", []))
                    if payload.get("evidence"):
                        sorties_map[sortie_id].evidence.extend(payload.get("evidence", []))
                    if payload.get("next_frontier"):
                        sorties_map[sortie_id].next_frontier = payload.get("next_frontier")

            elif evt_type == "QUALIFICATION_PROMOTED":
                st_id = StationID(payload["station_id"])
                agent_name = payload["agent_name"]
                q_type = payload["qualification_type"]
                target_lvl = payload["new_level"]
                reason = payload["promotion_reason"]
                t_refs = payload.get("test_refs", [])
                downstream = payload.get("downstream_effect")

                state.qualification_registry.promote_station(
                    station_id=st_id,
                    agent_name=agent_name,
                    qualification_type=q_type,
                    target_level=target_lvl,
                    reason=reason,
                    evidence_refs=ev_refs,
                    test_refs=t_refs,
                    validator=raw.get("actor", "Mission Control"),
                    downstream_effect=downstream,
                )
                if st_id in state.stations:
                    if q_type == "CQL":
                        state.stations[st_id].current_cql = target_lvl
                    else:
                        state.stations[st_id].current_sql = target_lvl

            elif evt_type == "QUALIFICATION_CHALLENGED":
                st_id = StationID(payload["station_id"])
                q_type = payload["qualification_type"]
                reason = payload["reason"]
                fals_refs = payload.get("falsifying_evidence_refs", [])
                demotion = payload["demotion_target"]

                state.qualification_registry.challenge_qualification(
                    station_id=st_id,
                    qualification_type=q_type,
                    reason=reason,
                    falsifying_evidence_refs=fals_refs,
                    demotion_target=demotion,
                )
                if st_id in state.stations:
                    if q_type == "CQL":
                        state.stations[st_id].current_cql = demotion
                    else:
                        state.stations[st_id].current_sql = demotion

            elif evt_type == "XP_AWARDED":
                st_id = StationID(payload["station_id"])
                cat = XPCategory(payload["category"])
                amt = payload["amount"]
                reason = payload["reason"]
                v_ref = payload["verified_event_ref"]

                state.game_progression.award_xp(
                    station_id=st_id,
                    category=cat,
                    amount=amt,
                    reason=reason,
                    verified_event_ref=v_ref,
                )

            if ev_refs:
                for ref in ev_refs:
                    if ref not in state.recent_evidence:
                        state.recent_evidence.append(ref)

        state.active_sorties = list(sorties_map.values())
        return state

    # Convenience operational methods

    def create_mission(self, actor: str, mission: Mission) -> AirspaceEvent:
        return self.record_event(
            event_type="MISSION_CREATED",
            actor=actor,
            payload=mission.model_dump(),
            mission_id=mission.mission_id,
            evidence_refs=mission.evidence_requirements,
        )

    def create_sortie(self, actor: str, sortie: Sortie) -> AirspaceEvent:
        return self.record_event(
            event_type="SORTIE_CREATED",
            actor=actor,
            payload=sortie.model_dump(),
            mission_id=sortie.mission_id,
            sortie_id=sortie.sortie_id,
        )

    def transition_sortie(
        self,
        actor: str,
        sortie_id: str,
        target_state: SortieState,
        reason: str = "",
        artifacts: Optional[List[str]] = None,
        tests: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None,
        next_frontier: Optional[str] = None,
    ) -> AirspaceEvent:
        # Dry run state reconstruction to verify state machine transition
        current_state = self.reconstruct_airspace_state()
        target_sortie = next((s for s in current_state.active_sorties if s.sortie_id == sortie_id), None)
        if not target_sortie:
            raise KeyError(f"Sortie '{sortie_id}' not found in current Airspace state.")

        # Test transition validity (raises ValueError if illegal)
        temp_copy = Sortie(**target_sortie.model_dump())
        temp_copy.transition_to(target_state, reason=reason)

        payload = {
            "target_state": target_state.value,
            "reason": reason,
            "artifacts": artifacts or [],
            "tests": tests or [],
            "evidence": evidence or [],
            "next_frontier": next_frontier,
        }
        return self.record_event(
            event_type="SORTIE_TRANSITIONED",
            actor=actor,
            mission_id=target_sortie.mission_id,
            sortie_id=sortie_id,
            payload=payload,
            evidence_refs=evidence or [],
        )

    def record_intel(self, actor: str, telemetry: IntelTelemetry) -> AirspaceEvent:
        return self.record_event(
            event_type="INTEL_RECORDED",
            actor=actor,
            payload=telemetry.model_dump(),
            evidence_refs=telemetry.evidence,
        )

    def promote_qualification(
        self,
        actor: str,
        station_id: StationID,
        agent_name: str,
        qualification_type: str,
        target_level: int,
        reason: str,
        evidence_refs: List[str],
        test_refs: List[str],
        downstream_effect: Optional[str] = None,
    ) -> AirspaceEvent:
        # Dry run against current state to ensure valid promotion rules
        current_state = self.reconstruct_airspace_state()
        current_state.qualification_registry.promote_station(
            station_id=station_id,
            agent_name=agent_name,
            qualification_type=qualification_type,
            target_level=target_level,
            reason=reason,
            evidence_refs=evidence_refs,
            test_refs=test_refs,
            validator=actor,
            downstream_effect=downstream_effect,
        )

        payload = {
            "station_id": station_id.value,
            "agent_name": agent_name,
            "qualification_type": qualification_type,
            "new_level": target_level,
            "promotion_reason": reason,
            "test_refs": test_refs,
            "downstream_effect": downstream_effect,
        }
        return self.record_event(
            event_type="QUALIFICATION_PROMOTED",
            actor=actor,
            payload=payload,
            evidence_refs=evidence_refs,
        )

    def award_xp(
        self,
        actor: str,
        station_id: StationID,
        category: XPCategory,
        amount: int,
        reason: str,
        verified_event_ref: str,
    ) -> AirspaceEvent:
        if not verified_event_ref or verified_event_ref.strip() == "":
            raise ValueError("XP Award Rejected: verified_event_ref is required.")

        payload = {
            "station_id": station_id.value,
            "category": category.value,
            "amount": amount,
            "reason": reason,
            "verified_event_ref": verified_event_ref,
        }
        return self.record_event(
            event_type="XP_AWARDED",
            actor=actor,
            payload=payload,
            evidence_refs=[verified_event_ref],
        )
