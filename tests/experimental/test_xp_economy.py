from decimal import Decimal

import pytest

from sage.experimental.airspace.xp_economy import accumulate_xp, build_xp_event, points_to_xp


def test_points_to_xp_uses_exact_decimal_conversion():
    assert points_to_xp(1) == Decimal("0.1")
    assert points_to_xp(25) == Decimal("2.5")
    assert points_to_xp(100) == Decimal("10.0")


def test_conversion_receipts_are_lossless():
    events = [build_xp_event("e1", "GPT", 1), build_xp_event("e2", "GPT", 9)]
    assert accumulate_xp(events) == Decimal("1.0")


def test_negative_points_are_rejected():
    with pytest.raises(ValueError):
        points_to_xp(-1)


def test_bool_is_not_a_point_count():
    with pytest.raises(TypeError):
        points_to_xp(True)
