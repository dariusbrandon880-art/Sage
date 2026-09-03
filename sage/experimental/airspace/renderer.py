"""Mobile-First Conversation Renderer for SAGE Airspace.

Formats AirspaceState, Missions, Sorties, Intel, and Qualifications for compact,
high-density display in conversational interfaces on iPhone/iPad.
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


class AirspaceRenderer:
    """Renders SAGE Airspace operating picture and cards for conversation interfaces."""

    @staticmethod
    def render_progress_bar(current: int, total: int = 7, width: int = 10) -> str:
        """Renders compact ASCII progress bar."""
        filled = int(round((current / max(1, total)) * width))
        filled = min(width, max(0, filled))
        return "█" * filled + "░" * (width - filled)

    @classmethod
    def render_c2_board(cls, state: AirspaceState) -> str:
        """Renders compact mobile-first Four-Layer C2 Operating Board."""
        from sage.experimental.airspace.immersion import render_four_layer_hud
        return render_four_layer_hud(state)

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

    @classmethod
    def render_c2_board_from_manager(cls, manager, *, status: str = "READY") -> str:
        """Render the C2 board with the unified organism progression projection."""
        from sage.experimental.airspace.immersion import render_four_layer_hud_from_manager
        return render_four_layer_hud_from_manager(manager, status=status)
