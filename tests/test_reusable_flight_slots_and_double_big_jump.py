"""Adversarial proof for reusable F1-F5 slots and Double Big Jump execution."""

from threading import Barrier, Event

import pytest

from scripts.execute_double_big_jump_wave import execute_parallel_waves, reconcile_receipts
from sage.c2.reusable_flight_slots import FlightMissionAssignment, SAGE_FLIGHT_SLOTS, validate_mission_assignments


def assignment(slot: str, mission: str) -> FlightMissionAssignment:
    return FlightMissionAssignment(
        slot_id=slot,
        mission_id=mission,
        frontier_name=f"frontier-{mission}",
        target_path=f"sage/{mission}.py",
        collision_zone=f"sage/{mission}",
        evidence_ref=f"evidence/{mission}",
        pr_or_change=f"change-{mission}",
    )


def test_same_slots_accept_different_missions_across_waves() -> None:
    wave_a = validate_mission_assignments([assignment(slot, f"wave-a-{slot}") for slot in SAGE_FLIGHT_SLOTS])
    wave_b = validate_mission_assignments([assignment(slot, f"wave-b-{slot}") for slot in SAGE_FLIGHT_SLOTS])

    assert tuple(item.slot_id for item in wave_a) == SAGE_FLIGHT_SLOTS
    assert tuple(item.slot_id for item in wave_b) == SAGE_FLIGHT_SLOTS
    assert {item.mission_id for item in wave_a}.isdisjoint({item.mission_id for item in wave_b})


def test_duplicate_mission_identity_fails_closed() -> None:
    assignments = [assignment(slot, "same-mission") for slot in SAGE_FLIGHT_SLOTS]
    with pytest.raises(ValueError, match="Mission identity must be unique"):
        validate_mission_assignments(assignments)


def test_double_big_jump_requires_actual_overlap() -> None:
    barrier = Barrier(2)
    a_started = Event()
    b_started = Event()
    release = Event()

    def wave_a() -> int:
        a_started.set()
        assert b_started.wait(timeout=5)
        release.set()
        return 0

    def wave_b() -> int:
        b_started.set()
        assert a_started.wait(timeout=5)
        release.wait(timeout=5)
        return 0

    results = execute_parallel_waves(wave_a, wave_b, barrier)
    assert results == {"WAVE_A": 0, "WAVE_B": 0}
    assert release.is_set()


def test_double_big_jump_rejects_stale_receipt_sha() -> None:
    head = "a" * 40
    receipt_a = {"exact_git_head": head, "rolls_royce_quality_passed": True}
    receipt_b = {"exact_git_head": "b" * 40, "fail_closed_verdict": "PASS"}
    assert reconcile_receipts(receipt_a, receipt_b, head) is False


def test_double_big_jump_accepts_matching_verified_receipts() -> None:
    head = "a" * 40
    receipt_a = {"exact_git_head": head, "rolls_royce_quality_passed": True}
    receipt_b = {"exact_git_head": head, "fail_closed_verdict": "PASS"}
    assert reconcile_receipts(receipt_a, receipt_b, head) is True
