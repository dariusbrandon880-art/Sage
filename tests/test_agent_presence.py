from sage.agent_presence import get_team_context, render_team_status


def test_team_status_exposes_all_station_progression():
    rendered = render_team_status()
    assert "Director:" in rendered
    assert "C2:GPT" in rendered
    assert "Intel:Gemini" in rendered
    assert "Engineering:Jules" in rendered
    assert "CQL-" in rendered
    assert "XP-" in rendered


def test_team_context_is_read_only_and_structured():
    context = get_team_context()
    assert context["read_only"] is True
    assert context["authority"] == "canonical_airspace_state"
    assert set(context["stations"]) == {
        "MISSION_DIRECTOR",
        "MISSION_CONTROL",
        "INTEL_STATION",
        "ENGINEERING_FLIGHT",
    }
