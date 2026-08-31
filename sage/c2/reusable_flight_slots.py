"""Canonical reusable F1-F5 slot contract for C2 mission waves.

Slot identity is stable across waves; mission identity is supplied by the
current authorized wave.  This module is deliberately small so every
orchestrator can share the same invariant instead of embedding permanent
mission roles in F1-F5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

SAGE_FLIGHT_SLOTS = ("F1", "F2", "F3", "F4", "F5")


@dataclass(frozen=True)
class FlightMissionAssignment:
    """A current-wave mission assigned to one reusable execution slot."""

    slot_id: str
    mission_id: str
    frontier_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: tuple[str, ...] = ()


def validate_mission_assignments(
    assignments: Iterable[FlightMissionAssignment],
) -> tuple[FlightMissionAssignment, ...]:
    """Validate the five-slot contract and return assignments in slot order."""

    items = tuple(assignments)
    if len(items) != len(SAGE_FLIGHT_SLOTS):
        raise ValueError(
            f"Five-flight wave requires exactly {len(SAGE_FLIGHT_SLOTS)} assignments, got {len(items)}"
        )

    slots = tuple(item.slot_id for item in items)
    if set(slots) != set(SAGE_FLIGHT_SLOTS) or len(set(slots)) != len(slots):
        raise ValueError(f"Assignments must contain each reusable slot exactly once: {SAGE_FLIGHT_SLOTS}")

    mission_ids = tuple(item.mission_id for item in items)
    if len(set(mission_ids)) != len(mission_ids):
        raise ValueError("Mission identity must be unique within a wave")

    for item in items:
        if item.slot_id not in SAGE_FLIGHT_SLOTS:
            raise ValueError(f"Unknown reusable flight slot: {item.slot_id}")
        if not item.mission_id.strip():
            raise ValueError(f"Mission identity is required for {item.slot_id}")

    return tuple(sorted(items, key=lambda item: SAGE_FLIGHT_SLOTS.index(item.slot_id)))


def assignment_map(
    assignments: Iterable[FlightMissionAssignment],
) -> Mapping[str, FlightMissionAssignment]:
    """Return a validated slot -> current-wave mission mapping."""

    validated = validate_mission_assignments(assignments)
    return {item.slot_id: item for item in validated}
