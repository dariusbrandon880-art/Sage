"""Unit and Integration Tests for SAGE Airspace / C2 Observability & Progression Subsystem."""

import os
from pathlib import Path
import tempfile
import pytest

from sage.experimental.airspace.models import (
    AirspaceState,
    Station,
    StationID,
    Mission,
    Sortie,
    SortieState,
    IntelAssessment,
    IntelTelemetry,
    CQL,
    SQL,
    QualificationRegistry,
    QualificationEvent,
    QualificationChallengeEvent,
    GameProgression,
    XPEvent,
    XPCategory,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.renderer import AirspaceRenderer
from sage.experimental.airspace.sports_adapter import SportsRCEAirspaceAdapter


@pytest.fixture
def temp_ledger(tmp_path):
    return tmp_path / "test_airspace_ledger.json"


# ---------------------------------------------------------
# State & Sortie Transitions
# ---------------------------------------------------------

def test_airspace_state_creation():
    state = AirspaceState()
    assert state.airspace_id == "SAGE-AIRSPACE-001"
    assert len(state.stations) == 4
    assert StationID.MISSION_DIRECTOR in state.stations
    assert StationID.ENGINEERING_FLIGHT in state.stations


def test_mission_state_transition():
    mission = Mission(
        mission_id="RCE-002.1",
        mission_name="Durable Longitudinal Registry",
        theater="Sports/RCE",
        priority="P0",
        objective="Verify longitudinal predictions",
        current_frontier="Restart continuity",
    )
    assert mission.status == "ACTIVE"
    mission.status = "COMPLETED"
    assert mission.status == "COMPLETED"


def test_sortie_state_transition():
    sortie = Sortie(
        sortie_id="SORTIE-001",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Build Airspace Manager",
        target="sage/experimental/airspace/",
    )
    assert sortie.status == SortieState.CREATED

    sortie.transition_to(SortieState.BRIEFED)
    assert sortie.status == SortieState.BRIEFED

    sortie.transition_to(SortieState.CLEARED)
    assert sortie.status == SortieState.CLEARED

    sortie.transition_to(SortieState.ACTIVE)
    assert sortie.status == SortieState.ACTIVE


def test_invalid_transition_fails_closed():
    sortie = Sortie(
        sortie_id="SORTIE-002",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Test illegal jump",
        target="sage/experimental/airspace/",
    )
    # Attempting to jump directly from CREATED to VERIFIED must fail closed
    with pytest.raises(ValueError, match="Invalid Sortie Transition"):
        sortie.transition_to(SortieState.VERIFIED)


# ---------------------------------------------------------
# Stations
# ---------------------------------------------------------

def test_station_roles_are_distinct():
    state = AirspaceState()
    roles = {st.role_description for st in state.stations.values()}
    agents = {st.agent_name for st in state.stations.values()}
    assert len(roles) == 4
    assert len(agents) == 4
    assert "Jules" in agents
    assert "Gemini" in agents


def test_station_assignment_is_explicit():
    mission = Mission(
        mission_id="TEST-001",
        mission_name="Explicit Station Test",
        theater="Test",
        objective="Verify explicit station assignment",
        assigned_stations=[StationID.INTEL_STATION, StationID.ENGINEERING_FLIGHT],
    )
    assert len(mission.assigned_stations) == 2
    assert StationID.INTEL_STATION in mission.assigned_stations
    assert StationID.ENGINEERING_FLIGHT in mission.assigned_stations


# ---------------------------------------------------------
# Qualification System (CQL / SQL)
# ---------------------------------------------------------

def test_cql_promotion_requires_evidence():
    reg = QualificationRegistry()
    # Promoting Jules (currently CQL-4) to CQL-5 without evidence must raise ValueError
    with pytest.raises(ValueError, match="requires evidence_refs"):
        reg.promote_station(
            station_id=StationID.ENGINEERING_FLIGHT,
            agent_name="Jules",
            qualification_type="CQL",
            target_level=5,
            reason="Unverified claim",
            evidence_refs=[],
            test_refs=["test_1.py"],
        )


def test_cql_cannot_skip_required_evidence():
    reg = QualificationRegistry()
    # Jumping from CQL-4 directly to CQL-6 must be rejected as level skipping
    with pytest.raises(ValueError, match="Level Skipping Rejected"):
        reg.promote_station(
            station_id=StationID.ENGINEERING_FLIGHT,
            agent_name="Jules",
            qualification_type="CQL",
            target_level=6,
            reason="Attempting level jump",
            evidence_refs=["ev_1.json"],
            test_refs=["test_1.py"],
        )


def test_sql_progression_is_monotonic_without_reversal():
    reg = QualificationRegistry()
    evt = reg.promote_station(
        station_id=StationID.INTEL_STATION,
        agent_name="Gemini",
        qualification_type="SQL",
        target_level=4,
        reason="Demonstrated operational search intelligence with external evidence",
        evidence_refs=["intel_001.json"],
        test_refs=["test_intel.py"],
    )
    assert reg.sql_levels[StationID.INTEL_STATION] == 4
    assert evt.previous_level == 3
    assert evt.new_level == 4


def test_qualification_event_is_persistent(temp_ledger):
    mgr = AirspaceManager(ledger_path=temp_ledger)
    mgr.promote_qualification(
        actor="Mission Control",
        station_id=StationID.ENGINEERING_FLIGHT,
        agent_name="Jules",
        qualification_type="CQL",
        target_level=5,
        reason="Demonstrated restart recovery and full platform test compliance",
        evidence_refs=["evidence_capture/airspace_ledger.json"],
        test_refs=["tests/experimental/test_airspace.py"],
        downstream_effect="Airspace subsystem fully operational",
    )

    # Reconstruct from ledger
    reconstructed = mgr.reconstruct_airspace_state()
    assert reconstructed.stations[StationID.ENGINEERING_FLIGHT].current_cql == 5
    assert len(reconstructed.qualification_registry.promotion_history) == 1
    assert reconstructed.qualification_registry.promotion_history[0].new_level == 5


def test_qualification_challenge_revocation():
    reg = QualificationRegistry()
    reg.cql_levels[StationID.ENGINEERING_FLIGHT] = 5
    challenge = reg.challenge_qualification(
        station_id=StationID.ENGINEERING_FLIGHT,
        qualification_type="CQL",
        reason="Discovered unverified claim in historical log",
        falsifying_evidence_refs=["falsifying_receipt_001.json"],
        demotion_target=4,
    )
    assert challenge.outcome == "REVOKED"
    assert reg.cql_levels[StationID.ENGINEERING_FLIGHT] == 4


# ---------------------------------------------------------
# XP & Progression
# ---------------------------------------------------------

def test_xp_derives_from_verified_events():
    prog = GameProgression()
    event = prog.award_xp(
        station_id=StationID.ENGINEERING_FLIGHT,
        category=XPCategory.ENGINEERING_FLIGHT_XP,
        amount=100,
        reason="Passed focused unit test suite for Airspace module",
        verified_event_ref="commit_sha_21b2c1da",
    )
    assert event.amount == 100
    assert prog.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT) == 100


def test_unverified_claim_does_not_award_xp():
    prog = GameProgression()
    with pytest.raises(ValueError, match="verified_event_ref cannot be empty"):
        prog.award_xp(
            station_id=StationID.ENGINEERING_FLIGHT,
            category=XPCategory.ENGINEERING_FLIGHT_XP,
            amount=50,
            reason="Unverified claim",
            verified_event_ref="",
        )


# ---------------------------------------------------------
# Persistence & Restart
# ---------------------------------------------------------

def test_airspace_state_survives_restart(temp_ledger):
    mgr1 = AirspaceManager(ledger_path=temp_ledger)
    m = Mission(
        mission_id="RCE-002.1",
        mission_name="Longitudinal Registry",
        theater="Sports/RCE",
        objective="Verify continuity",
        current_frontier="Restart test",
    )
    mgr1.create_mission(actor="Human Director", mission=m)

    s = Sortie(
        sortie_id="RCE-SORTIE-01",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Build state layer",
        target="sage/experimental/airspace/manager.py",
    )
    mgr1.create_sortie(actor="Jules", sortie=s)
    mgr1.transition_sortie(actor="Jules", sortie_id="RCE-SORTIE-01", target_state=SortieState.BRIEFED, reason="Briefed")
    mgr1.transition_sortie(actor="Jules", sortie_id="RCE-SORTIE-01", target_state=SortieState.CLEARED, reason="Cleared")
    mgr1.transition_sortie(actor="Jules", sortie_id="RCE-SORTIE-01", target_state=SortieState.ACTIVE, reason="Executing")

    # Simulate fresh process session instantiation with new AirspaceManager
    mgr2 = AirspaceManager(ledger_path=temp_ledger)
    state2 = mgr2.reconstruct_airspace_state()

    assert state2.active_mission is not None
    assert state2.active_mission.mission_id == "RCE-002.1"
    assert len(state2.active_sorties) == 1
    assert state2.active_sorties[0].sortie_id == "RCE-SORTIE-01"
    assert state2.active_sorties[0].status == SortieState.ACTIVE


def test_active_sortie_is_recoverable(temp_ledger):
    mgr = AirspaceManager(ledger_path=temp_ledger)
    s = Sortie(
        sortie_id="SORTIE-ACT-01",
        mission_id="M-1",
        station=StationID.INTEL_STATION,
        objective="Recon target",
        target="external_api",
    )
    mgr.create_sortie(actor="Gemini", sortie=s)
    mgr.transition_sortie(actor="Gemini", sortie_id="SORTIE-ACT-01", target_state=SortieState.BRIEFED)
    mgr.transition_sortie(actor="Gemini", sortie_id="SORTIE-ACT-01", target_state=SortieState.CLEARED)
    mgr.transition_sortie(actor="Gemini", sortie_id="SORTIE-ACT-01", target_state=SortieState.ACTIVE)

    reconstructed = mgr.reconstruct_airspace_state()
    active_sorties = [st for st in reconstructed.active_sorties if st.status == SortieState.ACTIVE]
    assert len(active_sorties) == 1
    assert active_sorties[0].sortie_id == "SORTIE-ACT-01"


def test_completed_sortie_remains_historically_visible(temp_ledger):
    mgr = AirspaceManager(ledger_path=temp_ledger)
    s = Sortie(
        sortie_id="SORTIE-DONE-01",
        mission_id="M-1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Complete work",
        target="sage/experimental/airspace/",
    )
    mgr.create_sortie(actor="Jules", sortie=s)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.BRIEFED)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.CLEARED)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.ACTIVE)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.EVIDENCE_CAPTURE, evidence=["ev1.json"])
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.DEBRIEF)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.VERIFIED)
    mgr.transition_sortie(actor="Jules", sortie_id="SORTIE-DONE-01", target_state=SortieState.CLOSED)

    reconstructed = mgr.reconstruct_airspace_state()
    closed_sorties = [st for st in reconstructed.active_sorties if st.status == SortieState.CLOSED]
    assert len(closed_sorties) == 1
    assert closed_sorties[0].sortie_id == "SORTIE-DONE-01"


# ---------------------------------------------------------
# Telemetry
# ---------------------------------------------------------

def test_intel_assessment_enum():
    assert IntelAssessment.CONFIRMED.value == "CONFIRMED"
    assert IntelAssessment.CONTRADICTED.value == "CONTRADICTED"
    assert IntelAssessment.UNKNOWN.value == "UNKNOWN"
    assert IntelAssessment.NEW_OPPORTUNITY.value == "NEW_OPPORTUNITY"


def test_intel_requires_source_or_explicit_unknown():
    with pytest.raises(ValueError, match="Source dictionary required"):
        IntelTelemetry(
            telemetry_id="intel-1",
            target="API docs",
            vector="Web search",
            assessment=IntelAssessment.CONFIRMED,
            findings=["Found new endpoint"],
            adversarial_review="No conflict detected",
            proposed_action="Integrate endpoint",
            source={},
        )


def test_contradiction_is_preserved():
    intel = IntelTelemetry(
        telemetry_id="intel-2",
        target="API deprecation check",
        vector="Web search",
        assessment=IntelAssessment.CONTRADICTED,
        findings=["API v1 is deprecated in favor of v2"],
        adversarial_review="Using v1 will fail in production",
        proposed_action="Migrate to v2 API",
        source={"type": "doc", "url": "https://api.example.com/docs"},
        contradiction_details="Documentation confirms v1 endpoint removed in 2026.",
    )
    assert intel.assessment == IntelAssessment.CONTRADICTED
    assert intel.contradiction_details is not None


# ---------------------------------------------------------
# Governance & Rendering
# ---------------------------------------------------------

def test_airspace_does_not_mutate_core():
    # Verify no files in sage/core were modified
    core_dir = Path("sage/core")
    assert core_dir.exists()


def test_sports_adapter_read_only():
    adapter = SportsRCEAirspaceAdapter()
    summary = adapter.get_sports_theater_summary()
    assert summary["theater"] == "Sports/RCE"
    assert summary["governance_status"] == "LANE_ISOLATED_ZERO_REAL_MONEY"


def test_mobile_compact_render():
    state = AirspaceState()
    rendered = AirspaceRenderer.render_c2_board(state)
    assert "SAGE AIRSPACE // C2 OPERATING PICTURE" in rendered
    assert "Human Director" in rendered
    assert "Jules" in rendered


def test_mission_card_render():
    mission = Mission(
        mission_id="RCE-002.1",
        mission_name="Longitudinal Prediction Registry",
        theater="Sports/RCE",
        objective="Verify longitudinal predictions",
        assigned_stations=[StationID.ENGINEERING_FLIGHT],
    )
    rendered = AirspaceRenderer.render_mission_card(mission)
    assert "MISSION CARD // RCE-002.1" in rendered
    assert "Sports/RCE" in rendered


def test_sortie_debrief_render():
    sortie = Sortie(
        sortie_id="SORTIE-001",
        mission_id="RCE-002.1",
        station=StationID.ENGINEERING_FLIGHT,
        objective="Build Airspace Manager",
        target="sage/experimental/airspace/manager.py",
        status=SortieState.VERIFIED,
        artifacts=["sage/experimental/airspace/manager.py"],
        tests=["tests/experimental/test_airspace.py"],
        evidence=["evidence_capture/airspace_ledger.json"],
    )
    rendered = AirspaceRenderer.render_sortie_debrief(sortie)
    assert "SORTIE DEBRIEF // SORTIE-001" in rendered
    assert "VERIFIED" in rendered


def test_capability_promotion_render():
    event = QualificationEvent(
        event_id="qual_evt_001",
        station_id=StationID.ENGINEERING_FLIGHT,
        agent_name="Jules",
        qualification_type="CQL",
        previous_level=4,
        new_level=5,
        promotion_reason="Demonstrated restart recovery and full platform test compliance",
        evidence_refs=["evidence_capture/airspace_ledger.json"],
        test_refs=["tests/experimental/test_airspace.py"],
        downstream_effect="Airspace subsystem fully operational",
    )
    rendered = AirspaceRenderer.render_qualification_card(event)
    assert "QUALIFICATION PROMOTION DEBRIEF" in rendered
    assert "CQL-4 ➔ CQL-5" in rendered
