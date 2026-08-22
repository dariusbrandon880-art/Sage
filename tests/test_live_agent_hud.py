import pytest

from sage import live_agent_hud


def _awareness(agent_id):
    return {
        "read_only": True,
        "authority": "canonical_airspace_state_and_event_ledger",
        "self": {"nameplate": "[SAGE::C2::CHATGPT]", "cql": 2, "sql": 1, "xp": 120, "state": "WORKING"},
        "team": {"coordination": {"status": "ACTIVE"}, "stations": {}},
        "coordination": {"pending": [], "delivery_semantics": "pull_projection_only"},
        "agent_id": agent_id,
    }


def test_live_hud_closes_awareness_context_hud_chain(monkeypatch):
    monkeypatch.setattr(live_agent_hud, "get_live_agent_awareness_snapshot", _awareness)

    projection = live_agent_hud.get_live_agent_hud("MISSION_CONTROL", context_id="flight-1")

    assert projection["context_id"] == "flight-1"
    assert projection["audience"] == "SAGE::C2::CHATGPT"
    assert projection["presentation_only"] is True
    assert projection["read_only"] is True
    assert projection["self"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert projection["self"]["xp"] == 120


def test_live_hud_rejects_unknown_agent(monkeypatch):
    monkeypatch.setattr(live_agent_hud, "get_live_agent_awareness_snapshot", _awareness)

    with pytest.raises(ValueError, match="unsupported agent_id"):
        live_agent_hud.get_live_agent_hud("UNKNOWN")


def test_live_hud_render_preserves_identity_and_progression(monkeypatch):
    monkeypatch.setattr(live_agent_hud, "get_live_agent_awareness_snapshot", _awareness)

    rendered = live_agent_hud.render_live_agent_hud("MISSION_CONTROL", context_id="flight-2")

    assert "[SAGE::C2::CHATGPT]" in rendered
    assert "CQL-2/SQL-1 XP-120 STATE=WORKING" in rendered
