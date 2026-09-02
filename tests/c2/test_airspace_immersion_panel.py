from sage.experimental.airspace.immersion import render_station_operating_panel
from sage.experimental.airspace.models import AirspaceState, Station, StationID


def _state() -> AirspaceState:
    state = AirspaceState(
        session_id="session_test_001",
        mode="OPERATIONAL",
        stations={
            StationID.MISSION_CONTROL: Station(
                station_id=StationID.MISSION_CONTROL,
                agent_name="GPT",
                role_description="C2 Synthesis & Operational Coordination",
                current_cql=4,
                current_sql=3,
            )
        },
        current_frontiers=["frontier-test"],
        recent_evidence=[{"evidence_id": "ev-001"}],
        next_clearance="VERIFY",
        active_sorties=[],
    )
    return state


def test_station_operating_panel_projects_existing_progression_and_operational_state():
    panel = render_station_operating_panel(_state(), StationID.MISSION_CONTROL)

    assert "[SAGE::C2::CHATGPT]" in panel
    assert "XP" in panel
    assert "CQL-4" in panel
    assert "SQL-3" in panel
    assert "MISSION" in panel
    assert "FRONTIER" in panel
    assert "EVIDENCE 1" in panel
    assert "NEXT VERIFY" in panel
    assert "NO ACTIVE SORTIES" in panel


def test_station_operating_panel_is_presentation_only():
    state = _state()
    before = repr(state)
    render_station_operating_panel(state, StationID.MISSION_CONTROL, compact=False)
    assert repr(state) == before
