"""Tests for Canonical C2 Immersion State and Projections."""

import pytest

from sage.c2.immersion_state import (
    ImmersionState,
    ExecutionPhase,
    TrustStatus,
    FlightStatus,
)
from sage.c2.immersion_projection import (
    project_immersion_nameplate,
    project_mission_hud,
    project_c2_response_contract,
    NameplateProjection,
    MissionHUDProjection,
    C2ResponseContract,
)


def test_immersion_state_creation_and_validation():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Intelligence Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="SPORTS-PREDICTION",
        gate="Capability isolation and verification",
        next_move="Execute Wave A verification suite",
        evidence_refs=("sha256_ref_001", "sha256_ref_002"),
        provenance_head="47bb765e03f1d07358ba783ce6ae69b1c8579167",
    )

    assert state.validate() is True
    assert state.station_identity == "[SAGE::C2::CHATGPT]"
    assert state.phase == ExecutionPhase.VERIFY
    assert state.trust_status == TrustStatus.VERIFIED

    d = state.to_dict()
    assert d["phase"] == "VERIFY"
    assert d["trust_status"] == "VERIFIED"
    assert len(d["evidence_refs"]) == 2


def test_immersion_state_invalid_field_raises():
    with pytest.raises(ValueError):
        ImmersionState(
            station_identity="",
            mission="Governed Intelligence Substrate",
            phase=ExecutionPhase.VERIFY,
            flight_id="F1",
            flight_status=FlightStatus.ACTIVE,
            trust_status=TrustStatus.VERIFIED,
            frontier="SPORTS-PREDICTION",
            gate="Capability isolation",
            next_move="Execute tests",
        )


def test_immersion_state_immutability():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Intelligence Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="SPORTS-PREDICTION",
        gate="Capability isolation",
        next_move="Execute tests",
    )

    with pytest.raises(AttributeError):
        state.phase = ExecutionPhase.EXECUTE  # Frozen dataclass enforcement


def test_project_immersion_nameplate():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Intelligence Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="SPORTS-PREDICTION",
        gate="Capability isolation",
        next_move="Execute tests",
    )

    nameplate = project_immersion_nameplate(state)
    assert isinstance(nameplate, NameplateProjection)

    rendered = nameplate.render()
    assert "[SAGE::C2::CHATGPT]" in rendered
    assert "MISSION CONTROL" in rendered
    assert "FLIGHT: F1 (ACTIVE)" in rendered
    assert "PHASE: VERIFY" in rendered
    assert "TRUST: VERIFIED" in rendered
    assert "FRONTIER: SPORTS-PREDICTION" in rendered


def test_project_mission_hud():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Intelligence Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="SPORTS-PREDICTION",
        gate="Capability isolation and verification",
        next_move="Execute Wave A verification suite",
        evidence_refs=("ref_123",),
    )

    hud = project_mission_hud(state)
    assert isinstance(hud, MissionHUDProjection)

    rendered = hud.render()
    assert "MISSION  : Governed Intelligence Substrate" in rendered
    assert "PHASE    : VERIFY" in rendered
    assert "FLIGHT   : F1 (ACTIVE)" in rendered
    assert "TRUST    : VERIFIED" in rendered
    assert "FRONTIER : SPORTS-PREDICTION" in rendered
    assert "GATE     : Capability isolation and verification" in rendered
    assert "EVIDENCE : 1 verified ref(s) [ref_123]" in rendered
    assert "NEXT MOVE: Execute Wave A verification suite" in rendered


def test_project_c2_response_contract():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Intelligence Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="SPORTS-PREDICTION",
        gate="Capability isolation",
        next_move="Execute tests",
        evidence_refs=("ref_999",),
    )

    contract = project_c2_response_contract(state)
    assert isinstance(contract, C2ResponseContract)
    assert contract.read_only is True
    assert contract.authority == "canonical_immersion_state"

    full_envelope = contract.render_full_envelope("Execution report details here.")
    assert "[SAGE::C2::CHATGPT]" in full_envelope
    assert "SAGE MISSION CONTROL HUD" in full_envelope
    assert "Execution report details here." in full_envelope
