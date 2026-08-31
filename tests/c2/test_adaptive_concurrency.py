"""Unit tests for SAGE Adaptive Concurrency Governor."""

import pytest

from sage.c2.adaptive_concurrency_governor import (
    AdaptiveConcurrencyGovernor,
    ConcurrencyProfileCandidate,
    WorkloadProfile,
)
from sage.c2.experiment_ledger import ValidationStatus


def test_adaptive_concurrency_governor_basic_evaluation() -> None:
    governor = AdaptiveConcurrencyGovernor()
    workload = WorkloadProfile(
        workload_id="workload_001",
        total_tasks=10,
        dependency_density=0.1,
        resource_overlap_ratio=0.1,
        avg_verification_latency_sec=1.5,
        historical_rework_rate=0.05,
        ci_capacity_limit=10,
    )

    candidate = governor.evaluate_workload(workload)
    assert candidate.workload_id == "workload_001"
    assert candidate.validation_status == ValidationStatus.HOLD
    assert candidate.recommended_workers >= 8
    assert candidate.confidence_score > 0.8
    assert candidate.provenance_hash != ""


def test_adaptive_concurrency_governor_throttling_on_high_coupling() -> None:
    governor = AdaptiveConcurrencyGovernor()
    coupled_workload = WorkloadProfile(
        workload_id="workload_coupled",
        total_tasks=10,
        dependency_density=0.8,
        resource_overlap_ratio=0.7,
        avg_verification_latency_sec=15.0,
        historical_rework_rate=0.4,
        ci_capacity_limit=10,
    )

    candidate = governor.evaluate_workload(coupled_workload)
    assert candidate.recommended_workers < 5
    assert candidate.validation_status == ValidationStatus.HOLD
    assert "Recommended:" in candidate.rationale
