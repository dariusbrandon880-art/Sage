"""Regression coverage for the unified C2 immersion runtime."""

from sage.c2.immersion_runtime import activate_immersion
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


def _state(**overrides):
    values = {
        "station_identity": "[SAGE::C2::CHATGPT]",
        "mission": "Governed Continuous Intelligence",
        "phase": ExecutionPhase.VERIFY,
        "flight_id": "F3",
        "flight_status": FlightStatus.ACTIVE,
        "trust_status": TrustStatus.VERIFIED,
        "frontier": "Sports Prediction Laboratory",
        "gate": "exact-head verification",
        "next_move": "reconcile and promote",
        "evidence_refs": ("#318", "#313", "#298"),
        "provenance_head": "123877fa124b834f92ca983e48f4dd780934f5f8",
    }
    values.update(overrides)
    return ImmersionState(**values)


def test_activation_is_one_way_and_deterministic():
    frame = activate_immersion(
        _state(),
        flights=(
            {"flight_id": "F1", "label": "FOUNDATION", "status": "GREEN"},
            {"flight_id": "F2", "label": "INTELLIGENCE", "status": "GREEN"},
            {"flight_id": "F3", "label": "EXECUTION", "status": "AMBER"},
            {"flight_id": "F4", "label": "VERIFICATION", "status": "GREEN"},
            {"flight_id": "F5", "label": "WAREHOUSE", "status": "GREEN"},
        ),
        reconvergence={"verdict": "PASS", "verified_cells": 20},
        wave_id="wave-big-jump-current",
    )
    assert frame.render_mode == "SAGE_C2_IMMERSION"
    assert frame.observatory.phase == "VERIFY"
    assert frame.observatory.frontier == "Sports Prediction Laboratory"
    assert frame.observatory.evidence_refs == ("#318", "#313", "#298")
    assert frame.milestone is not None
    assert frame.milestone.impact.stars == 5
    assert frame.milestone.impact.rank == "MASTER"


def test_failed_reconvergence_never_awards_progression():
    frame = activate_immersion(
        _state(),
        reconvergence={"verdict": "FAIL", "verified_cells": 20},
        wave_id="wave-failed",
    )
    assert frame.milestone is not None
    assert frame.milestone.impact.stars == 0
    assert frame.milestone.impact.rank == "UNRANKED"


def test_projection_does_not_mutate_canonical_state():
    state = _state()
    before = state.to_dict()
    activate_immersion(state, flights=({"flight_id": "F1", "label": "FOUNDATION", "status": "GREEN"},))
    assert state.to_dict() == before
