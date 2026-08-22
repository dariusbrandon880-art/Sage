"""Governed longitudinal evidence composition.

This module composes observed trajectory evidence across baseline and SAGE runs.
It is deliberately descriptive: it does not qualify capability, mutate canonical
state, or replace LongitudinalCapabilityEvaluator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Sequence

from sage.experimental.trajectory_reliability import (
    ReliabilityEpisode,
    ReliabilityReport,
    TrajectoryReliabilityAnalyzer,
)


@dataclass(frozen=True)
class AttributedEpisode:
    """A reliability episode with explicit causal/identity attribution."""

    episode: ReliabilityEpisode
    system: str
    mission_id: str
    session_id: str
    observation_id: str
    provenance_digest: str


@dataclass(frozen=True)
class LongitudinalEvidenceReport:
    """Paired descriptive evidence; never a qualification verdict."""

    baseline: ReliabilityReport
    sage: ReliabilityReport
    relative_success_gain: float
    recovery_delta: float
    retention_delta: float
    regression_delta: float
    provenance_complete: bool
    attribution_complete: bool
    receipt_digest: str


class LongitudinalEvidenceComposer:
    """Compose matched baseline/SAGE observations into one auditable evidence object."""

    def compose(
        self,
        baseline: Sequence[AttributedEpisode],
        sage: Sequence[AttributedEpisode],
    ) -> LongitudinalEvidenceReport:
        self._validate_side("baseline", baseline)
        self._validate_side("sage", sage)
        baseline_map = {item.mission_id: item for item in baseline}
        sage_map = {item.mission_id: item for item in sage}
        if set(baseline_map) != set(sage_map):
            raise ValueError("BASELINE_SAGE_MISSION_SET_MISMATCH")

        baseline_report = self._report(baseline)
        sage_report = self._report(sage)
        relative_gain = (
            (sage_report.success_rate - baseline_report.success_rate)
            / baseline_report.success_rate
            if baseline_report.success_rate > 0
            else (1.0 if sage_report.success_rate > 0 else 0.0)
        )
        payload = {
            "baseline": [self._canonical(item) for item in baseline],
            "sage": [self._canonical(item) for item in sage],
            "relative_success_gain": relative_gain,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return LongitudinalEvidenceReport(
            baseline=baseline_report,
            sage=sage_report,
            relative_success_gain=relative_gain,
            recovery_delta=sage_report.recovery_rate - baseline_report.recovery_rate,
            retention_delta=sage_report.retention_rate - baseline_report.retention_rate,
            regression_delta=sage_report.regression_rate - baseline_report.regression_rate,
            provenance_complete=all(item.provenance_digest for item in (*baseline, *sage)),
            attribution_complete=True,
            receipt_digest=digest,
        )

    @staticmethod
    def _validate_side(label: str, observations: Sequence[AttributedEpisode]) -> None:
        if not observations:
            raise ValueError(f"{label.upper()}_OBSERVATIONS_REQUIRED")
        ids = [item.observation_id for item in observations]
        if any(not value for value in ids):
            raise ValueError(f"{label.upper()}_OBSERVATION_ID_REQUIRED")
        if len(ids) != len(set(ids)):
            raise ValueError(f"{label.upper()}_DUPLICATE_OBSERVATION_ID")
        for item in observations:
            if not item.system:
                raise ValueError(f"{label.upper()}_SYSTEM_REQUIRED")
            if not item.mission_id:
                raise ValueError(f"{label.upper()}_MISSION_REQUIRED")
            if not item.session_id:
                raise ValueError(f"{label.upper()}_SESSION_REQUIRED")
            if not item.provenance_digest:
                raise ValueError(f"{label.upper()}_PROVENANCE_REQUIRED")

    @staticmethod
    def _report(observations: Sequence[AttributedEpisode]) -> ReliabilityReport:
        return TrajectoryReliabilityAnalyzer().analyze(
            [item.episode for item in observations]
        )

    @staticmethod
    def _canonical(item: AttributedEpisode) -> dict:
        return {
            "episode": asdict(item.episode),
            "system": item.system,
            "mission_id": item.mission_id,
            "session_id": item.session_id,
            "observation_id": item.observation_id,
            "provenance_digest": item.provenance_digest,
        }
