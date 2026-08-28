from fastapi.testclient import TestClient

from sage.experimental.observatory import server


EXPECTED_NAMEPLATES = (
    "[SAGE::DIRECTOR]",
    "[SAGE::C2::CHATGPT]",
    "[SAGE::INTEL::GEMINI]",
    "[SAGE::ENGINEER::JULES]",
)


def _sample_hud():
    roster = [
        {"nameplate": name, "agent_name": name, "role": "role", "cql": 1, "sql": 1, "xp": 0, "state": "STANDBY"}
        for name in EXPECTED_NAMEPLATES
    ]
    return {
        "self": roster[1],
        "team": {"coordination_status": "READY", "roster": roster},
        "coordination": {"pending_count": 0, "pending": [], "delivery_semantics": "read_only"},
    }


def test_observatory_exposes_live_canonical_hud(monkeypatch):
    monkeypatch.setattr(server, "get_live_agent_hud", lambda agent_id="MISSION_CONTROL": _sample_hud())
    response = TestClient(server.app).get("/api/hud?agent_id=MISSION_CONTROL")
    assert response.status_code == 200
    payload = response.json()
    assert [item["nameplate"] for item in payload["team"]["roster"]] == list(EXPECTED_NAMEPLATES)
    assert payload["self"]["nameplate"] == "[SAGE::C2::CHATGPT]"


def test_observatory_dashboard_consumes_hud_and_renders_nameplate_surface():
    response = TestClient(server.app).get("/")
    assert response.status_code == 200
    body = response.text
    assert "/api/hud?agent_id=MISSION_CONTROL" in body
    assert "LIVE AGENT NAMEPLATES" in body
    assert "canonical identity" in body
    assert "hud.team?.roster" in body
