"""Out-of-sample calibration and market-edge evaluation for shadow predictions."""

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
    resolved_count: int


def score_predictions(
    predictions: Iterable[PredictionRecord], outcomes: Mapping[str, int]
) -> EvaluationResult:
    records = [p for p in predictions if p.event_id in outcomes and p.verify_lock() and p.is_oos]
    if not records:
        return EvaluationResult("unknown", 0, None, None, None, None, 0)

    brier = []
    market_brier = []
    log_losses = []
    errors = []
    for record in records:
        outcome = float(outcomes[record.event_id])
        p = min(1.0 - 1e-15, max(1e-15, record.predicted_probability))
        market = min(1.0 - 1e-15, max(1e-15, record.market_probability))
        brier.append((p - outcome) ** 2)
        market_brier.append((market - outcome) ** 2)
        log_losses.append(-(outcome * math.log(p) + (1.0 - outcome) * math.log(1.0 - p)))
        errors.append(abs(p - outcome))

    return EvaluationResult(
        model_version=records[0].model_version,
        sample_count=len(records),
        brier_score=sum(brier) / len(brier),
        log_loss=sum(log_losses) / len(log_losses),
        market_brier_score=sum(market_brier) / len(market_brier),
        mean_probability_error=sum(errors) / len(errors),
        resolved_count=len(records),
    )
