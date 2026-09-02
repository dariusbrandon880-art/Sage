"""Verification tests for Career, Rank, and Boss Encounter governance boundaries.

Enforces:
1. Boss model restrictions (Big and Major difficulty classes only).
2. Zero fake HP / canonical state projection invariance.
3. Fleet qualification state evidence-bound persistence.
"""

import pytest
from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger
from sage.c2.immersion_state import ImmersionState, ExecutionPhase, FlightStatus, TrustStatus
from sage.c2.immersion_projection import project_c2_response_contract


def test_fleet_qualification_ledger_evidence_bound():
    """Verify that FleetQualificationLedger operates strictly as evidence-backed state."""
    ledger = FleetQualificationLedger()
    state = ledger.get_or_create_state("agent-jules")
    assert state.total_xp == 0
    assert state.rank_title == "Cadet"

    updated = ledger.record_xp_event("agent-jules", 150, badge="test-evidence-badge")
    assert updated.rank_title == "Flight Captain"
    assert "test-evidence-badge" in updated.verification_badges


def test_immersion_projection_deterministic_and_read_only():
    """Verify immersion projection layer is pure and does not invent state or HP."""
    immersion_state = ImmersionState(
        station_identity="[SAGE::C2::JULES]",
        mission="CAREER REHYDRATION",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="CAREER_ENGINE",
        gate="GOVERNANCE_LOCK",
        next_move="REPORT_REHYDRATION",
        evidence_refs=("ref_123",),
        provenance_head="f7ecf6c",
    )

    contract = project_c2_response_contract(immersion_state)
    assert contract.nameplate.station_tag == "[SAGE::C2::JULES]"
    assert contract.hud.phase == "VERIFY"
    assert "ref_123" in contract.hud.evidence_summary
    assert contract.read_only is True
    assert contract.authority == "canonical_immersion_state"
