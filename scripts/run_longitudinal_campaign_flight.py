#!/usr/bin/env python3
"""Run one bounded flight from the governed five-flight campaign.

This orchestrator reuses the existing authentic repository-backed pilot executors
and LongitudinalFlightRunner. It changes only the mission profile and evaluation
identity; it does not create a second evaluator or authority path.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import tempfile
from pathlib import Path

from sage.experimental.longitudinal_capability import EvaluationPlan, MissionCase
from sage.experimental.longitudinal_runner import LongitudinalFlightRunner
from scripts.run_longitudinal_flight import baseline_executor, sage_executor

PROFILES = {
    "004": {
        "name": "RECOVERY",
        "missions": (
            MissionCase("pilot_repo_lint_runner", difficulty=1, requires_cross_session_reuse=False),
            MissionCase("pilot_repo_lint_evaluator", difficulty=1, requires_cross_session_reuse=True),
            MissionCase("pilot_runner_regression_tests", difficulty=2, requires_cross_session_reuse=True, requires_recovery=True),
        ),
    },
    "005": {
        "name": "REUSE",
        "missions": (
            MissionCase("pilot_repo_lint_runner", difficulty=1, requires_cross_session_reuse=True),
            MissionCase("pilot_repo_lint_evaluator", difficulty=1, requires_cross_session_reuse=True),
            MissionCase("pilot_runner_regression_tests", difficulty=2, requires_cross_session_reuse=True, requires_recovery=True),
        ),
    },
    "006": {
        "name": "RETENTION_REGRESSION",
        "missions": (
            MissionCase("pilot_repo_lint_runner", difficulty=1, requires_cross_session_reuse=True),
            MissionCase("pilot_repo_lint_evaluator", difficulty=2, requires_cross_session_reuse=True),
            MissionCase("pilot_runner_regression_tests", difficulty=2, requires_cross_session_reuse=True, requires_recovery=True),
        ),
    },
    "007": {
        "name": "COMPOUND",
        "missions": (
            MissionCase("pilot_repo_lint_runner", difficulty=1, requires_cross_session_reuse=True),
            MissionCase("pilot_repo_lint_evaluator", difficulty=2, requires_cross_session_reuse=True),
            MissionCase("pilot_runner_regression_tests", difficulty=2, requires_cross_session_reuse=True, requires_recovery=True),
        ),
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flight", choices=sorted(PROFILES), required=True)
    args = parser.parse_args()
    profile = PROFILES[args.flight]

    plan = EvaluationPlan(
        evaluation_id=f"SAGE-LONGITUDINAL-FLIGHT-{args.flight}",
        mission_set_id=f"REPO-GOVERNED-FLIGHT-{args.flight}",
        missions=profile["missions"],
        minimum_missions=3,
        minimum_relative_gain=0.0,
        maximum_regression_rate=0.0,
        minimum_evidence_completeness=1.0,
        minimum_provenance_preservation=1.0,
        minimum_unauthorized_block_rate=0.0,
        minimum_continuity_integrity=0.0,
        minimum_learning_candidate_quality=0.0,
    )

    with tempfile.TemporaryDirectory(prefix=f"sage-longitudinal-flight-{args.flight}-") as temp_dir:
        root = Path(temp_dir)
        state_dir = root / "continuity"
        sandbox_root = root / "sandbox"

        def run_baseline(mission, session_id):
            return baseline_executor(state_dir, mission, session_id)

        def run_sage(mission, session_id):
            return sage_executor(state_dir, sandbox_root, mission, session_id)

        runner = LongitudinalFlightRunner(plan, record_manager=None, mission_session_prefix=f"flight-{args.flight}")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            result = runner.run(run_baseline, run_sage)

        receipt = result.evaluation
        report = {
            "flight": f"SAGE-LONGITUDINAL-FLIGHT-{args.flight}",
            "profile": profile["name"],
            "classification": "REAL_REPOSITORY_FLIGHT_OBSERVATION_ONLY",
            "verdict": receipt.verdict.value,
            "receipt_hash": receipt.receipt_hash(),
            "relative_success_gain": receipt.relative_success_gain,
            "recovery_rate": receipt.recovery_rate,
            "regression_rate": receipt.regression_rate,
            "fail_closed_reasons": list(receipt.fail_closed_reasons),
            "canonical_state_mutation": False,
            "baseline": [o.__dict__ for o in result.baseline_observations],
            "sage": [o.__dict__ for o in result.sage_observations],
        }
        print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
