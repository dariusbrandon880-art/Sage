"""Cross-System Unified Operating Picture Bridge for SAGE.

Reconstructs a single, repository-backed operational view across ACT Continuity,
Airspace C2 Observability, and Sports/RCE Longitudinal Observation without mutating
subsystem ownership boundaries.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import AirspaceState, SortieState
from sage.experimental.airspace.sports_adapter import SportsRCEAirspaceAdapter
from sage.experimental.flight_record import SAGEFlightRecordManager


class CoreOperationalAnswers(BaseModel):
    """Answers to SAGE's four fundamental operational questions."""
    what_is_active: Dict[str, Any] = Field(default_factory=dict)
    what_was_verified: Dict[str, Any] = Field(default_factory=dict)
    what_remains: Dict[str, Any] = Field(default_factory=dict)
    what_is_authorized_next: Dict[str, Any] = Field(default_factory=dict)


class UnifiedOperatingPicture(BaseModel):
    """Repository-backed cross-system operational reconstruction snapshot."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    act_summary: Dict[str, Any] = Field(default_factory=dict)
    airspace_summary: Dict[str, Any] = Field(default_factory=dict)
    sports_summary: Dict[str, Any] = Field(default_factory=dict)
    core_questions: CoreOperationalAnswers = Field(default_factory=CoreOperationalAnswers)
    alignment_status: str = "ALIGNED"  # ALIGNED, MISALIGNED, EVIDENCE_CORRUPTED


class UnifiedOperatingPictureResolver:
    """Read-only resolver querying ACT, Airspace, and Sports/RCE to build a unified picture."""

    def __init__(
        self,
        airspace_ledger_path: Optional[str | Path] = None,
        act_storage_path: Optional[str | Path] = None,
        sports_ledger_path: Optional[str | Path] = None,
    ):
        self.airspace_manager = AirspaceManager(ledger_path=airspace_ledger_path)
        self.act_storage_path = Path(act_storage_path or "sage_data/experimental_ccl")
        self.flight_record_manager = SAGEFlightRecordManager(sports_ledger_path=sports_ledger_path)
        self.sports_adapter = SportsRCEAirspaceAdapter(flight_record_manager=self.flight_record_manager)

    def resolve_unified_operating_picture(self, session_id: Optional[str] = None) -> UnifiedOperatingPicture:
        """Reconstructs cross-system operating picture from underlying persistent state."""
        # 1. Reconstruct Airspace State
        airspace_state = self.airspace_manager.reconstruct_airspace_state()

        # 2. Reconstruct ACT Continuity State
        orchestrator = DeveloperWorkflowOrchestrator(
            session_id=session_id or "session_airspace_v1",
            ccl=None,
            evidence_output_path="evidence_capture/ccl_operational_feedback.json"
        )
        orchestrator.ccl.storage_path = self.act_storage_path
        orchestrator.mission_queue.storage_path = self.act_storage_path
        orchestrator.mission_queue.queue_file = self.act_storage_path / "mission_queue.json"
        orchestrator.mission_queue.load_queue()

        # 3. Query Sports/RCE State
        sports_summary = self.sports_adapter.get_sports_theater_summary()

        # 4. Extract ACT Summary
        act_session = orchestrator.session
        pending_tasks = [t for t in orchestrator.mission_queue.list_tasks() if t.status == "PENDING"]
        completed_tasks = [t for t in orchestrator.mission_queue.list_tasks() if t.status == "COMPLETED"]

        act_summary = {
            "session_id": act_session.session_id if act_session else "N/A",
            "active_objectives": list(act_session.active_objectives) if act_session else [],
            "pending_tasks_count": len(pending_tasks),
            "completed_tasks_count": len(completed_tasks),
            "loop_mode": orchestrator.loop_state.get("mode", "CONTINUOUS"),
            "last_checkpoint_id": orchestrator.loop_state.get("last_checkpoint_id"),
        }

        # 5. Extract Airspace Summary
        active_sorties = [s for s in airspace_state.active_sorties if s.status in (SortieState.ACTIVE, SortieState.CLEARED, SortieState.EVIDENCE_CAPTURE)]
        completed_sorties = [s for s in airspace_state.active_sorties if s.status in (SortieState.VERIFIED, SortieState.CLOSED)]

        airspace_summary = {
            "airspace_id": airspace_state.airspace_id,
            "mode": airspace_state.mode,
            "active_mission_id": airspace_state.active_mission.mission_id if airspace_state.active_mission else None,
            "active_sorties_count": len(active_sorties),
            "completed_sorties_count": len(completed_sorties),
            "stations_cql": {st_id.value: st.current_cql for st_id, st in airspace_state.stations.items()},
            "recent_evidence_count": len(airspace_state.recent_evidence),
            "next_clearance": airspace_state.next_clearance,
        }

        # 6. Formulate Core Questions Answers
        what_is_active = {
            "act_session": act_summary.get("session_id"),
            "airspace_mission": airspace_summary.get("active_mission_id"),
            "active_sorties": [s.sortie_id for s in active_sorties],
            "sports_theater": sports_summary.get("theater"),
            "sports_unresolved_predictions": sports_summary.get("unresolved_predictions_count"),
        }

        what_was_verified = {
            "act_completed_tasks": [t.task_id for t in completed_tasks],
            "airspace_completed_sorties": [s.sortie_id for s in completed_sorties],
            "recent_evidence_refs": airspace_state.recent_evidence[-5:],  # Last 5
            "sports_resolved_predictions": sports_summary.get("resolved_predictions_count"),
        }

        what_remains = {
            "act_pending_tasks": [t.task_id for t in pending_tasks],
            "current_frontiers": airspace_state.current_frontiers,
            "sports_pending_predictions": sports_summary.get("unresolved_predictions_count"),
        }

        what_is_authorized_next = {
            "airspace_next_clearance": airspace_state.next_clearance,
            "authorized_station": "ENGINEERING_FLIGHT",
            "next_authorized_boundary": "Session 3 Airspace cross-system verification complete",
        }

        core_answers = CoreOperationalAnswers(
            what_is_active=what_is_active,
            what_was_verified=what_was_verified,
            what_remains=what_remains,
            what_is_authorized_next=what_is_authorized_next,
        )

        # Alignment status check
        alignment_status = "ALIGNED"
        if airspace_state.active_mission and airspace_state.active_mission.mission_id == "RCE-002.1":
            if sports_summary.get("theater") != "Sports/RCE":
                alignment_status = "MISALIGNED"

        return UnifiedOperatingPicture(
            timestamp=datetime.now(timezone.utc).isoformat(),
            act_summary=act_summary,
            airspace_summary=airspace_summary,
            sports_summary=sports_summary,
            core_questions=core_answers,
            alignment_status=alignment_status,
        )
