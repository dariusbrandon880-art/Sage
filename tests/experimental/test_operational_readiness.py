"""Unit and Integration Tests for SAGE Operational Readiness Assessment Engine."""

import json
from pathlib import Path
import pytest

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import Mission, Sortie, SortieState, StationID
from sage.experimental.airspace.readiness import (
    OperationalReadinessAssessment,
    OperationalReadinessEvaluator,
    ReadinessStatus,
)
from sage.experimental.airspace.renderer import AirspaceRenderer
from sage.experimental.airspace.unified_operating_picture import UnifiedOperatingPictureResolver


@pytest.fixture
def temp_airspace_ledger(tmp_path):
    return tmp_path / "test_readiness_airspace_ledger.json"


@pytest.fixture
def temp_act_dir(tmp_path):
    act_path = tmp_path / "act_storage"
    act_path.mkdir(parents=True, exist_ok=True)
    return act_path


def test_readiness_reconstruction(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Durable Registry",
        theater="Sports/RCE",
        objective="Readiness test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    assessment = evaluator.evaluate_readiness()

    assert assessment.readiness_status == ReadinessStatus.READY
    assert assessment.active["airspace_mission"] == "RCE-002.1"


def test_readiness_blocks_missing_evidence(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    # Mission with non-existent evidence file requirement
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Missing Evidence Mission",
        theater="Sports/RCE",
        objective="Missing evidence test",
        evidence_requirements=["non_existent_file_xyz_123.json"],
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    assessment = evaluator.evaluate_readiness()

    assert assessment.readiness_status == ReadinessStatus.BLOCKED_MISSING_EVIDENCE
    assert "missing_evidence" in assessment.blocked


def test_readiness_detects_conflicts(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Conflict Mission",
        theater="Sports/RCE",
        objective="Conflict test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    # Mock misaligned sports summary
    evaluator.resolver.sports_adapter.get_sports_theater_summary = lambda: {"theater": "CONFLICTING_THEATER"}

    assessment = evaluator.evaluate_readiness()

    assert assessment.readiness_status == ReadinessStatus.REQUIRES_REVIEW_CONFLICT
    assert assessment.blocked["conflict_type"] == "MISALIGNED_THEATER"


def test_readiness_restart_determinism(temp_airspace_ledger, temp_act_dir):
    mgr1 = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Determinism Mission",
        theater="Sports/RCE",
        objective="Determinism test",
    )
    mgr1.create_mission(actor="Human Director", mission=m)

    # First evaluation
    eval1 = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    assessment1 = eval1.evaluate_readiness()

    # Second evaluation after process restart simulation
    eval2 = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    assessment2 = eval2.evaluate_readiness()

    assert assessment1.readiness_status == assessment2.readiness_status
    assert assessment1.active == assessment2.active
    assert assessment1.verified == assessment2.verified


def test_readiness_preserves_subsystem_boundaries(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Boundary Test Mission",
        theater="Sports/RCE",
        objective="Boundary preservation test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    initial_mtime = temp_airspace_ledger.stat().st_mtime

    evaluator = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    _assessment = evaluator.evaluate_readiness()

    # Verify ledger file was NOT modified by read-only readiness evaluation
    assert temp_airspace_ledger.stat().st_mtime == initial_mtime


def test_renderer_displays_readiness_from_state(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Renderer Test Mission",
        theater="Sports/RCE",
        objective="Renderer readiness test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    evaluator = OperationalReadinessEvaluator(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    assessment = evaluator.evaluate_readiness()
    rendered = AirspaceRenderer.render_readiness_assessment(assessment)

    assert "SAGE OPERATIONAL READINESS ASSESSMENT" in rendered
    assert "READINESS STATUS : READY" in rendered
    assert "All persistent evidence verified cleanly" in rendered
