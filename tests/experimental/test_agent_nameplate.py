from sage.experimental.agent_nameplate import build_default_c2_nameplate, build_nameplate
from sage.experimental.agent_progression import AgentProgression


def test_default_c2_nameplate_fails_closed_to_lowest_rank():
    badge = build_default_c2_nameplate()
    assert badge.agent_id == "agent_c2"
    assert badge.display_name == "C2"
    assert badge.station == "Mission Control / C2"
    assert badge.rank == "CQL-0"
    assert badge.xp == 0
    assert badge.missions == 0
    assert badge.status == "ACTIVE"


def test_nameplate_tracks_verified_progression_state():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control / C2")
    badge = build_nameplate(agent, display_name="C2", status="READY")
    assert badge.as_dict() == {
        "agent_id": "agent_c2",
        "display_name": "C2",
        "station": "Mission Control / C2",
        "rank": "CQL-0",
        "xp": 0,
        "missions": 0,
        "status": "READY",
    }
    assert badge.compact() == "[C2 · CQL-0 · 0 XP · Mission Control / C2 · READY]"


def test_nameplate_does_not_create_progression():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control / C2")
    before = agent.canonical_digest()
    badge = build_nameplate(agent, display_name="C2")
    after = agent.canonical_digest()
    assert badge.xp == 0
    assert before == after
