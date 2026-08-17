"""Unit and Integration Tests for SAGE Governed Decision Boundary Engine."""

from pathlib import Path
import pytest

from sage.experimental.airspace.decision_boundary import (
    DecisionRecommendation,
    OperationalDecisionBoundary,
    OperationalDecisionBoundaryEvaluator,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import Mission, Sortie, SortieState, StationID
from sage.experimental.airspace.renderer import AirspaceRenderer
from sage.experimental.airspace.sports_adapter import SportsRCEAirspaceAdapter


@pytest.fixture
def temp_airspace_ledger(tmp_path):
    return tmp_path / "test_decision_airspace_ledger.json"


@pytest.fixture
def temp_act_dir(tmp_path):
    act_path = tmp_path / "act_storage"
    act_path.mkdir(parents=True, exist_ok=True)
    return act_path


def test_decision_boundary_from_readiness(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Decision Boundary Mission",
        theater="Sports/RCE",
        objective="Decision test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    assert boundary.decision_recommendation == DecisionRecommendation.PROCEED_AUTHORIZED_FRONTIER
    assert boundary.readiness_reference == "READY"
    assert "clearance_authority" in boundary.authorization_required


def test_missing_evidence_blocks_decision(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Missing Evidence Mission",
        theater="Sports/RCE",
        objective="Missing evidence decision test",
        evidence_requirements=["non_existent_file_xyz_999.json"],
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()

    assert boundary.decision_recommendation == DecisionRecommendation.HOLD_MISSING_EVIDENCE
    assert boundary.readiness_reference == "BLOCKED_MISSING_EVIDENCE"


def test_conflict_requires_review(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Conflict Mission",
        theater="Sports/RCE",
        objective="Conflict decision test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    # Mock misaligned sports summary
    evaluator.readiness_evaluator.resolver.sports_adapter.get_sports_theater_summary = lambda: {"theater": "CONFLICTING_THEATER"}

    boundary = evaluator.evaluate_decision_boundary()

    assert boundary.decision_recommendation == DecisionRecommendation.HOLD_CONFLICT_REVIEW
    assert boundary.readiness_reference == "REQUIRES_REVIEW_CONFLICT"


def test_stale_observation_blocks_progression(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Stale Mission",
        theater="Sports/RCE",
        objective="Stale observation test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    # Mock state.last_updated to 3 days ago
    from datetime import datetime, timezone, timedelta
    old_ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    orig_recon = evaluator.readiness_evaluator.resolver.airspace_manager.reconstruct_airspace_state
    def mock_recon():
        st = orig_recon()
        st.last_updated = old_ts
        return st

    evaluator.readiness_evaluator.resolver.airspace_manager.reconstruct_airspace_state = mock_recon

    boundary = evaluator.evaluate_decision_boundary()

    assert boundary.decision_recommendation == DecisionRecommendation.HOLD_STALE_OBSERVATION
    assert boundary.readiness_reference == "STALE_OBSERVATION"


def test_sports_rce_remains_read_only():
    adapter = SportsRCEAirspaceAdapter()
    summary = adapter.get_sports_theater_summary()
    assert summary["theater"] == "Sports/RCE"
    assert summary["governance_status"] == "LANE_ISOLATED_ZERO_REAL_MONEY"


def test_restart_recreates_identical_decision(temp_airspace_ledger, temp_act_dir):
    mgr1 = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Restart Decision Mission",
        theater="Sports/RCE",
        objective="Restart decision test",
    )
    mgr1.create_mission(actor="Human Director", mission=m)

    eval1 = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary1 = eval1.evaluate_decision_boundary()

    # Re-instantiate evaluator simulating fresh process
    eval2 = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary2 = eval2.evaluate_decision_boundary()

    assert boundary1.decision_recommendation == boundary2.decision_recommendation
    assert boundary1.readiness_reference == boundary2.readiness_reference
    assert boundary1.recommended_frontier == boundary2.recommended_frontier


def test_renderer_displays_decision_boundary(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Renderer Decision Mission",
        theater="Sports/RCE",
        objective="Renderer decision test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalDecisionBoundaryEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    boundary = evaluator.evaluate_decision_boundary()
    rendered = AirspaceRenderer.render_decision_boundary(boundary)

    assert "SAGE GOVERNED DECISION PACKAGE" in rendered
    assert "PROCEED_AUTHORIZED_FRONTIER" in rendered
    assert "MISSION_DIRECTOR (Human Operator)" in rendered
