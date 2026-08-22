from sage.agent_awareness import AWARENESS_VERSION, CANONICAL_AUTHORITY, build_agent_awareness_snapshot, get_agent_awareness_snapshot


def _identity(agent_id):
    return {
        "nameplate": "[SAGE::C2::CHATGPT]",
        "station_id": agent_id,
        "agent_name": "GPT",
        "role": "Mission Control",
        "cql": 1,
        "sql": 1,
        "xp": 100,
        "state": "WORKING",
        "read_only": True,
        "authority": "canonical_airspace_state",
    }


def _team():
    return {
        "stations": {
            "MISSION_CONTROL": _identity("MISSION_CONTROL"),
            "INTEL_STATION": {
                "nameplate": "[SAGE::INTEL::GEMINI]",
                "station_id": "INTEL_STATION",
                "cql": 1,
                "sql": 1,
                "xp": 80,
                "state": "RECON",
                "read_only": True,
            },
            "ENGINEERING_FLIGHT": {
                "nameplate": "[SAGE::ENGINEER::JULES]",
                "station_id": "ENGINEERING_FLIGHT",
                "cql": 1,
                "sql": 1,
                "xp": 90,
                "state": "STANDBY",
                "read_only": True,
            },
        },
        "coordination": {"status": "ACTIVE"},
        "read_only": True,
        "authority": "canonical_airspace_state",
    }


def _event():
    return {
        "envelope_version": "agent-context-envelope-v0.1",
        "sender": "SAGE::INTEL::GEMINI",
        "recipient": "SAGE::C2::CHATGPT",
        "event_id": "evt-1",
        "event_type": "AGENT_CHALLENGE",
        "delivery_state": "PENDING",
        "delivery_semantics": "pull_projection_only",
        "read_only": True,
        "authority": CANONICAL_AUTHORITY,
        "payload": {"challenge": "test"},
    }


def test_snapshot_projects_self_team_and_pending_coordination():
    snapshot = build_agent_awareness_snapshot(
        agent_id="MISSION_CONTROL",
        identity=_identity("MISSION_CONTROL"),
        team_context=_team(),
        unread_coordination=[_event()],
    )

    assert snapshot["awareness_version"] == AWARENESS_VERSION
    assert snapshot["self"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert snapshot["team"]["stations"]["INTEL_STATION"]["nameplate"] == "[SAGE::INTEL::GEMINI]"
    assert snapshot["team"]["stations"]["ENGINEERING_FLIGHT"]["xp"] == 90
    assert snapshot["coordination"]["pending"][0]["sender"] == "SAGE::INTEL::GEMINI"
    assert snapshot["coordination"]["pending"][0]["delivery_state"] == "PENDING"
    assert snapshot["coordination"]["delivery_semantics"] == "pull_projection_only"
    assert snapshot["read_only"] is True
    assert snapshot["authority"] == CANONICAL_AUTHORITY


def test_snapshot_isolation_prevents_input_mutation():
    identity = _identity("MISSION_CONTROL")
    team = _team()
    events = [_event()]

    snapshot = build_agent_awareness_snapshot(
        agent_id="MISSION_CONTROL",
        identity=identity,
        team_context=team,
        unread_coordination=events,
    )
    snapshot["self"]["xp"] = 999999
    snapshot["team"]["stations"]["INTEL_STATION"]["xp"] = 999999
    snapshot["coordination"]["pending"][0]["payload"]["challenge"] = "mutated"

    assert identity["xp"] == 100
    assert team["stations"]["INTEL_STATION"]["xp"] == 80
    assert events[0]["payload"]["challenge"] == "test"


def test_provider_composition_is_deterministic_and_read_only():
    snapshot = get_agent_awareness_snapshot(
        "MISSION_CONTROL",
        identity_provider=_identity,
        team_provider=_team,
        unread_provider=lambda _agent: [_event()],
    )

    assert snapshot == get_agent_awareness_snapshot(
        "MISSION_CONTROL",
        identity_provider=_identity,
        team_provider=_team,
        unread_provider=lambda _agent: [_event()],
    )
    assert snapshot["read_only"] is True
    assert snapshot["self"]["authority"] == "canonical_airspace_state"


def test_invalid_agent_id_fails_closed():
    try:
        build_agent_awareness_snapshot(
            agent_id="",
            identity=_identity("MISSION_CONTROL"),
            team_context=_team(),
            unread_coordination=[],
        )
    except ValueError as exc:
        assert "agent_id" in str(exc)
    else:
        raise AssertionError("empty agent_id was accepted")
