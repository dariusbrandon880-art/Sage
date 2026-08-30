"""Canonical C2 Immersion State model and substrate.

Enforces strict one-way state architecture:
    CANONICAL STATE -> IMMERSION PROJECTION -> PRESENTATION

State is authoritative and read-only once created; presentation layers consume
projections derived deterministically from this state without creating theater
or guessing state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class ExecutionPhase(str, Enum):
    PREFLIGHT = "PREFLIGHT"
    EXECUTE = "EXECUTE"
    TEST = "TEST"
    EVIDENCE = "EVIDENCE"
    VERIFY = "VERIFY"
    RECONCILE = "RECONCILE"
    REPORT = "REPORT"


class TrustStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    HOLD = "HOLD"
    VERIFIED = "VERIFIED"


class FlightStatus(str, Enum):
    STANDBY = "STANDBY"
    ACTIVE = "ACTIVE"
    HOLD = "HOLD"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class ImmersionState:
    """Canonical C2 Immersion State.

    Represents the authoritative operational state of a SAGE station/flight.
    All fields are derived from canonical execution state or verified evidence.
    """

    station_identity: str
    mission: str
    phase: ExecutionPhase
    flight_id: str
    flight_status: FlightStatus
    trust_status: TrustStatus
    frontier: str
    gate: str
    next_move: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_head: str = ""

    def __post_init__(self) -> None:
        if not self.station_identity or not self.station_identity.strip():
            raise ValueError("station_identity cannot be empty.")
        if not self.mission or not self.mission.strip():
            raise ValueError("mission cannot be empty.")
        if not self.flight_id or not self.flight_id.strip():
            raise ValueError("flight_id cannot be empty.")
        if not self.frontier or not self.frontier.strip():
            raise ValueError("frontier cannot be empty.")
        if not self.gate or not self.gate.strip():
            raise ValueError("gate cannot be empty.")
        if not self.next_move or not self.next_move.strip():
            raise ValueError("next_move cannot be empty.")

    def validate(self) -> bool:
        """Verify state integrity and fail closed if required fields are missing."""
        try:
            return bool(
                self.station_identity
                and self.mission
                and self.phase in ExecutionPhase
                and self.flight_id
                and self.flight_status in FlightStatus
                and self.trust_status in TrustStatus
                and self.frontier
                and self.gate
                and self.next_move
            )
        except Exception:
            return False

    def to_dict(self) -> dict[str, object]:
        return {
            "station_identity": self.station_identity,
            "mission": self.mission,
            "phase": self.phase.value,
            "flight_id": self.flight_id,
            "flight_status": self.flight_status.value,
            "trust_status": self.trust_status.value,
            "frontier": self.frontier,
            "gate": self.gate,
            "next_move": self.next_move,
            "evidence_refs": list(self.evidence_refs),
            "provenance_head": self.provenance_head,
        }
