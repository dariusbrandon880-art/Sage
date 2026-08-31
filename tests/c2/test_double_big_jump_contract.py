import pytest

from sage.c2.build_jump_wave import FlightMissionSpec
from sage.c2.double_big_jump_contract import (
    DoubleBigJumpWaveSpec,
    reconverge_double_big_jump,
    require_current_head,
    validate_double_big_jump_waves,
)


def make_mission(slot: str, name: str) -> FlightMissionSpec:
    return FlightMissionSpec(
        flight_id=slot,
        frontier_name=name,
        target_path=f"sage/c2/{name}.py",
        collision_zone=f"sage.c2.{name}",
        evidence_ref=f"evidence/{name}.json",
        pr_or_change=name,
    )


def make_wave(wave_id: str, prefix: str) -> DoubleBigJumpWaveSpec:
    return DoubleBigJumpWaveSpec(
        wave_id=wave_id,
        missions=tuple(make_mission(f"F{i}", f"{prefix}_{i}") for i in range(1, 6)),
    )


def test_two_waves_use_reusable_slots_and_unique_missions():
    waves = validate_double_big_jump_waves((make_wave("A", "alpha"), make_wave("B", "beta")))
    assert tuple(m.flight_id for m in waves[0].missions) == ("F1", "F2", "F3", "F4", "F5")
    assert tuple(m.flight_id for m in waves[1].missions) == ("F1", "F2", "F3", "F4", "F5")


def test_duplicate_wave_identity_fails_closed():
    with pytest.raises(ValueError, match="wave identities must be unique"):
        validate_double_big_jump_waves((make_wave("A", "alpha"), make_wave("A", "beta")))


def test_stale_or_missing_head_fails_closed():
    with pytest.raises(ValueError):
        require_current_head(None, "a" * 40)
    with pytest.raises(ValueError):
        require_current_head("a" * 40, "b" * 40)


def test_reconvergence_requires_both_independent_passes():
    waves = (make_wave("A", "alpha"), make_wave("B", "beta"))
    assert reconverge_double_big_jump(wave_results={"A": True, "B": True}, waves=waves)
    assert not reconverge_double_big_jump(wave_results={"A": True, "B": False}, waves=waves)


def test_reconvergence_requires_both_wave_results():
    waves = (make_wave("A", "alpha"), make_wave("B", "beta"))
    with pytest.raises(ValueError, match="independent result"):
        reconverge_double_big_jump(wave_results={"A": True}, waves=waves)
