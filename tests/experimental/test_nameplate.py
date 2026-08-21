from sage.experimental.airspace.models import AirspaceState, StationID
from sage.experimental.airspace.nameplate import render_agent_nameplate, render_chat_nameplate


def test_nameplate_uses_canonical_station_progression():
    state = AirspaceState()
    state.game_progression.award_xp(
        station_id=StationID.MISSION_CONTROL,
        category="MISSION_XP",
        amount=125,
        reason="verified mission event",
        verified_event_ref="commit:test-123",
    )

    rendered = render_agent_nameplate(state, StationID.MISSION_CONTROL)

    assert "GPT" in rendered
    assert "CQL-4" in rendered
    assert "XP 125" in rendered


def test_chat_nameplate_is_compact_and_bracketed():
    state = AirspaceState()
    rendered = render_chat_nameplate(state, StationID.ENGINEERING_FLIGHT)

    assert rendered.startswith("[")
    assert "Jules" in rendered
    assert "CQL-4" in rendered
    assert rendered.endswith("]")


def test_nameplate_does_not_mutate_progression():
    state = AirspaceState()
    before = state.game_progression.get_total_xp_for_station(StationID.INTEL_STATION)

    render_agent_nameplate(state, StationID.INTEL_STATION)

    after = state.game_progression.get_total_xp_for_station(StationID.INTEL_STATION)
    assert after == before
