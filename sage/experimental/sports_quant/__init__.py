"""Governed sports quantitative shadow-research lane.

This package is research-only: it can ingest read-only market snapshots, generate
paper predictions, lock them before event start, resolve outcomes, score calibration,
and learn from failures. It has no wagering or account-execution surface.
"""

from .ingestion import MarketSnapshot, FanDuelSnapshotAdapter
from .prediction import PredictionRecord, PredictionBatchEngine
from .evaluation import EvaluationResult, score_predictions
from .learning import FailureCluster, build_failure_clusters, validate_oos_candidate

__all__ = [
    "MarketSnapshot",
    "FanDuelSnapshotAdapter",
    "PredictionRecord",
    "PredictionBatchEngine",
    "EvaluationResult",
    "score_predictions",
    "FailureCluster",
    "build_failure_clusters",
    "validate_oos_candidate",
]
