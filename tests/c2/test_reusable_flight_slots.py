from sage.c2.reusable_flight_slots import (
    FlightMissionAssignment,
    SAGE_FLIGHT_SLOTS,
    assignment_map,
    validate_mission_assignments,
)


def _assignment(slot: str, mission: str) -> FlightMissionAssignment:
    return FlightMissionAssignment(
        slot_id=slot,
        mission_id=mission,
        frontier_name=f"frontier-{mission}",
        target_path=f"sage/{mission}.py",
        collision_zone=f"sage/{mission}/",
        evidence_ref=f"evidence/{mission}.json",
        pr_or_change=f"mission-{mission}",
    )


def test_slots_are_stable_while_missions_can_change_between_waves():
    wave_a = [_assignment(slot, f"wave-a-{slot}") for slot in SAGE_FLIGHT_SLOTS]
    wave_b = [_assignment(slot, f"wave-b-{slot}") for slot in reversed(SAGE_FLIGHT_SLOTS)]

    assert tuple(item.slot_id for item in validate_mission_assignments(wave_a)) == SAGE_FLIGHT_SLOTS
    assert tuple(item.slot_id for item in validate_mission_assignments(wave_b)) == SAGE_FLIGHT_SLOTS
    assert assignment_map(wave_a)["F1"].mission_id == "wave-a-F1"
    assert assignment_map(wave_b)["F1"].mission_id == "wave-b-F1"


def test_each_slot_must_appear_exactly_once():
    assignments = [_assignment(slot, f"mission-{slot}") for slot in SAGE_FLIGHT_SLOTS[:-1]]
    assignments.append(_assignment("F4", "replacement"))

    try:
        validate_mission_assignments(assignments)
    except ValueError as exc:
        assert "each reusable slot exactly once" in str(exc)
    else:
        raise AssertionError("duplicate slot assignment must fail closed")


def test_mission_identity_must_be_unique_within_wave():
    assignments = [_assignment(slot, "same-mission") for slot in SAGE_FLIGHT_SLOTS]

    try:
        validate_mission_assignments(assignments)
    except ValueError as exc:
        assert "Mission identity must be unique" in str(exc)
    else:
        raise AssertionError("duplicate mission identity must fail closed")
