"""Canonical contract for composing two independent Big Jump waves.

Double Big Jump is composition, not a second flight architecture:
- each wave owns reusable F1..F5 slots;
- each wave supplies explicit mission specifications;
- waves share one verified repository HEAD;
- missing or stale HEAD evidence fails closed;
- promotion requires both waves to pass independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sage.c2.build_jump_wave import FlightMissionSpec, REUSABLE_FLIGHT_SLOTS


@dataclass(frozen=True)
class DoubleBigJumpWaveSpec:
    wave_id: str
    missions: tuple[FlightMissionSpec, ...]

    def validate(self) -> None:
        if not self.wave_id.strip():
            raise ValueError("wave_id cannot be empty")
        if len(self.missions) != len(REUSABLE_FLIGHT_SLOTS):
            raise ValueError("each Double Big Jump wave requires exactly five missions")
        if tuple(m.slot_id for m in self.missions) != REUSABLE_FLIGHT_SLOTS:
            raise ValueError("missions must use reusable slots F1..F5 in canonical order")
        mission_ids = tuple(m.mission_id for m in self.missions)
        if len(set(mission_ids)) != len(mission_ids):
            raise ValueError("mission identities must be unique within a wave")


def validate_double_big_jump_waves(
    waves: Iterable[DoubleBigJumpWaveSpec],
) -> tuple[DoubleBigJumpWaveSpec, DoubleBigJumpWaveSpec]:
    pair = tuple(waves)
    if len(pair) != 2:
        raise ValueError("Double Big Jump requires exactly two independent waves")
    if pair[0].wave_id == pair[1].wave_id:
        raise ValueError("wave identities must be unique")
    for wave in pair:
        wave.validate()
    return pair  # type: ignore[return-value]


def require_current_head(actual_head: str | None, expected_head: str | None) -> str:
    """Fail closed unless a concrete current HEAD is independently available and matches."""
    if not actual_head or not expected_head:
        raise ValueError("Double Big Jump requires independently verified current repository HEAD")
    if actual_head != expected_head:
        raise ValueError("Double Big Jump repository HEAD mismatch")
    return actual_head


def reconverge_double_big_jump(
    *, wave_results: dict[str, bool], waves: Iterable[DoubleBigJumpWaveSpec]
) -> bool:
    pair = validate_double_big_jump_waves(waves)
    if set(wave_results) != {w.wave_id for w in pair}:
        raise ValueError("reconvergence requires an independent result for each wave")
    return all(wave_results[w.wave_id] for w in pair)
