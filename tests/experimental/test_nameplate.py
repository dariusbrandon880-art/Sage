from sage.experimental.airspace.models import AirspaceState, StationID
from sage.experimental.airspace.nameplate import (
    build_nametag_badge,
    get_rank_title,
    render_agent_nameplate,
    render_chat_nameplate,
    render_nametag_badge,
)


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


def test_chat_nameplate_is_canonical_and_bracketed():
    state = AirspaceState()
    rendered = render_chat_nameplate(state, StationID.ENGINEERING_FLIGHT)

    assert rendered.startswith("[SAGE::ENGINEER::JULES]")
    assert "Jules" in rendered
    assert "CQL-4" in rendered
    assert "XP 0" in rendered


def test_nameplate_does_not_mutate_progression():
    state = AirspaceState()
    before = state.game_progression.get_total_xp_for_station(StationID.INTEL_STATION)

    render_agent_nameplate(state, StationID.INTEL_STATION)

    after = state.game_progression.get_total_xp_for_station(StationID.INTEL_STATION)
    assert after == before


def test_get_rank_title_mapping():
    assert get_rank_title(StationID.ENGINEERING_FLIGHT, 4) == "Senior Software Engineer"
    assert get_rank_title(StationID.ENGINEERING_FLIGHT, 7) == "Lead Systems Architect"
    assert get_rank_title(StationID.MISSION_DIRECTOR, 7) == "Fleet Commander"
    assert get_rank_title(StationID.INTEL_STATION, 3) == "Senior Intel Specialist"


def test_build_and_render_nametag_badge():
    state = AirspaceState()
    state.game_progression.award_xp(
        station_id=StationID.ENGINEERING_FLIGHT,
        category="ENGINEERING_FLIGHT_XP",
        amount=250,
        reason="implemented nametag badges",
        verified_event_ref="commit:nametag-456",
    )

    badge = build_nametag_badge(state, StationID.ENGINEERING_FLIGHT)
    assert badge["nameplate"] == "[SAGE::ENGINEER::JULES]"
    assert badge["agent_name"] == "Jules"
    assert badge["rank_title"] == "Senior Software Engineer"
    assert badge["cql"] == 4
    assert badge["xp"] == 250
    assert badge["verification_badge"] == "[VERIFIED::CQL-4]"

    rendered = render_nametag_badge(state, StationID.ENGINEERING_FLIGHT)
    assert "[SAGE::ENGINEER::JULES]" in rendered
    assert "Senior Software Engineer" in rendered
    assert "[VERIFIED::CQL-4]" in rendered
    assert "XP 250" in rendered
