"""SAGE Sports-Probability Scientific Research - Market Baseline and De-vigging Engine.

Implements the SAGE-RF-DEVIG-001 specification:
Reconstructs fair baseline probabilities (P_market) from sportsbook price observations
using mathematically rigorous de-vigging models.
"""

from typing import Dict, List, Any, Tuple
import math


class MarketBaselineEngine:
    """Rigorous de-vigging engine to compute fair market baseline probabilities from sportsbook prices."""

    @staticmethod
    def american_to_decimal(american_price: float) -> float:
        """Converts American odds (e.g. +150, -110) to decimal price format."""
        if american_price == 0:
            raise ValueError("American odds cannot be zero.")
        if american_price > 0:
            return (american_price / 100.0) + 1.0
        else:
            return (100.0 / abs(american_price)) + 1.0

    @classmethod
    def calculate_overround(cls, decimal_prices: List[float]) -> float:
        """Computes the total sportsbook overround/margin from a list of decimal prices."""
        if not decimal_prices:
            return 0.0
        return sum(1.0 / p for p in decimal_prices)

    @classmethod
    def devig_proportional(cls, decimal_prices: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        """Proportional/Multiplicative De-vigging Method.

        Distributes sportsbook margin proportionally based on implied probabilities.
        """
        overround = cls.calculate_overround(list(decimal_prices.values()))
        if overround < 1.0:
            raise ValueError(f"STALE/CONFLICTED PROJECTION: Invalid overround {overround:.4f}. Must be >= 1.0.")

        fair_probabilities = {}
        for selection, price in decimal_prices.items():
            implied = 1.0 / price
            # If overround is exactly 1.0, prob is just implied
            fair_probabilities[selection] = implied / overround if overround > 1.0 else implied

        return fair_probabilities, overround

    @classmethod
    def devig_equal_distribution(cls, decimal_prices: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        """Equal Distribution / Additive De-vigging Method.

        Distributes sportsbook overround equally across all market selections.
        """
        n = len(decimal_prices)
        overround = cls.calculate_overround(list(decimal_prices.values()))
        if overround < 1.0:
            raise ValueError(f"STALE/CONFLICTED PROJECTION: Invalid overround {overround:.4f}. Must be >= 1.0.")

        if abs(overround - 1.0) < 1e-6:
            fair_probs = {sel: 1.0 / p for sel, p in decimal_prices.items()}
            return fair_probs, overround

        margin = overround - 1.0
        margin_per_selection = margin / n

        fair_probabilities = {}
        for selection, price in decimal_prices.items():
            implied = 1.0 / price
            fair_prob = implied - margin_per_selection
            fair_probabilities[selection] = max(0.0, fair_prob)

        total_p = sum(fair_probabilities.values())
        if total_p > 0:
            for selection in fair_probabilities:
                fair_probabilities[selection] /= total_p

        return fair_probabilities, overround

    @classmethod
    def devig_power_method(cls, decimal_prices: Dict[str, float], tolerance: float = 1e-9, max_iter: int = 100) -> Tuple[Dict[str, float], float]:
        """Power / Shin-like De-vigging Method.

        Solves for an exponent 'k' such that sum((1/price)^k) = 1.0.
        Highly accurate and recommended for markets with wide price discrepancies.
        """
        prices = list(decimal_prices.values())
        overround = cls.calculate_overround(prices)
        if overround < 1.0:
            raise ValueError(f"STALE/CONFLICTED PROJECTION: Invalid overround {overround:.4f}. Must be >= 1.0.")

        # If overround is very close to 1.0, k is approximately 1.0
        if abs(overround - 1.0) < 1e-6:
            fair_probs = {sel: 1.0 / p for sel, p in decimal_prices.items()}
            return fair_probs, overround

        # Solve for k using Newton-Raphson
        k = 1.1  # Initial guess
        for _ in range(max_iter):
            f_val = sum(math.pow(1.0 / p, k) for p in prices) - 1.0
            f_prime = sum(math.log(1.0 / p) * math.pow(1.0 / p, k) for p in prices)
            if abs(f_prime) < 1e-12:
                break
            next_k = k - (f_val / f_prime)
            if abs(next_k - k) < tolerance:
                k = next_k
                break
            k = next_k

        fair_probabilities = {}
        for selection, price in decimal_prices.items():
            fair_probabilities[selection] = math.pow(1.0 / price, k)

        total_p = sum(fair_probabilities.values())
        for selection in fair_probabilities:
            fair_probabilities[selection] /= total_p

        return fair_probabilities, overround
