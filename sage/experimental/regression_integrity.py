"""Deterministic longitudinal regression analysis.

Read-only analysis over existing flight observations. A regression is evidence,
never a capability verdict or promotion signal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sage.experimental.longitudinal_capability import FlightObservation


@dataclass(frozen=True)
class RegressionResult:
    compared: int
    regressions: int
    regression_rate: float
    baseline_failures: int
    current_failures: int
    verdict: str


def compare_observations(baseline: Sequence[FlightObservation], current: Sequence[FlightObservation]) -> RegressionResult:
    baseline_by_id = {o.mission_id: o for o in baseline}
    current_by_id = {o.mission_id: o for o in current}
    if len(baseline_by_id) != len(baseline) or len(current_by_id) != len(current):
        raise ValueError("DUPLICATE_MISSION_ID")
    if set(baseline_by_id) != set(current_by_id):
        raise ValueError("MISSION_SET_MISMATCH")
    regressions = sum(baseline_by_id[mid].success and not current_by_id[mid].success for mid in baseline_by_id)
    baseline_failures = sum(not o.success for o in baseline_by_id.values())
    current_failures = sum(not o.success for o in current_by_id.values())
    compared = len(baseline_by_id)
    rate = regressions / compared if compared else 0.0
    verdict = "REGRESSION" if regressions else "NO_REGRESSION"
    return RegressionResult(compared, regressions, rate, baseline_failures, current_failures, verdict)
