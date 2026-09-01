from pathlib import Path

from sage.c2.capability_graph import CapabilityGraphEngine


def test_discovers_executable_surfaces_with_exact_head():
    graph = CapabilityGraphEngine(".").discover("a" * 40)
    assert graph.exact_git_head == "a" * 40
    assert graph.nodes
    assert graph.digest
    assert all(node.path.endswith(".py") for node in graph.nodes)


def test_discovers_multiple_capability_surfaces():
    graph = CapabilityGraphEngine(".").discover("b" * 40)
    surfaces = {node.surface for node in graph.nodes}
    assert "C2" in surfaces
    assert len(surfaces) >= 3


def test_mission_ranking_prefers_distinct_surfaces():
    graph = CapabilityGraphEngine(".").discover("c" * 40)
    missions = CapabilityGraphEngine(".").rank_missions(graph, limit=8)
    assert missions
    assert len(missions) == min(8, len(missions))
    assert len({mission.surface for mission in missions}) == len(missions)
    assert all(mission.before and mission.after for mission in missions)


def test_invalid_limit_fails_closed():
    graph = CapabilityGraphEngine(".").discover("d" * 40)
    try:
        CapabilityGraphEngine(".").rank_missions(graph, limit=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected invalid mission limit to fail closed")
