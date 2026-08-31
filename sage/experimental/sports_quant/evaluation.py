"""Out-of-sample calibration, closing line value (CLV), EV, and market-edge evaluation for shadow predictions."""

from dataclasses import dataclass
import math
from typing import Iterable, Mapping

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
    expected_value_ev: float | None
    resolved_count: int


def calculate_ev(
    predicted_probability: float,
    decimal_odds: float,
) -> float:
    """Calculate Expected Value (EV) given model predicted probability and decimal price."""
    if decimal_odds <= 0.0 or predicted_probability < 0.0 or predicted_probability > 1.0:
        return 0.0
    # EV = (p * (odds - 1)) - ((1 - p) * 1) = p * odds - 1
    return (predicted_probability * decimal_odds) - 1.0


def calculate_clv(
    predicted_probability: float,
    closing_market_probability: float,
) -> float:
    """Calculate Closing Line Value (CLV) as log-ratio or difference of probabilities."""
    if closing_market_probability <= 0.0 or closing_market_probability >= 1.0:
        return 0.0
    # Expected edge relative to closing market
    return predicted_probability - closing_market_probability


def score_predictions(
    predictions: Iterable[PredictionRecord],
    outcomes: Mapping[str, int],
    closing_prices: Mapping[str, float] | None = None,
    decimal_odds_map: Mapping[str, float] | None = None,
) -> EvaluationResult:
    records = [p for p in predictions if p.event_id in outcomes and p.verify_lock() and p.is_oos]
    if not records:
        return EvaluationResult("unknown", 0, None, None, None, None, None, None, 0)

    brier = []
    market_brier = []
    log_losses = []
    errors = []
    clvs = []
    evs = []

    for record in records:
        outcome = float(outcomes[record.event_id])
        p = min(1.0 - 1e-15, max(1e-15, record.predicted_probability))
        market = min(1.0 - 1e-15, max(1e-15, record.market_probability))
        brier.append((p - outcome) ** 2)
        market_brier.append((market - outcome) ** 2)
        log_losses.append(-(outcome * math.log(p) + (1.0 - outcome) * math.log(1.0 - p)))
        errors.append(abs(p - outcome))

        if closing_prices and record.event_id in closing_prices:
            closing_prob = closing_prices[record.event_id]
            clvs.append(calculate_clv(p, closing_prob))

        if decimal_odds_map and record.event_id in decimal_odds_map:
            odds = decimal_odds_map[record.event_id]
            evs.append(calculate_ev(p, odds))

    mean_clv = sum(clvs) / len(clvs) if clvs else None
    mean_ev = sum(evs) / len(evs) if evs else None

    return EvaluationResult(
        model_version=records[0].model_version,
        sample_count=len(records),
        brier_score=sum(brier) / len(brier),
        log_loss=sum(log_losses) / len(log_losses),
        market_brier_score=sum(market_brier) / len(market_brier),
        mean_probability_error=sum(errors) / len(errors),
        clv_score=mean_clv,
        expected_value_ev=mean_ev,
        resolved_count=len(records),
    )
