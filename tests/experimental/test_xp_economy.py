from decimal import Decimal

import pytest

from sage.experimental.airspace.models import GameProgression, StationID, XPCategory
from sage.experimental.airspace.xp_economy import (
    XPEvent,
    accumulate_xp,
    award_verified_points,
    build_xp_event,
    points_to_xp,
)


def test_points_to_xp_uses_100_points_to_10_xp_ratio() -> None:
    assert points_to_xp(1) == Decimal("0.1")
    assert points_to_xp(5) == Decimal("0.5")
    assert points_to_xp(10) == Decimal("1")
    assert points_to_xp(25) == Decimal("2.5")
    assert points_to_xp(100) == Decimal("10")
    assert points_to_xp(500) == Decimal("50")


def test_conversion_is_deterministic() -> None:
    assert [points_to_xp(25) for _ in range(100)] == [Decimal("2.5")] * 100


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
        xp_awarded=Decimal("2.5"),
    )


def test_lifetime_xp_is_the_sum_of_verified_events() -> None:
    events = [
        build_xp_event("a", "jules", 10),
        build_xp_event("b", "gemini", 25),
        build_xp_event("c", "chatgpt", 5),
    ]
    assert accumulate_xp(events) == Decimal("4")


def test_event_identity_and_agent_are_required() -> None:
    with pytest.raises(ValueError):
        build_xp_event("", "jules", 1)
    with pytest.raises(ValueError):
        build_xp_event("a", "", 1)


def test_verified_points_route_whole_xp_into_canonical_game_progression() -> None:
    progression = GameProgression()
    event = award_verified_points(
        progression=progression,
        station_id=StationID.ENGINEERING_FLIGHT,
        verified_points=100,
        category=XPCategory.ENGINEERING_FLIGHT_XP,
        reason="Verified Queue #03 capability work",
        verified_event_ref="mission-847",
    )

    assert event.amount == 10
    assert event.station_id == StationID.ENGINEERING_FLIGHT
    assert event.verified_event_ref == "mission-847"
    assert progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT) == 10
    assert len(progression.xp_events) == 1


def test_fractional_xp_is_not_silently_rounded_in_canonical_adapter() -> None:
    progression = GameProgression()
    with pytest.raises(ValueError, match="whole XP"):
        award_verified_points(
            progression=progression,
            station_id=StationID.ENGINEERING_FLIGHT,
            verified_points=25,
            category=XPCategory.ENGINEERING_FLIGHT_XP,
            reason="Verified Queue #03 fractional conversion",
            verified_event_ref="mission-848",
        )
