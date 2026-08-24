"""Unit tests for Fleet Readiness Intelligence Subsystem."""

import pytest
from sage.experimental.airspace.fleet_readiness import (
    FleetReadinessEvaluator,
    ReadinessStatus,
)


def test_fleet_readiness_evaluator_normal_ready_state():
    """Verify normal READY evaluation when evidence refs are present and risk flags are empty."""
    evaluator = FleetReadinessEvaluator("SAGE-FLEET-001")
    state = evaluator.evaluate_readiness(
        evidence_refs=("receipt_sec_001", "receipt_c2_002"),
        qualification_refs=("cql_lvl_4", "sql_lvl_3"),
        risk_flags=(),
        timestamp_utc="2026-08-24T00:05:00Z",
    )

    assert state.fleet_id == "SAGE-FLEET-001"
    assert state.readiness_status == ReadinessStatus.READY
    assert state.readiness_score == 1.0
    assert len(state.evidence_refs) == 2
    assert state.readiness_digest is not None


def test_fleet_readiness_evaluator_degraded_state():
    """Verify DEGRADED status assignment when minor risk flags are present."""
    evaluator = FleetReadinessEvaluator("SAGE-FLEET-001")
    state = evaluator.evaluate_readiness(
        evidence_refs=("receipt_sec_001",),
        qualification_refs=("cql_lvl_3",),
        risk_flags=("MINOR_STALE_RUNNER_WARNING",),
        timestamp_utc="2026-08-24T00:05:00Z",
    )

    assert state.readiness_status == ReadinessStatus.DEGRADED
    assert state.readiness_score < 1.0
    assert "MINOR_STALE_RUNNER_WARNING" in state.risk_flags


def test_fleet_readiness_evaluator_unqualified_state():
    """Verify UNQUALIFIED status assignment when critical security violation risk flag is present."""
    evaluator = FleetReadinessEvaluator("SAGE-FLEET-001")
    state = evaluator.evaluate_readiness(
        evidence_refs=("receipt_sec_001",),
        qualification_refs=("cql_lvl_1",),
        risk_flags=("CRITICAL_SECURITY_VIOLATION",),
        timestamp_utc="2026-08-24T00:05:00Z",
    )

    assert state.readiness_status == ReadinessStatus.UNQUALIFIED
    assert state.readiness_score <= 0.20


def test_falsification_rejection_empty_evidence_refs():
    """Verify rejection of readiness evaluation attempts with empty evidence references."""
    evaluator = FleetReadinessEvaluator()
    with pytest.raises(ValueError, match="evidence_refs cannot be empty"):
        evaluator.evaluate_readiness(
            evidence_refs=(),
            qualification_refs=("cql_lvl_4",),
            risk_flags=(),
            timestamp_utc="2026-08-24T00:05:00Z",
        )


def test_falsification_rejection_empty_qualification_refs():
    """Verify rejection of readiness evaluation attempts with empty qualification references."""
    evaluator = FleetReadinessEvaluator()
    with pytest.raises(ValueError, match="qualification_refs cannot be empty"):
        evaluator.evaluate_readiness(
            evidence_refs=("receipt_001",),
            qualification_refs=(),
            risk_flags=(),
            timestamp_utc="2026-08-24T00:05:00Z",
        )


def test_generate_readiness_receipt():
    """Verify generation of signed evidence receipt for a readiness state."""
    evaluator = FleetReadinessEvaluator("SAGE-FLEET-001")
    state = evaluator.evaluate_readiness(
        evidence_refs=("receipt_001", "receipt_002"),
        qualification_refs=("cql_lvl_4",),
        risk_flags=(),
        timestamp_utc="2026-08-24T00:05:00Z",
    )

    receipt = evaluator.generate_receipt(state, "2026-08-24T00:06:00Z")

    assert receipt.fleet_id == "SAGE-FLEET-001"
    assert receipt.readiness_status == ReadinessStatus.READY
    assert receipt.verified_evidence_count == 2
    assert receipt.receipt_digest is not None
