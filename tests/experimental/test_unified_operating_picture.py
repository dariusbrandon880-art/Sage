"""Cross-System Integration and Restart Tests for Unified Operating Picture."""

import os
from pathlib import Path
import tempfile
import pytest

from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, SAGEMissionTask
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import (
    AirspaceState,
    Mission,
    Sortie,
    SortieState,
    StationID,
)
from sage.experimental.airspace.renderer import AirspaceRenderer
from sage.experimental.airspace.sports_adapter import SportsRCEAirspaceAdapter
from sage.experimental.airspace.unified_operating_picture import (
    UnifiedOperatingPicture,
    UnifiedOperatingPictureResolver,
)


@pytest.fixture
def temp_airspace_ledger(tmp_path):
    return tmp_path / "test_airspace_ledger.json"


@pytest.fixture
def temp_act_dir(tmp_path):
    act_path = tmp_path / "ccl_storage"
    act_path.mkdir(parents=True, exist_ok=True)
    return act_path


def test_operating_picture_reconstruction(temp_airspace_ledger, temp_act_dir):
    # Setup Airspace state
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Durable Registry",
        theater="Sports/RCE",
        objective="Cross-system test",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    s = Sortie(
        sortie_id="SORTIE-UOP-01",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Verify UOP",
        target="sage/experimental/airspace/",
    )
    mgr.create_sortie(actor="Jules", sortie=s)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-UOP-01", target_state=SortieState.BRIEFED)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-UOP-01", target_state=SortieState.CLEARED)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-UOP-01", target_state=SortieState.ACTIVE)

    # Resolve UOP
    resolver = UnifiedOperatingPictureResolver(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    uop = resolver.resolve_unified_operating_picture()

    assert uop.airspace_summary["active_mission_id"] == "RCE-002.1"
    assert uop.airspace_summary["active_sorties_count"] == 1
    assert uop.core_questions.what_is_active["airspace_mission"] == "RCE-002.1"


def test_act_airspace_state_alignment(temp_airspace_ledger, temp_act_dir):
    # Create Airspace state with Sports/RCE mission
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Durable Longitudinal Registry",
        theater="Sports/RCE",
        objective="Observe games",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    resolver = UnifiedOperatingPictureResolver(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    uop = resolver.resolve_unified_operating_picture()

    assert uop.alignment_status == "ALIGNED"
    assert uop.sports_summary["theater"] == "Sports/RCE"


def test_sports_adapter_read_only_boundary():
    adapter = SportsRCEAirspaceAdapter()
    summary = adapter.get_sports_theater_summary()
    assert summary["theater"] == "Sports/RCE"
    assert summary["governance_status"] == "LANE_ISOLATED_ZERO_REAL_MONEY"


def test_restart_rehydrates_cross_system_state(temp_airspace_ledger, temp_act_dir):
    # Session 1: Persist Airspace & ACT events
    mgr1 = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Restart Test Mission",
        theater="Sports/RCE",
        objective="Survive restart",
        current_frontier="Restart proof",
    )
    mgr1.create_mission(actor="Human Director", mission=m)

    s = Sortie(
        sortie_id="SORTIE-RST-01",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Test process restart",
        target="sage/experimental/airspace/",
    )
    mgr1.create_sortie(actor="Jules", sortie=s)
    mgr1.transition_sortie(actor="Jules", sortie_id="SORTIE-RST-01", target_state=SortieState.BRIEFED)
    mgr1.transition_sortie(actor="Jules", sortie_id="SORTIE-RST-01", target_state=SortieState.CLEARED)
    mgr1.transition_sortie(actor="Jules", sortie_id="SORTIE-RST-01", target_state=SortieState.ACTIVE)

    # Session 2: Instantiate fresh resolver simulating process restart
    resolver2 = UnifiedOperatingPictureResolver(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    uop2 = resolver2.resolve_unified_operating_picture()

    assert uop2.airspace_summary["active_mission_id"] == "RCE-002.1"
    assert uop2.airspace_summary["active_sorties_count"] == 1
    assert "SORTIE-RST-01" in uop2.core_questions.what_is_active["active_sorties"]


def test_missing_evidence_blocks_progression():
    mgr = AirspaceManager()
    with pytest.raises(ValueError, match="requires evidence_refs"):
        mgr.promote_qualification(
            actor="Mission Control",
            station_id=StationID.ENGINEERING_FLIGHT,
            agent_name="Jules",
            qualification_type="CQL",
            target_level=5,
            reason="Unverified claim",
            evidence_refs=[],
            test_refs=[],
        )


def test_conflicting_state_requires_review(temp_airspace_ledger, temp_act_dir):
    # Force state misalignment scenario
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Misaligned Theater Mission",
        theater="Sports/RCE",
        objective="Test misalignment detection",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    resolver = UnifiedOperatingPictureResolver(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    # Mock sports summary returning invalid theater
    resolver.sports_adapter.get_sports_theater_summary = lambda: {"theater": "UNKNOWN_THEATER"}

    uop = resolver.resolve_unified_operating_picture()
    assert uop.alignment_status == "MISALIGNED"


def test_renderer_uses_reconstructed_state(temp_airspace_ledger, temp_act_dir):
    mgr = AirspaceManager(ledger_path=temp_airspace_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Renderer Test Mission",
        theater="Sports/RCE",
        objective="Verify state-derived rendering",
    )
    mgr.create_mission(actor="Human Director", mission=m)

    resolver = UnifiedOperatingPictureResolver(
        airspace_ledger_path=temp_airspace_ledger,
        act_storage_path=temp_act_dir,
    )
    uop = resolver.resolve_unified_operating_picture()
    rendered = AirspaceRenderer.render_unified_operating_picture(uop)

    assert "SAGE CROSS-SYSTEM OPERATING PICTURE" in rendered
    assert "RCE-002.1" in rendered
    assert "ALIGNMENT STATUS : ALIGNED" in rendered
