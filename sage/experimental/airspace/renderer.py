"""Mobile-First Conversation Renderer for SAGE Airspace.

Formats AirspaceState, Missions, Sorties, Intel, Qualifications, Unified
Operating Picture, and Operational Readiness Assessments for compact,
high-density display on mobile conversation interfaces.
"""

from typing import Optional, Dict, Any, List
from sage.experimental.airspace.models import (
    AirspaceState,
    Mission,
    Sortie,
    StationID,
    IntelTelemetry,
    QualificationEvent,
)
from sage.experimental.airspace.readiness import OperationalReadinessAssessment
from sage.experimental.airspace.unified_operating_picture import UnifiedOperatingPicture


class AirspaceRenderer:
    """Renders SAGE Airspace operating picture, cards, and readiness assessments."""

    @staticmethod
    def render_progress_bar(current: int, total: int = 7, width: int = 10) -> str:
        """Renders compact ASCII progress bar."""
        filled = int(round((current / max(1, total)) * width))
        filled = min(width, max(0, filled))
        return "█" * filled + "░" * (width - filled)

    @classmethod
    def render_c2_board(cls, state: AirspaceState) -> str:
        """Renders compact mobile-first C2 Operating Board."""
        lines = []
        lines.append("SAGE AIRSPACE // C2 OPERATING PICTURE")
        lines.append("━" * 42)
        lines.append(f"STATUS       : {state.mode}")
        lines.append(f"SESSION      : {state.session_id}")

        if state.active_mission:
            lines.append(f"MISSION      : {state.active_mission.mission_id} [{state.active_mission.priority}]")
            lines.append(f"THEATER      : {state.active_mission.theater}")
        else:
            lines.append("MISSION      : NONE ACTIVE")

        lines.append("─" * 42)
        lines.append("STATIONS & QUALIFICATIONS")

        for st_id, station in state.stations.items():
            cql_bar = cls.render_progress_bar(station.current_cql, total=7, width=8)
            sql_str = f"SQL-{station.current_sql}" if station.current_sql > 0 else "      "
            lines.append(
                f"▪ {station.agent_name:<10} CQL-{station.current_cql} {cql_bar} {sql_str}"
            )

        lines.append("─" * 42)
        lines.append("ACTIVE SORTIES")
        if state.active_sorties:
            for sortie in state.active_sorties[-3:]:  # Show up to 3 active sorties
                lines.append(f"• [{sortie.sortie_id}] {sortie.status.value:<14} ({sortie.station.value})")
                lines.append(f"  Target: {sortie.target[:32]}")
        else:
            lines.append("• NO ACTIVE SORTIES")

        lines.append("─" * 42)
        lines.append("EVIDENCE & FRONTIER")
        if state.recent_evidence:
            lines.append(f"✓ Latest Evidence : {state.recent_evidence[-1][:32]}")
        if state.current_frontiers:
            lines.append(f"🎯 Current Frontier: {state.current_frontiers[-1][:32]}")
        lines.append(f"🔓 Next Clearance : {state.next_clearance[:32]}")
        lines.append("━" * 42)

        return "\n".join(lines)

    @classmethod
    def render_unified_operating_picture(cls, uop: UnifiedOperatingPicture) -> str:
        """Renders cross-system unified operating picture answering the 4 core operational questions."""
        q = uop.core_questions
        lines = []
        lines.append("SAGE CROSS-SYSTEM OPERATING PICTURE")
        lines.append("━" * 42)
        lines.append(f"ALIGNMENT STATUS : {uop.alignment_status}")
        lines.append("─" * 42)
        lines.append("1. WHAT IS ACTIVE?")
        lines.append(f"  ACT Session    : {q.what_is_active.get('act_session', 'N/A')}")
        lines.append(f"  Airspace Mission: {q.what_is_active.get('airspace_mission', 'NONE')}")
        lines.append(f"  Active Sorties : {', '.join(q.what_is_active.get('active_sorties', [])) or 'NONE'}")
        lines.append(f"  Sports Predictions: {q.what_is_active.get('sports_unresolved_predictions', 0)} unresolved")
        lines.append("─" * 42)
        lines.append("2. WHAT WAS VERIFIED?")
        lines.append(f"  ACT Completed  : {len(q.what_was_verified.get('act_completed_tasks', []))} tasks")
        lines.append(f"  Airspace Sorties: {len(q.what_was_verified.get('airspace_completed_sorties', []))} verified/closed")
        if q.what_was_verified.get("recent_evidence_refs"):
            lines.append(f"  Latest Evidence: {q.what_was_verified.get('recent_evidence_refs')[-1][:28]}")
        lines.append("─" * 42)
        lines.append("3. WHAT REMAINS?")
        lines.append(f"  ACT Pending    : {len(q.what_remains.get('act_pending_tasks', []))} tasks")
        if q.what_remains.get("current_frontiers"):
            lines.append(f"  Frontier       : {q.what_remains.get('current_frontiers')[-1][:28]}")
        lines.append("─" * 42)
        lines.append("4. WHAT IS AUTHORIZED NEXT?")
        lines.append(f"  Clearance      : {q.what_is_authorized_next.get('airspace_next_clearance')}")
        lines.append(f"  Authorized Role: {q.what_is_authorized_next.get('authorized_station')}")
        lines.append("━" * 42)
        return "\n".join(lines)

    @classmethod
    def render_readiness_assessment(cls, assessment: OperationalReadinessAssessment) -> str:
        """Renders mobile-first Operational Readiness Assessment card."""
        lines = []
        lines.append("SAGE OPERATIONAL READINESS ASSESSMENT")
        lines.append("━" * 42)
        lines.append(f"READINESS STATUS : {assessment.readiness_status.value}")
        lines.append(f"REASON           : {assessment.evaluation_reason}")
        lines.append("─" * 42)
        lines.append("ACTIVE:")
        for k, v in assessment.active.items():
            lines.append(f"  ▪ {k:<18}: {v}")
        lines.append("─" * 42)
        lines.append("VERIFIED:")
        for k, v in assessment.verified.items():
            lines.append(f"  ▪ {k:<18}: {v}")
        lines.append("─" * 42)
        lines.append("BLOCKED / ISSUES:")
        if assessment.blocked:
            for k, v in assessment.blocked.items():
                lines.append(f"  ▪ {k:<18}: {v}")
        else:
            lines.append("  ▪ NONE (Zero blockers)")
        lines.append("─" * 42)
        lines.append("AUTHORIZED NEXT:")
        for k, v in assessment.authorized_next.items():
            lines.append(f"  ▪ {k:<18}: {v}")
        lines.append("━" * 42)
        return "\n".join(lines)

    @classmethod
    def render_mission_card(cls, mission: Mission) -> str:
        """Renders compact mission card."""
        lines = []
        lines.append(f"MISSION CARD // {mission.mission_id}")
        lines.append("━" * 42)
        lines.append(f"NAME        : {mission.mission_name}")
        lines.append(f"THEATER     : {mission.theater}")
        lines.append(f"PRIORITY    : {mission.priority}")
        lines.append(f"STATUS      : {mission.status}")
        lines.append("─" * 42)
        lines.append(f"OBJECTIVE   : {mission.objective}")
        lines.append(f"FRONTIER    : {mission.current_frontier}")
        lines.append("─" * 42)
        lines.append("STATIONS ASSIGNED:")
        for st in mission.assigned_stations:
            lines.append(f" ▪ {st.value}")
        lines.append("━" * 42)
        return "\n".join(lines)

    @classmethod
    def render_sortie_debrief(cls, sortie: Sortie) -> str:
        """Renders compact sortie debrief card."""
        lines = []
        lines.append(f"SORTIE DEBRIEF // {sortie.sortie_id}")
        lines.append("━" * 42)
        lines.append(f"MISSION     : {sortie.mission_id}")
        lines.append(f"STATION     : {sortie.station.value}")
        lines.append(f"STATUS      : {sortie.status.value}")
        lines.append("─" * 42)
        lines.append(f"OBJECTIVE   : {sortie.objective}")
        lines.append(f"TARGET      : {sortie.target}")
        lines.append("─" * 42)
        lines.append(f"TESTS RUN   : {len(sortie.tests)}")
        lines.append(f"EVIDENCE    : {len(sortie.evidence)} refs")
        lines.append(f"ARTIFACTS   : {len(sortie.artifacts)}")
        if sortie.next_frontier:
            lines.append(f"NEXT FRONTIER: {sortie.next_frontier}")
        lines.append("━" * 42)
        return "\n".join(lines)

    @classmethod
    def render_qualification_card(cls, event: QualificationEvent) -> str:
        """Renders compact capability promotion debrief card."""
        lines = []
        lines.append("QUALIFICATION PROMOTION DEBRIEF")
        lines.append("━" * 42)
        lines.append(f"STATION     : {event.station_id.value}")
        lines.append(f"AGENT       : {event.agent_name}")
        lines.append(f"ADVANCEMENT : {event.qualification_type}-{event.previous_level} ➔ {event.qualification_type}-{event.new_level}")
        lines.append("─" * 42)
        lines.append(f"REASON      : {event.promotion_reason}")
        if event.downstream_effect:
            lines.append(f"EFFECT      : {event.downstream_effect}")
        lines.append(f"EVIDENCE    : {len(event.evidence_refs)} refs")
        lines.append(f"TESTS       : {len(event.test_refs)} refs")
        lines.append(f"VALIDATOR   : {event.validator}")
        lines.append("━" * 42)
        return "\n".join(lines)
