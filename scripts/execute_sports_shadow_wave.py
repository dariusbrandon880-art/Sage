"""Run a read-only sports quantitative shadow evaluation from JSON snapshots.

This runner never authenticates to a sportsbook, places wagers, or emits a live
execution command. It evaluates locked paper predictions against supplied outcomes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage.experimental.sports_quant import (
    FanDuelSnapshotAdapter,
    PredictionBatchEngine,
    build_failure_clusters,
    score_predictions,
    validate_oos_candidate,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshots", type=Path)
    parser.add_argument("outcomes", type=Path)
    parser.add_argument("--cycle", default="sports-shadow")
    parser.add_argument("--min-sample-size", type=int, default=30)
    args = parser.parse_args()

    snapshots = [FanDuelSnapshotAdapter.from_mapping(item) for item in load_json(args.snapshots)]
    outcomes = {str(key): int(value) for key, value in load_json(args.outcomes).items()}
    predictions = PredictionBatchEngine(model_version="shadow-v1").generate(snapshots, args.cycle)
    evaluation = score_predictions(predictions, outcomes)
    failures = build_failure_clusters(predictions, outcomes)

    receipt = {
        "cycle_id": args.cycle,
        "model_version": evaluation.model_version,
        "sample_count": evaluation.sample_count,
        "resolved_count": evaluation.resolved_count,
        "brier_score": evaluation.brier_score,
        "log_loss": evaluation.log_loss,
        "market_brier_score": evaluation.market_brier_score,
        "clv_score": evaluation.clv_score,
        "mean_market_edge": evaluation.mean_market_edge,
        "failure_cluster_count": len(failures),
        "wagering_executed": False,
        "promotion": "HOLD",
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
