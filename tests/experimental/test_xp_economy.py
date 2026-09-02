import pytest

from sage.experimental.airspace.xp_economy import (
    XPEvent,
    accumulate_xp,
    build_xp_event,
    points_to_xp,
)


def test_points_to_xp_uses_ten_to_one_ratio() -> None:
    assert points_to_xp(1) == 10
    assert points_to_xp(5) == 50
    assert points_to_xp(25) == 250
    assert points_to_xp(500) == 5000


def test_conversion_is_deterministic() -> None:
    assert [points_to_xp(25) for _ in range(100)] == [250] * 100


def test_negative_points_are_rejected() -> None:
    with pytest.raises(ValueError):
        points_to_xp(-1)


def test_non_integer_points_are_rejected() -> None:
    with pytest.raises(TypeError):
        points_to_xp(1.5)  # type: ignore[arg-type]


def test_xp_event_preserves_agent_and_event_lineage() -> None:
    event = build_xp_event("mission-847", "jules", 25)
    assert event == XPEvent(
        event_id="mission-847",
        agent_id="jules",
        verified_points=25,
        xp_awarded=250,
    )


def test_lifetime_xp_is_the_sum_of_verified_events() -> None:
    events = [
        build_xp_event("a", "jules", 10),
        build_xp_event("b", "gemini", 25),
        build_xp_event("c", "chatgpt", 5),
    ]
    assert accumulate_xp(events) == 400


def test_event_identity_and_agent_are_required() -> None:
    with pytest.raises(ValueError):
        build_xp_event("", "jules", 1)
    with pytest.raises(ValueError):
        build_xp_event("a", "", 1)
