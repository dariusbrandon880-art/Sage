"""Read-only longitudinal reliability envelope over governed observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sage.experimental.longitudinal_capability import FlightObservation


@dataclass(frozen=True)
class ReliabilityResult:
    flight_count: int
    success_rate: float
    recovery_rate: float
    continuity_rate: float
    provenance_rate: float
    evidence_rate: float
    regression_rate: float
    verdict: str


def assess_reliability(observations: Sequence[FlightObservation]) -> ReliabilityResult:
    if not observations:
        raise ValueError("NO_OBSERVATIONS")
    n = len(observations)
    success = sum(o.success for o in observations) / n
    continuity = sum(o.continuity_intact for o in observations) / n
    provenance = sum(o.provenance_preserved for o in observations) / n
    evidence = sum(o.evidence_complete for o in observations) / n
    regressions = sum(o.regression_detected for o in observations)
    recovery_candidates = [o for o in observations if o.regression_detected or o.recovered_after_failure]
    recovery = (sum(o.recovered_after_failure for o in recovery_candidates) / len(recovery_candidates)) if recovery_candidates else 1.0
    regression_rate = regressions / n
    verdict = "PASS" if all(v == 1.0 for v in (continuity, provenance, evidence)) and regression_rate == 0 else "HOLD"
    return ReliabilityResult(n, success, recovery, continuity, provenance, evidence, regression_rate, verdict)
