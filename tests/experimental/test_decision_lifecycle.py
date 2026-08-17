"""Unit and Integration Tests for SAGE Decision Lifecycle Observation Engine."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from sage.experimental.airspace.decision_boundary import (
    DecisionRecommendation,
    OperationalDecisionBoundary,
    OperationalDecisionBoundaryEvaluator,
)
from sage.experimental.airspace.decision_lifecycle import (
    DecisionLifecycleObserver,
    DecisionLifecycleRecord,
    DecisionValidityState,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import Mission, Sortie, SortieState, StationID
from sage.experimental.airspace.renderer import AirspaceRenderer


@pytest.fixture
def temp_airspace_ledger(tmp_path):
    return tmp_path / "test_lifecycle_airspace_ledger.json"


@pytest.fixture
def temp_act_dir(tmp_path):
    act_path = tmp_path / "act_storage"
    act_path.mkdir(parents=True, exist_ok=True)
    return act_path


def test_decision_lifecycle_creation(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Lifecycle Creation Mission",
        theater="Sports/RCE",
        objective="Lifecycle test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator)
    lifecycle = observer.observe_decision_lifecycle(source_boundary=boundary)

    assert lifecycle.validity_state == DecisionValidityState.DECISION_VALIDATED
    assert lifecycle.review_required is False
    assert lifecycle.source_decision_reference == boundary.decision_id
    assert lifecycle.integrity_hash != ""


def test_decision_restart_recovery(temp_airspace_ledger, temp_act_dir):
    mgr1 = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Restart Lifecycle Mission",
        theater="Sports/RCE",
        objective="Restart test",
    )
    mgr1.create_mission(actor="Human Director", mission=m)

    eval1 = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = eval1.evaluate_decision_boundary()

    # Re-instantiate evaluator and observer simulating process restart
    eval2 = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    observer2 = DecisionLifecycleObserver(decision_evaluator=eval2)
    lifecycle = observer2.observe_decision_lifecycle(source_boundary=boundary)

    assert lifecycle.validity_state == DecisionValidityState.DECISION_VALIDATED
    assert lifecycle.source_decision_reference == boundary.decision_id


def test_stale_decision_detection(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Stale Decision Mission",
        theater="Sports/RCE",
        objective="Stale lifecycle test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    # Backdate source boundary timestamp by 48 hours to simulate stale decision
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    stale_boundary = OperationalDecisionBoundary(**boundary.model_dump())
    stale_boundary.timestamp = old_ts

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator, max_validity_hours=24.0)
    lifecycle = observer.observe_decision_lifecycle(source_boundary=stale_boundary)

    assert lifecycle.validity_state == DecisionValidityState.DECISION_STALE
    assert lifecycle.review_required is True
    assert len(lifecycle.invalidation_reasons) > 0


def test_conflicting_state_requires_review(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Conflict Decision Mission",
        theater="Sports/RCE",
        objective="Conflict lifecycle test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    # Mock current state conflict
    evaluator.readiness_evaluator.resolver.sports_adapter.get_sports_theater_summary = lambda: {"theater": "CONFLICTING_THEATER"}

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator)
    lifecycle = observer.observe_decision_lifecycle(source_boundary=boundary)

    assert lifecycle.validity_state == DecisionValidityState.DECISION_CONFLICTED
    assert lifecycle.review_required is True


def test_new_evidence_invalidates_old_snapshot(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Evidence Snapshot Mission",
        theater="Sports/RCE",
        objective="Evidence drift test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary_before = evaluator.evaluate_decision_boundary()

    # Add new evidence to airspace state
    mgr.promote_qualification(
        actor="Mission Control",
        station_id=StationID.ENGINEERING_FLIGHT,
        agent_name="Jules",
        qualification_type="CQL",
        target_level=5,
        reason="Added new evidence",
        evidence_refs=["new_evidence_artifact_2026.json"],
        test_refs=["tests/experimental/test_decision_lifecycle.py"],
    )

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator)
    lifecycle = observer.observe_decision_lifecycle(source_boundary=boundary_before)

    assert lifecycle.validity_state == DecisionValidityState.DECISION_REVIEW_REQUIRED
    assert lifecycle.review_required is True
    assert any("Evidence snapshot drift" in reason for reason in lifecycle.invalidation_reasons)


def test_lifecycle_observer_read_only(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Read Only Test Mission",
        theater="Sports/RCE",
        objective="Read only boundary test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    initial_mtime = temp_airspace_ledger.stat().st_mtime

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator)
    _lifecycle = observer.observe_decision_lifecycle(source_boundary=boundary)

    # Verify ledger file was NOT modified by read-only lifecycle observation
    assert temp_airspace_ledger.stat().st_mtime == initial_mtime


def test_renderer_displays_decision_status(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Renderer Lifecycle Mission",
        theater="Sports/RCE",
        objective="Renderer lifecycle test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    observer = DecisionLifecycleObserver(decision_evaluator=evaluator)
    lifecycle = observer.observe_decision_lifecycle(source_boundary=boundary)

    rendered = AirspaceRenderer.render_decision_lifecycle(lifecycle)

    assert "SAGE DECISION LIFECYCLE OBSERVATION" in rendered
    assert "DECISION_VALIDATED" in rendered
    assert "INTEGRITY HASH" in rendered
