from sage.governed_context_view import (
    CONTEXT_VIEW_VERSION,
    build_governed_context_view,
)


def _awareness():
    return {
        "awareness_version": "agent-awareness-v0.1",
        "agent_id": "MISSION_CONTROL",
        "self": {
            "nameplate": "[SAGE::C2::CHATGPT]",
            "cql": 1,
            "sql": 1,
            "xp": 100,
            "state": "WORKING",
        },
        "team": {
            "stations": {
                "MISSION_CONTROL": {"nameplate": "[SAGE::C2::CHATGPT]", "xp": 100},
                "INTEL_STATION": {"nameplate": "[SAGE::INTEL::GEMINI]", "xp": 80},
                "ENGINEERING_FLIGHT": {"nameplate": "[SAGE::ENGINEER::JULES]", "xp": 90},
            }
        },
        "coordination": {
            "pending": [
                {"event_id": "evt-1", "sender": "SAGE::INTEL::GEMINI", "delivery_state": "PENDING"},
                {"event_id": "evt-2", "sender": "SAGE::ENGINEER::JULES", "delivery_state": "PENDING"},
            ],
            "delivery_semantics": "pull_projection_only",
        },
        "read_only": True,
        "authority": "canonical_airspace_state_and_event_ledger",
    }


def test_team_coordination_view_is_explicit_and_bounded():
    view = build_governed_context_view(
        awareness=_awareness(),
        audience="SAGE::C2::CHATGPT",
        purpose="COORDINATION",
        context_id="ctx-001",
        max_pending=1,
    )

    assert view["context_view_version"] == CONTEXT_VIEW_VERSION
    assert view["audience"] == "SAGE::C2::CHATGPT"
    assert view["purpose"] == "COORDINATION"
    assert view["bounded"] is True
    assert view["read_only"] is True
    assert len(view["coordination"]["pending"]) == 1
    assert view["coordination"]["pending"][0]["event_id"] == "evt-1"
    assert view["authority"] == "canonical_airspace_state_and_event_ledger"


def test_self_profile_excludes_team_and_pending_coordination():
    view = build_governed_context_view(
        awareness=_awareness(),
        audience="SAGE::C2::CHATGPT",
        purpose="HUD",
        context_id="ctx-self",
        profile="SELF",
    )

    assert view["self"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert view["team"] == {}
    assert view["coordination"]["pending"] == []


def test_team_profile_excludes_pending_coordination():
    view = build_governed_context_view(
        awareness=_awareness(),
        audience="SAGE::DIRECTOR",
        purpose="HUD",
        context_id="ctx-team",
        profile="TEAM",
    )

    assert "INTEL_STATION" in view["team"]["stations"]
    assert view["coordination"]["pending"] == []


def test_source_must_be_read_only():
    awareness = _awareness()
    awareness["read_only"] = False

    try:
        build_governed_context_view(
            awareness=awareness,
            audience="SAGE::DIRECTOR",
            purpose="HUD",
            context_id="ctx-locked",
        )
    except ValueError as exc:
        assert "read-only" in str(exc)
    else:
        raise AssertionError("mutable awareness source was accepted")


def test_invalid_context_controls_fail_closed():
    cases = [
        {"audience": "", "purpose": "HUD", "context_id": "ctx"},
        {"audience": "UNTRUSTED", "purpose": "HUD", "context_id": "ctx"},
        {"audience": "SAGE::DIRECTOR", "purpose": "UNKNOWN", "context_id": "ctx"},
        {"audience": "SAGE::DIRECTOR", "purpose": "HUD", "context_id": ""},
        {"audience": "SAGE::DIRECTOR", "purpose": "HUD", "context_id": "ctx", "max_pending": -1},
        {"audience": "SAGE::DIRECTOR", "purpose": "HUD", "context_id": "ctx", "profile": "UNKNOWN"},
    ]

    for case in cases:
        try:
            build_governed_context_view(awareness=_awareness(), **case)
        except ValueError:
            continue
        raise AssertionError(f"invalid context control accepted: {case}")


def test_unsupported_awareness_authority_fails_closed():
    awareness = _awareness()
    awareness["authority"] = "external_provider"

    try:
        build_governed_context_view(
            awareness=awareness,
            audience="SAGE::DIRECTOR",
            purpose="HUD",
            context_id="ctx-authority",
        )
    except ValueError as exc:
        assert "authority" in str(exc)
    else:
        raise AssertionError("unsupported awareness authority was accepted")


def test_missing_awareness_authority_fails_closed():
    awareness = _awareness()
    del awareness["authority"]

    try:
        build_governed_context_view(
            awareness=awareness,
            audience="SAGE::DIRECTOR",
            purpose="HUD",
            context_id="ctx-missing-authority",
        )
    except ValueError as exc:
        assert "canonical authority" in str(exc)
    else:
        raise AssertionError("missing awareness authority was accepted")


def test_projection_does_not_mutate_awareness():
    awareness = _awareness()
    view = build_governed_context_view(
        awareness=awareness,
        audience="SAGE::C2::CHATGPT",
        purpose="VERIFICATION",
        context_id="ctx-copy",
    )
    view["self"]["xp"] = 999999
    view["coordination"]["pending"][0]["event_id"] = "tampered"

    assert awareness["self"]["xp"] == 100
    assert awareness["coordination"]["pending"][0]["event_id"] == "evt-1"
