"""Focused Test Suite for SAGE Operational Reliability Metrics.

Tests reliability computation from receipts, failure classification breakdown, evidence completeness metrics,
restart determinism across fresh processes, source boundary preservation, and historical immutability.
"""

import json
import pytest
from pathlib import Path

from sage.experimental.execution_observability import (
    ExecutionObservationReceipt,
    ExecutionObservationTracker,
)
from sage.experimental.operational_reliability import (
    OperationalReliabilityRecord,
    ReliabilityAnalyzer,
)


@pytest.fixture
def tmp_rel_ledger(tmp_path):
    """Fixture providing temporary ledger path for reliability tests."""
    return tmp_path / "execution_observation_ledger.json"


def test_reliability_from_receipts(tmp_rel_ledger):
    """Verify computation of OperationalReliabilityRecord from execution receipts."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_rel_ledger)

    r1 = ExecutionObservationReceipt(
        execution_id="exec_rel_001",
        mission_id="mission_001",
        evidence_references=["evidence_1.json"],
        observed_transitions=[{"duration_seconds": 0.5}],
        completion_state="COMPLETED"
    )
    r2 = ExecutionObservationReceipt(
        execution_id="exec_rel_002",
        mission_id="mission_002",
        evidence_references=["evidence_2.json"],
        observed_transitions=[{"duration_seconds": 0.3}],
        completion_state="COMPLETED"
    )
    tracker.record_observation_receipt(r1)
    tracker.record_observation_receipt(r2)

    analyzer = ReliabilityAnalyzer(observation_tracker=tracker)
    rel_rec = analyzer.analyze_ledger()

    assert rel_rec.execution_count == 2
    assert rel_rec.completed_count == 2
    assert rel_rec.failed_count == 0
    assert rel_rec.evidence_completeness_ratio == 1.0
    assert rel_rec.reliability_score == 1.0
    assert rel_rec.average_transition_duration == pytest.approx(0.4, abs=0.01)
    assert rel_rec.sha256_hash != ""


def test_failure_classification(tmp_rel_ledger):
    """Verify accurate failure category breakdown for failed and blocked execution cycles."""
    receipts = [
        ExecutionObservationReceipt(
            execution_id="exec_fail_001",
            mission_id="mission_fail_1",
            evidence_references=["ev1.json"],
            completion_state="FAILED",
            failure_state="LINTER_VIOLATION"
        ),
        ExecutionObservationReceipt(
            execution_id="exec_fail_002",
            mission_id="mission_fail_2",
            evidence_references=["ev2.json"],
            completion_state="FAILED",
            failure_state="LINTER_VIOLATION"
        ),
        ExecutionObservationReceipt(
            execution_id="exec_halt_001",
            mission_id="mission_halt_1",
            authorization_result={"status": "BLOCKED"},
            evidence_references=["ev3.json"],
            completion_state="HALTED"
        )
    ]

    analyzer = ReliabilityAnalyzer()
    rel = analyzer.compute_reliability_from_receipts(receipts)

    assert rel.execution_count == 3
    assert rel.failed_count == 2
    assert rel.blocked_count == 1
    assert rel.failure_category_breakdown["LINTER_VIOLATION"] == 2
    assert rel.failure_category_breakdown["BLOCKED_AUTHORIZATION"] == 1
    assert rel.reliability_score < 1.0


def test_missing_evidence_metric(tmp_rel_ledger):
    """Verify evidence completeness ratio calculation when receipts lack evidence references."""
    receipts = [
        ExecutionObservationReceipt(
            execution_id="exec_ev_1",
            mission_id="m1",
            evidence_references=["ev1.json"],
            completion_state="COMPLETED"
        ),
        ExecutionObservationReceipt(
            execution_id="exec_ev_2",
            mission_id="m2",
            evidence_references=[],  # Missing evidence!
            completion_state="IN_PROGRESS"
        )
    ]

    analyzer = ReliabilityAnalyzer()
    rel = analyzer.compute_reliability_from_receipts(receipts)

    assert rel.execution_count == 2
    assert rel.evidence_completeness_ratio == 0.5
    assert rel.reliability_score < 1.0


def test_restart_determinism(tmp_rel_ledger):
    """Ensure that ReliabilityAnalyzer produces identical deterministic metrics across fresh process restarts."""
    # Process A
    tracker_a = ExecutionObservationTracker(ledger_path=tmp_rel_ledger)
    r1 = ExecutionObservationReceipt(
        execution_id="exec_det_001",
        mission_id="m1",
        evidence_references=["ev1.json"],
        completion_state="COMPLETED"
    )
    tracker_a.record_observation_receipt(r1)
    analyzer_a = ReliabilityAnalyzer(observation_tracker=tracker_a)
    rel_a = analyzer_a.analyze_ledger()

    del tracker_a
    del analyzer_a

    # Process B: Fresh restart
    tracker_b = ExecutionObservationTracker(ledger_path=tmp_rel_ledger)
    analyzer_b = ReliabilityAnalyzer(observation_tracker=tracker_b)
    rel_b = analyzer_b.analyze_ledger()

    assert rel_a.execution_count == rel_b.execution_count
    assert rel_a.reliability_score == rel_b.reliability_score
    assert rel_a.sha256_hash == rel_b.sha256_hash


def test_source_boundary_preservation(tmp_rel_ledger):
    """Verify that ReliabilityAnalyzer reads from observation tracker without writing to source systems."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_rel_ledger)
    r1 = ExecutionObservationReceipt(
        execution_id="exec_boundary_001",
        mission_id="m1",
        evidence_references=["ev1.json"],
        completion_state="COMPLETED"
    )
    tracker.record_observation_receipt(r1)

    analyzer = ReliabilityAnalyzer(observation_tracker=tracker)
    mtime_before = tmp_rel_ledger.stat().st_mtime

    rel = analyzer.analyze_ledger()
    mtime_after = tmp_rel_ledger.stat().st_mtime

    assert rel.execution_count == 1
    # Check that ledger file mtime was untouched during analysis
    assert mtime_before == mtime_after


def test_no_mutation_of_history(tmp_rel_ledger):
    """Verify that historical observation records remain 100% immutable during analysis."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_rel_ledger)
    r1 = ExecutionObservationReceipt(
        execution_id="exec_hist_001",
        mission_id="m1",
        evidence_references=["ev1.json"],
        completion_state="COMPLETED"
    )
    tracker.record_observation_receipt(r1)

    with open(tmp_rel_ledger, "r", encoding="utf-8") as f:
        content_before = f.read()

    analyzer = ReliabilityAnalyzer(observation_tracker=tracker)
    _rel = analyzer.analyze_ledger()

    with open(tmp_rel_ledger, "r", encoding="utf-8") as f:
        content_after = f.read()

    assert content_before == content_after
