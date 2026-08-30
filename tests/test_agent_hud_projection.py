from sage.agent_hud_projection import build_agent_hud_projection, render_agent_hud


def _context():
    return {
        "context_id": "mission-170-next",
        "audience": "SAGE::DIRECTOR",
        "purpose": "HUD",
        "bounded": True,
        "read_only": True,
        "self": {
            "nameplate": "[SAGE::C2::CHATGPT]",
            "agent_name": "GPT",
            "role": "Mission Control",
            "cql": 1,
            "sql": 1,
            "xp": 100,
            "state": "WORKING",
        },
        "team": {
            "coordination": {"status": "ACTIVE"},
            "stations": {
                "MISSION_CONTROL": {
                    "nameplate": "[SAGE::C2::CHATGPT]",
                    "agent_name": "GPT",
                    "role": "Mission Control",
                    "cql": 1,
                    "sql": 1,
                    "xp": 100,
                    "state": "WORKING",
                },
                "INTEL_STATION": {
                    "nameplate": "[SAGE::INTEL::GEMINI]",
                    "agent_name": "Gemini",
                    "role": "Intel",
                    "cql": 1,
                    "sql": 1,
                    "xp": 80,
                    "state": "RECON",
                },
            },
        },
        "coordination": {
            "pending": [
                {
                    "sender": "SAGE::INTEL::GEMINI",
                    "recipient": "SAGE::C2::CHATGPT",
                    "event_type": "AGENT_CHALLENGE",
                    "delivery_state": "PENDING",
                }
            ],
            "delivery_semantics": "pull_projection_only",
        },
    }


def test_hud_projects_nameplates_progression_state_and_activity():
    projection = build_agent_hud_projection(context_view=_context())

    assert projection["presentation_only"] is True
    assert projection["self"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert projection["self"]["cql"] == 1
    assert projection["self"]["sql"] == 1
    assert projection["self"]["xp"] == 100
    assert projection["self"]["state"] == "WORKING"
    assert projection["team"]["roster"][1]["nameplate"] == "[SAGE::INTEL::GEMINI]"
    assert projection["team"]["roster"][1]["state"] == "RECON"
    assert projection["coordination"]["pending_count"] == 1
    assert projection["coordination"]["pending"][0]["delivery_state"] == "PENDING"


def test_hud_isolation_prevents_context_mutation():
    context = _context()
    projection = build_agent_hud_projection(context_view=context)

    projection["self"]["xp"] = 999999
    projection["team"]["roster"][0]["state"] = "COMPROMISED"
    projection["coordination"]["pending"][0]["delivery_state"] = "DELIVERED"

    assert context["self"]["xp"] == 100
    assert context["team"]["stations"]["MISSION_CONTROL"]["state"] == "WORKING"
    assert context["coordination"]["pending"][0]["delivery_state"] == "PENDING"


def test_hud_rejects_unbounded_or_writable_sources():
    context = _context()

    context["bounded"] = False
    try:
        build_agent_hud_projection(context_view=context)
        raise AssertionError("unbounded context must fail closed")
    except ValueError as exc:
        assert "bounded" in str(exc)

    context = _context()
    context["read_only"] = False
    try:
        build_agent_hud_projection(context_view=context)
        raise AssertionError("writable context must fail closed")
    except ValueError as exc:
        assert "read-only" in str(exc)


def test_render_is_human_readable_and_provenance_preserving():
    ctx = _context()
    ctx["self"]["milestone_strike"] = "⚡ 3/5"
    ctx["self"]["safe_impact_stars"] = 3
    projection = build_agent_hud_projection(context_view=ctx)
    rendered = render_agent_hud(projection)

    assert "[SAGE::C2::CHATGPT]" in rendered
    assert "CQL-1/SQL-1 XP-100 STRIKE=⚡ 3/5 STARS=⭐⭐⭐ STATE=WORKING" in rendered
    assert "[SAGE::INTEL::GEMINI]:RECON" in rendered
    assert "PENDING=1" in rendered
