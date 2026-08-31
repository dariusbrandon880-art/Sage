"""Failure diagnostics and governed candidate-strategy promotion gates."""

from dataclasses import dataclass
from typing import Iterable, Mapping

from .prediction import PredictionRecord
from .evaluation import EvaluationResult, score_predictions


@dataclass(frozen=True)
class FailureCluster:
    model_version: str
    event_ids: tuple[str, ...]
    selections: tuple[str, ...]
    mean_abs_error: float
    tags: tuple[str, ...]


def build_failure_clusters(
    predictions: Iterable[PredictionRecord],
    outcomes: Mapping[str, int],
    error_threshold: float = 0.35,
) -> list[FailureCluster]:
    failures = [
        p for p in predictions
        if p.event_id in outcomes
        and p.verify_lock()
        and abs(p.predicted_probability - float(outcomes[p.event_id])) > error_threshold
    ]
    by_version: dict[str, list[PredictionRecord]] = {}
    for record in failures:
        by_version.setdefault(record.model_version, []).append(record)

    clusters: list[FailureCluster] = []
    for version, records in sorted(by_version.items()):
        tags = []
        if any(record.predicted_probability >= 0.75 and outcomes[record.event_id] == 0 for record in records):
            tags.append("HIGH_CONFIDENCE_MISS")
        if any(record.predicted_probability <= 0.25 and outcomes[record.event_id] == 1 for record in records):
            tags.append("LOW_CONFIDENCE_MISS")
        clusters.append(
            FailureCluster(
                model_version=version,
                event_ids=tuple(sorted({record.event_id for record in records})),
                selections=tuple(sorted({record.selection for record in records})),
                mean_abs_error=sum(abs(r.predicted_probability - float(outcomes[r.event_id])) for r in records) / len(records),
                tags=tuple(tags) or ("CALIBRATION_MISS",),
            )
        )
    return clusters


def validate_oos_candidate(
    candidate: Iterable[PredictionRecord],
    baseline: Iterable[PredictionRecord],
    outcomes: Mapping[str, int],
    min_sample_size: int = 30,
) -> tuple[bool, EvaluationResult, EvaluationResult]:
    """Allow promotion only after sufficiently large common OOS evidence and strict improvement."""
    candidate_records = [p for p in candidate if p.is_oos and p.verify_lock()]
    baseline_records = [p for p in baseline if p.is_oos and p.verify_lock()]
    candidate_events = {p.event_id for p in candidate_records}
    baseline_events = {p.event_id for p in baseline_records}
    common = candidate_events & baseline_events & set(outcomes)
    candidate_eval = score_predictions((p for p in candidate_records if p.event_id in common), outcomes)
    baseline_eval = score_predictions((p for p in baseline_records if p.event_id in common), outcomes)
    if candidate_eval.brier_score is None or baseline_eval.brier_score is None:
        return False, candidate_eval, baseline_eval
    if len(common) < min_sample_size:
        return False, candidate_eval, baseline_eval
    if candidate_eval.clv_score is None or baseline_eval.clv_score is None:
        return False, candidate_eval, baseline_eval
    return (
        candidate_eval.brier_score < baseline_eval.brier_score
        and candidate_eval.clv_score > baseline_eval.clv_score,
        candidate_eval,
        baseline_eval,
    )
