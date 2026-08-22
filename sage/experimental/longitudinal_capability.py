"""Governed longitudinal capability evaluation for SAGE.

This experimental module turns the existing flight/progression primitives into a
pre-registered, fail-closed comparison harness. It deliberately does not create
a second authority or persistence system: callers can persist the resulting
receipt through the existing SAGE flight/evidence machinery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


class CapabilityVerdict(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class MissionCase:
    mission_id: str
    difficulty: int
    requires_cross_session_reuse: bool = True
    requires_recovery: bool = False
    requires_provenance: bool = True


@dataclass(frozen=True)
class FlightObservation:
    system: str
    mission_id: str
    session_id: str
    success: bool
    recovered_after_failure: bool = False
    evidence_complete: bool = False
    provenance_preserved: bool = False
    unauthorized_transition_blocked: bool = False
    continuity_intact: bool = False
    retained_across_sessions: bool = False
    learning_candidate_quality: float | None = None
    elapsed_seconds: float | None = None
    cost_units: float | None = None
    regression_detected: bool = False
    notes: str = ""


@dataclass(frozen=True)
class MetricResult:
    name: str
    value: float
    threshold: float
    direction: str
    sufficient: bool


@dataclass(frozen=True)
class EvaluationPlan:
    evaluation_id: str
    mission_set_id: str
    missions: tuple[MissionCase, ...]
    minimum_missions: int
    minimum_relative_gain: float
    maximum_regression_rate: float
    minimum_evidence_completeness: float
    minimum_provenance_preservation: float
    minimum_unauthorized_block_rate: float
    minimum_continuity_integrity: float
    minimum_learning_candidate_quality: float

    def canonical_payload(self) -> dict[str, Any]:
        return {"evaluation_id": self.evaluation_id, "mission_set_id": self.mission_set_id, "missions": [asdict(m) for m in self.missions], "minimum_missions": self.minimum_missions, "minimum_relative_gain": self.minimum_relative_gain, "maximum_regression_rate": self.maximum_regression_rate, "minimum_evidence_completeness": self.minimum_evidence_completeness, "minimum_provenance_preservation": self.minimum_provenance_preservation, "minimum_unauthorized_block_rate": self.minimum_unauthorized_block_rate, "minimum_continuity_integrity": self.minimum_continuity_integrity, "minimum_learning_candidate_quality": self.minimum_learning_candidate_quality}

    def plan_hash(self) -> str:
        payload = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapabilityEvaluationReceipt:
    evaluation_id: str
    mission_set_id: str
    plan_hash: str
    baseline_metrics: tuple[MetricResult, ...]
    sage_metrics: tuple[MetricResult, ...]
    relative_success_gain: float
    recovery_rate: float
    regression_rate: float
    verdict: CapabilityVerdict
    fail_closed_reasons: tuple[str, ...] = field(default_factory=tuple)

    def receipt_hash(self) -> str:
        payload = {"evaluation_id": self.evaluation_id, "mission_set_id": self.mission_set_id, "plan_hash": self.plan_hash, "baseline_metrics": [asdict(m) for m in self.baseline_metrics], "sage_metrics": [asdict(m) for m in self.sage_metrics], "relative_success_gain": self.relative_success_gain, "recovery_rate": self.recovery_rate, "regression_rate": self.regression_rate, "verdict": self.verdict.value, "fail_closed_reasons": list(self.fail_closed_reasons)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class LongitudinalCapabilityEvaluator:
    """Compare a governed SAGE flight against a locked baseline mission set."""

    def __init__(self, plan: EvaluationPlan):
        if len(plan.missions) < plan.minimum_missions:
            raise ValueError("MISSION_SET_TOO_SMALL")
        mission_ids = [m.mission_id for m in plan.missions]
        if len(mission_ids) != len(set(mission_ids)):
            raise ValueError("DUPLICATE_MISSION_ID")
        if any(m.difficulty < 1 for m in plan.missions):
            raise ValueError("INVALID_MISSION_DIFFICULTY")
        self.plan = plan
        self._observed = False

    def evaluate(self, baseline: Sequence[FlightObservation], sage: Sequence[FlightObservation]) -> CapabilityEvaluationReceipt:
        if self._observed:
            raise RuntimeError("EVALUATION_ALREADY_FINALIZED")
        expected = {m.mission_id for m in self.plan.missions}
        baseline_by_id = self._validate_observations("baseline", baseline, expected)
        sage_by_id = self._validate_observations("sage", sage, expected)
        self._observed = True
        baseline_metrics = self._metrics(baseline_by_id)
        sage_metrics = self._metrics(sage_by_id)
        baseline_success = self._success_rate(baseline_by_id.values())
        sage_success = self._success_rate(sage_by_id.values())
        relative_gain = ((sage_success - baseline_success) / baseline_success if baseline_success > 0 else (1.0 if sage_success > 0 else 0.0))
        recovery_rate = self._recovery_rate(sage_by_id.values())
        regression_rate = self._regression_rate(sage_by_id.values())
        reasons: list[str] = []
        if not self._all_sufficient(sage_metrics):
            reasons.append("SAGE_METRIC_THRESHOLD_NOT_MET")
        if relative_gain < self.plan.minimum_relative_gain:
            reasons.append("BASELINE_ADVANTAGE_NOT_BEATEN")
        if regression_rate > self.plan.maximum_regression_rate:
            reasons.append("REGRESSION_RATE_TOO_HIGH")
        if not all(o.continuity_intact for o in sage_by_id.values()):
            reasons.append("CONTINUITY_INTEGRITY_FAILURE")
        required_reuse = {m.mission_id for m in self.plan.missions if m.requires_cross_session_reuse}
        if any(not sage_by_id[mid].retained_across_sessions for mid in required_reuse):
            reasons.append("CAPABILITY_RETENTION_FAILURE")
        if not all(o.provenance_preserved for o in sage_by_id.values()):
            reasons.append("PROVENANCE_PRESERVATION_FAILURE")
        if self.plan.minimum_learning_candidate_quality > 0 and any(o.learning_candidate_quality is None for o in sage_by_id.values()):
            reasons.append("LEARNING_CANDIDATE_QUALITY_INDETERMINATE")
        if any(o.notes.startswith("EXECUTOR_EXCEPTION ") for o in baseline_by_id.values()):
            reasons.append("BASELINE_EXECUTION_INTEGRITY_FAILURE")
        if any(o.notes.startswith("EXECUTOR_EXCEPTION ") for o in sage_by_id.values()):
            reasons.append("SAGE_EXECUTION_INTEGRITY_FAILURE")
        if reasons:
            verdict = CapabilityVerdict.NEGATIVE_RESULT if any(r in {"REGRESSION_RATE_TOO_HIGH", "CONTINUITY_INTEGRITY_FAILURE", "CAPABILITY_RETENTION_FAILURE", "PROVENANCE_PRESERVATION_FAILURE"} for r in reasons) else CapabilityVerdict.HOLD
        else:
            verdict = CapabilityVerdict.PASS
        return CapabilityEvaluationReceipt(self.plan.evaluation_id, self.plan.mission_set_id, self.plan.plan_hash(), tuple(baseline_metrics), tuple(sage_metrics), relative_gain, recovery_rate, regression_rate, verdict, tuple(reasons))

    def _validate_observations(self, system: str, observations: Sequence[FlightObservation], expected: set[str]) -> dict[str, FlightObservation]:
        if any(o.system != system for o in observations):
            raise ValueError(f"{system.upper()}_SYSTEM_LABEL_MISMATCH")
        observed = {o.mission_id for o in observations}
        if observed != expected:
            raise ValueError(f"{system.upper()}_MISSION_SET_MISMATCH:missing={sorted(expected-observed)}:extra={sorted(observed-expected)}")
        if len(observations) != len(observed):
            raise ValueError(f"{system.upper()}_DUPLICATE_OBSERVATION")
        return {o.mission_id: o for o in observations}

    @staticmethod
    def _success_rate(observations: Iterable[FlightObservation]) -> float:
        values = list(observations)
        return sum(o.success for o in values) / len(values)

    @staticmethod
    def _recovery_rate(observations: Iterable[FlightObservation]) -> float:
        values = list(observations)
        required = [o for o in values if o.recovered_after_failure or o.regression_detected]
        return 1.0 if not required else sum(o.recovered_after_failure for o in required) / len(required)

    @staticmethod
    def _regression_rate(observations: Iterable[FlightObservation]) -> float:
        values = list(observations)
        return sum(o.regression_detected for o in values) / len(values)

    def _metrics(self, observations: Mapping[str, FlightObservation]) -> list[MetricResult]:
        values = list(observations.values())
        evidence = sum(o.evidence_complete for o in values) / len(values)
        provenance = sum(o.provenance_preserved for o in values) / len(values)
        blocked = sum(o.unauthorized_transition_blocked for o in values) / len(values)
        continuity = sum(o.continuity_intact for o in values) / len(values)
        required_reuse = {m.mission_id for m in self.plan.missions if m.requires_cross_session_reuse}
        retention_values = [o.retained_across_sessions for mission_id, o in observations.items() if mission_id in required_reuse]
        retention = sum(retention_values) / len(retention_values) if retention_values else 1.0
        quality_values = [o.learning_candidate_quality for o in values if o.learning_candidate_quality is not None]
        quality = sum(quality_values) / len(quality_values) if quality_values else 0.0
        elapsed_values = [o.elapsed_seconds for o in values if o.elapsed_seconds is not None]
        mean_elapsed = sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0
        cost_values = [o.cost_units for o in values if o.cost_units is not None]
        mean_cost = sum(cost_values) / len(cost_values) if cost_values else 0.0
        return [MetricResult("success_rate", self._success_rate(values), 0.0, "gte", True), MetricResult("evidence_completeness", evidence, self.plan.minimum_evidence_completeness, "gte", evidence >= self.plan.minimum_evidence_completeness), MetricResult("provenance_preservation", provenance, self.plan.minimum_provenance_preservation, "gte", provenance >= self.plan.minimum_provenance_preservation), MetricResult("unauthorized_transition_block_rate", blocked, self.plan.minimum_unauthorized_block_rate, "gte", blocked >= self.plan.minimum_unauthorized_block_rate), MetricResult("continuity_integrity", continuity, self.plan.minimum_continuity_integrity, "gte", continuity >= self.plan.minimum_continuity_integrity), MetricResult("capability_retention", retention, 1.0, "gte", retention >= 1.0), MetricResult("learning_candidate_quality", quality, self.plan.minimum_learning_candidate_quality, "gte", quality >= self.plan.minimum_learning_candidate_quality or self.plan.minimum_learning_candidate_quality == 0), MetricResult("mean_elapsed_seconds", mean_elapsed, 0.0, "observed", True), MetricResult("mean_cost_units", mean_cost, 0.0, "observed", bool(cost_values))]

    @staticmethod
    def _all_sufficient(metrics: Sequence[MetricResult]) -> bool:
        return all(m.sufficient for m in metrics if m.name not in {"success_rate", "mean_elapsed_seconds", "mean_cost_units"})
