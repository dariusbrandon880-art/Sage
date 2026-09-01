"""Out-of-sample calibration and market-edge evaluation for shadow predictions."""

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Iterable, Mapping

if TYPE_CHECKING:
    from .prediction import PredictionRecord


@dataclass(frozen=True)
class EvaluationResult:
    model_version: str
    sample_count: int
    brier_score: float | None
    log_loss: float | None
    market_brier_score: float | None
    mean_probability_error: float | None
    clv_score: float | None
    mean_market_edge: float | None
    resolved_count: int


def calculate_ev(win_probability: float, decimal_odds: float) -> float:
    """Calculate Expected Value (EV) fraction per unit wagered.

    EV = (p * decimal_odds) - 1
    """
    if not 0.0 <= win_probability <= 1.0:
        raise ValueError("INVALID_PROBABILITY: win_probability must be between 0 and 1")
    if decimal_odds <= 0.0:
        raise ValueError("INVALID_ODDS: decimal_odds must be positive")
    return (win_probability * decimal_odds) - 1.0


def calculate_kelly_stake(
    win_probability: float,
    decimal_odds: float,
    fraction: float = 0.25,
    max_stake_cap: float = 0.05,
    wagering_executed: bool = False,
) -> float:
    """Calculate fractional Kelly stake recommendation under strict zero-wagering bounds."""
    if wagering_executed:
        raise ValueError("SHADOW_BOUNDARY_VIOLATION: wagering execution is prohibited")
    if not 0.0 <= win_probability <= 1.0:
        raise ValueError("INVALID_PROBABILITY")
    if decimal_odds <= 1.0:
        return 0.0

    b = decimal_odds - 1.0
    q = 1.0 - win_probability
    raw_kelly = (win_probability * b - q) / b
    if raw_kelly <= 0.0:
        return 0.0

    suggested_stake = raw_kelly * fraction
    return min(suggested_stake, max_stake_cap)


def calculate_clv(predicted_probability: float, closing_market_probability: float) -> float:
    """Return model probability edge versus the closing market probability."""
    return predicted_probability - closing_market_probability


def score_predictions(
    predictions: Iterable["PredictionRecord"], outcomes: Mapping[str, int]
) -> EvaluationResult:
    records = [p for p in predictions if p.event_id in outcomes and p.verify_lock() and p.is_oos]
    if not records:
        return EvaluationResult("unknown", 0, None, None, None, None, None, None, 0)

    brier = []
    market_brier = []
    log_losses = []
    errors = []
    clv = []
    for record in records:
        outcome = float(outcomes[record.event_id])
        p = min(1.0 - 1e-15, max(1e-15, record.predicted_probability))
        market = min(1.0 - 1e-15, max(1e-15, record.market_probability))
        brier.append((p - outcome) ** 2)
        market_brier.append((market - outcome) ** 2)
        log_losses.append(-(outcome * math.log(p) + (1.0 - outcome) * math.log(1.0 - p)))
        errors.append(abs(p - outcome))
        clv.append(calculate_clv(p, market))

    return EvaluationResult(
        model_version=records[0].model_version,
        sample_count=len(records),
        brier_score=sum(brier) / len(brier),
        log_loss=sum(log_losses) / len(log_losses),
        market_brier_score=sum(market_brier) / len(market_brier),
        mean_probability_error=sum(errors) / len(errors),
        clv_score=sum(clv) / len(clv),
        mean_market_edge=sum(clv) / len(clv),
        resolved_count=len(records),
    )
