"""SAGE Operational Readiness Assessment Engine.

Provides a governed, read-only projection answering:
"Given current persisted evidence, is SAGE ready to continue?"
without substituting human decision authority or mutating source subsystems.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.airspace.models import SortieState
from sage.experimental.airspace.unified_operating_picture import (
    UnifiedOperatingPicture,
    UnifiedOperatingPictureResolver,
)


class ReadinessStatus(str, Enum):
    """SAGE Operational Readiness Assessment Status."""
    READY = "READY"
    BLOCKED_MISSING_EVIDENCE = "BLOCKED_MISSING_EVIDENCE"
    REQUIRES_REVIEW_CONFLICT = "REQUIRES_REVIEW_CONFLICT"
    STATE_CORRUPTED = "STATE_CORRUPTED"
    STALE_OBSERVATION = "STALE_OBSERVATION"


class OperationalReadinessAssessment(BaseModel):
    """Governed operational readiness projection across SAGE subsystems."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: Dict[str, Any] = Field(default_factory=dict)
    verified: Dict[str, Any] = Field(default_factory=dict)
    blocked: Dict[str, Any] = Field(default_factory=dict)
    authorized_next: Dict[str, Any] = Field(default_factory=dict)
    readiness_status: ReadinessStatus = ReadinessStatus.READY
    evaluation_reason: str = "All persistent evidence verified cleanly. SAGE is ready to continue."


class OperationalReadinessEvaluator:
    """Evaluates cross-system persisted evidence to project operational readiness."""

    def __init__(
        self,
        resolver: Optional[UnifiedOperatingPictureResolver] = None,
        airspace_ledger_path: Optional[str | Path] = None,
        act_storage_path: Optional[str | Path] = None,
        sports_ledger_path: Optional[str | Path] = None,
    ):
        self.airspace_ledger_path = Path(airspace_ledger_path or "evidence_capture/airspace_ledger.json")
        self.resolver = resolver or UnifiedOperatingPictureResolver(
            airspace_ledger_path=self.airspace_ledger_path,
            act_storage_path=act_storage_path,
            sports_ledger_path=sports_ledger_path,
        )

    def evaluate_readiness(self, session_id: Optional[str] = None) -> OperationalReadinessAssessment:
        """Evaluates persistent evidence and generates a governed readiness assessment."""
        # 1. State Corruption Check (JSON parsing or file corruption)
        if self.airspace_ledger_path.exists():
            try:
                with open(self.airspace_ledger_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        json.loads(content)
            except Exception as e:
                return OperationalReadinessAssessment(
                    readiness_status=ReadinessStatus.STATE_CORRUPTED,
                    evaluation_reason=f"Airspace ledger corruption detected: {e}",
                    blocked={"error": str(e), "ledger_path": str(self.airspace_ledger_path)},
                )

        # 2. Resolve Unified Operating Picture
        try:
            uop = self.resolver.resolve_unified_operating_picture(session_id=session_id)
        except Exception as e:
            return OperationalReadinessAssessment(
                readiness_status=ReadinessStatus.STATE_CORRUPTED,
                evaluation_reason=f"Failed to resolve operating picture: {e}",
                blocked={"error": str(e)},
            )

        # 3. Subsystem Alignment Conflict Check
        if uop.alignment_status == "MISALIGNED":
            return OperationalReadinessAssessment(
                readiness_status=ReadinessStatus.REQUIRES_REVIEW_CONFLICT,
                evaluation_reason="Subsystem alignment conflict detected: Airspace mission and Sports/RCE theater mismatch.",
                active=uop.core_questions.what_is_active,
                verified=uop.core_questions.what_was_verified,
                blocked={"conflict_type": "MISALIGNED_THEATER", "airspace_mission": uop.airspace_summary.get("active_mission_id")},
                authorized_next={"action": "HUMAN_OPERATOR_REVIEW_REQUIRED"},
            )

        # 4. Check Missing Evidence Requirements
        airspace_state = self.resolver.airspace_manager.reconstruct_airspace_state()
        missing_evidence_items = []

        if airspace_state.active_mission:
            reqs = airspace_state.active_mission.evidence_requirements
            for req in reqs:
                if not Path(req).exists():
                    missing_evidence_items.append(f"Mission '{airspace_state.active_mission.mission_id}' missing evidence reference file: {req}")

        for sortie in airspace_state.active_sorties:
            if sortie.status in (SortieState.EVIDENCE_CAPTURE, SortieState.DEBRIEF) and not sortie.evidence:
                missing_evidence_items.append(f"Sortie '{sortie.sortie_id}' in state {sortie.status.value} missing evidence")

        if missing_evidence_items:
            return OperationalReadinessAssessment(
                readiness_status=ReadinessStatus.BLOCKED_MISSING_EVIDENCE,
                evaluation_reason=f"Missing evidence blocks readiness: {missing_evidence_items[0]}",
                active=uop.core_questions.what_is_active,
                verified=uop.core_questions.what_was_verified,
                blocked={"missing_evidence": missing_evidence_items},
                authorized_next={"action": "PROVIDE_REQUIRED_EVIDENCE"},
            )

        # 5. Stale Observation Check (If observations are > 48h old)
        is_stale = False
        stale_reason = ""
        if airspace_state.last_updated:
            try:
                last_dt = datetime.fromisoformat(airspace_state.last_updated)
                if datetime.now(timezone.utc) - last_dt > timedelta(hours=48):
                    is_stale = True
                    stale_reason = f"Airspace state last updated {airspace_state.last_updated} (>48h ago)"
            except Exception:
                pass

        if is_stale:
            return OperationalReadinessAssessment(
                readiness_status=ReadinessStatus.STALE_OBSERVATION,
                evaluation_reason=f"Stale observation detected: {stale_reason}",
                active=uop.core_questions.what_is_active,
                verified=uop.core_questions.what_was_verified,
                blocked={"stale_reason": stale_reason},
                authorized_next={"action": "REFRESH_OBSERVATION_TELEMETRY"},
            )

        # 6. Default: READY
        active_summary = {
            "act_session": uop.act_summary.get("session_id"),
            "airspace_mission": uop.airspace_summary.get("active_mission_id"),
            "active_sorties_count": uop.airspace_summary.get("active_sorties_count"),
            "unresolved_sports_predictions": uop.sports_summary.get("unresolved_predictions_count"),
        }

        verified_summary = {
            "completed_act_tasks": uop.act_summary.get("completed_tasks_count"),
            "completed_sorties": uop.airspace_summary.get("completed_sorties_count"),
            "resolved_sports_predictions": uop.sports_summary.get("resolved_predictions_count"),
            "evidence_count": uop.airspace_summary.get("recent_evidence_count"),
        }

        blocked_summary = {
            "act_pending_tasks": uop.act_summary.get("pending_tasks_count"),
            "conflicts": [],
            "missing_evidence": [],
        }

        authorized_next_summary = {
            "clearance": uop.airspace_summary.get("next_clearance"),
            "station": "ENGINEERING_FLIGHT",
            "frontier": uop.core_questions.what_remains.get("current_frontiers")[-1] if uop.core_questions.what_remains.get("current_frontiers") else "Continue governed flight",
        }

        return OperationalReadinessAssessment(
            active=active_summary,
            verified=verified_summary,
            blocked=blocked_summary,
            authorized_next=authorized_next_summary,
            readiness_status=ReadinessStatus.READY,
            evaluation_reason="All persistent evidence verified cleanly. SAGE is ready to continue.",
        )
