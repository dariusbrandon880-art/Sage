from sage.agent_presence import get_agent_identity, get_team_context, render_chat_identity, render_team_status


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


def test_agent_identity_projects_canonical_identity_and_state():
    identity = get_agent_identity("MISSION_CONTROL")
    assert identity["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert identity["agent_name"] == "GPT"
    assert identity["role"]
    assert isinstance(identity["cql"], int)
    assert isinstance(identity["sql"], int)
    assert isinstance(identity["xp"], int)
    assert identity["state"]
    assert identity["read_only"] is True
    assert identity["authority"] == "canonical_airspace_state"


def test_chat_identity_renders_truthful_nameplate_and_live_state():
    rendered = render_chat_identity("MISSION_CONTROL")
    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert "CQL-" in rendered
    assert "XP " in rendered
    assert " • " in rendered


def test_team_context_nameplates_are_canonical_and_non_mutating():
    context = get_team_context()
    assert context["stations"]["MISSION_DIRECTOR"]["nameplate"] == "[SAGE::DIRECTOR]"
    assert context["stations"]["MISSION_CONTROL"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert context["stations"]["INTEL_STATION"]["nameplate"] == "[SAGE::INTEL::GEMINI]"
    assert context["stations"]["ENGINEERING_FLIGHT"]["nameplate"] == "[SAGE::ENGINEER::JULES]"
    assert all(station["read_only"] for station in context["stations"].values())
