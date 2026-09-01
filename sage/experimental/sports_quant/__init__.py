"""Governed sports quantitative shadow-research lane.

This package is research-only: it can ingest read-only market snapshots, generate
paper predictions, lock them before event start, resolve outcomes, score calibration,
and learn from failures. It has no wagering or account-execution surface.
"""

from .ingestion import MarketSnapshot, PlayerPropSnapshot, FanDuelSnapshotAdapter
from .prediction import (
    PredictionRecord,
    PredictionBatchEngine,
    PropEdgeResult,
    FanDuelPlayerPropAnalyzer,
    evaluate_sgp_boost,
)
from .evaluation import (
    EvaluationResult,
    calculate_clv,
    calculate_ev,
    calculate_kelly_stake,
    score_predictions,
)
from .learning import FailureCluster, build_failure_clusters, validate_oos_candidate

__all__ = [
    "MarketSnapshot",
    "PlayerPropSnapshot",
    "FanDuelSnapshotAdapter",
    "PredictionRecord",
    "PredictionBatchEngine",
    "PropEdgeResult",
    "FanDuelPlayerPropAnalyzer",
    "evaluate_sgp_boost",
    "EvaluationResult",
    "calculate_clv",
    "calculate_ev",
    "calculate_kelly_stake",
    "score_predictions",
    "FailureCluster",
    "build_failure_clusters",
    "validate_oos_candidate",
]
