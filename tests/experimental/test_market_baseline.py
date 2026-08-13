"""Unit and regression tests for SAGE Market Baseline and De-vigging Engine.

Enforces validation of SAGE-RF-DEVIG-001 specification.
"""

import pytest
from sage.experimental.market_baseline import MarketBaselineEngine


def test_odds_conversion_and_overround():
    """Verify American to decimal odds conversion and overround calculation."""
    p1 = MarketBaselineEngine.american_to_decimal(-110)
    assert abs(p1 - 1.90909) < 1e-4

    p2 = MarketBaselineEngine.american_to_decimal(150)
    assert p2 == 2.50

    overround = MarketBaselineEngine.calculate_overround([p1, p1])
    assert abs(overround - 1.0476) < 1e-3


def test_devig_proportional():
    """Verify multiplicative/proportional devigging."""
    prices = {"home": 1.83, "away": 2.0}
    fair_probs, overround = MarketBaselineEngine.devig_proportional(prices)

    assert abs(sum(fair_probs.values()) - 1.0) < 1e-9
    assert overround > 1.0
    assert abs(overround - 1.046448) < 1e-4


def test_devig_equal_distribution():
    """Verify equal distribution devigging."""
    prices = {"home": 1.83, "away": 2.0}
    fair_probs, overround = MarketBaselineEngine.devig_equal_distribution(prices)

    assert abs(sum(fair_probs.values()) - 1.0) < 1e-9
    assert overround > 1.0


def test_devig_power_method():
    """Verify Newton-Raphson power method devigging and exponent convergence."""
    prices = {"home": 1.50, "away": 3.0}
    fair_probs, overround = MarketBaselineEngine.devig_power_method(prices)
    assert abs(fair_probs["home"] - 0.66666) < 1e-3
    assert abs(fair_probs["away"] - 0.33333) < 1e-3

    prices_overround = {
        "home": MarketBaselineEngine.american_to_decimal(-110),
        "away": MarketBaselineEngine.american_to_decimal(-110)
    }
    fair_probs_over, overround_over = MarketBaselineEngine.devig_power_method(prices_overround)
    assert abs(sum(fair_probs_over.values()) - 1.0) < 1e-9
    assert abs(fair_probs_over["home"] - 0.5) < 1e-9


def test_invalid_overround_fails_closed():
    """Verify that an overround < 1.0 fails closed, triggering stale/conflict errors."""
    invalid_prices = {"home": 2.10, "away": 2.10}  # Overround < 1.0

    with pytest.raises(ValueError) as exc_info:
        MarketBaselineEngine.devig_proportional(invalid_prices)
    assert "Invalid overround" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        MarketBaselineEngine.devig_equal_distribution(invalid_prices)
    assert "Invalid overround" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        MarketBaselineEngine.devig_power_method(invalid_prices)
    assert "Invalid overround" in str(exc_info.value)
