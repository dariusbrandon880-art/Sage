"""SAGE Airspace / C2 Observability & Progression Subsystem."""

from .models import (
    StationID,
    Station,
    SortieState,
    Mission,
    Sortie,
    IntelAssessment,
    IntelTelemetry,
    CQL,
    SQL,
    QualificationEvent,
    QualificationChallengeEvent,
    QualificationRegistry,
    XPCategory,
    XPEvent,
    GameProgression,
    AirspaceState,
)

# Queue #03 must not regress the pre-existing Airspace presentation surface.
# These attributes were historically part of AirspaceState but were omitted
# by the Decimal-XP model rewrite. Keep them as explicit compatibility
# properties until the canonical model file can be surgically restored without
# rewriting unrelated state. Values remain local to the projected instance and
# are never used as an authorization or progression source of truth.
def _get_current_frontiers(state: AirspaceState) -> list[str]:
    return state.__dict__.setdefault("_current_frontiers", [])


def _set_current_frontiers(state: AirspaceState, value: list[str]) -> None:
    state.__dict__["_current_frontiers"] = value


def _get_next_clearance(state: AirspaceState) -> str:
    return state.__dict__.setdefault("_next_clearance", "Execute Session 3 Airspace Build")


def _set_next_clearance(state: AirspaceState, value: str) -> None:
    state.__dict__["_next_clearance"] = value


AirspaceState.current_frontiers = property(_get_current_frontiers, _set_current_frontiers)
AirspaceState.next_clearance = property(_get_next_clearance, _set_next_clearance)

from .nameplate import (
    build_agent_identity,
    render_agent_identity,
    render_agent_nameplate,
    render_chat_nameplate,
)

__all__ = [
    "StationID",
    "Station",
    "SortieState",
    "Mission",
    "Sortie",
    "IntelAssessment",
    "IntelTelemetry",
    "CQL",
    "SQL",
    "QualificationEvent",
    "QualificationChallengeEvent",
    "QualificationRegistry",
    "XPCategory",
    "XPEvent",
    "GameProgression",
    "AirspaceState",
    "build_agent_identity",
    "render_agent_identity",
    "render_agent_nameplate",
    "render_chat_nameplate",
]
