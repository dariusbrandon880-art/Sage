"""SAGE C2 runtime execution invariant state."""

from dataclasses import dataclass, field
from typing import Any


class C2StateValidationError(RuntimeError):
    """Raised when the C2 execution envelope is not ready."""


@dataclass
class C2ExecutionState:
    """Runtime-owned C2 execution envelope."""

    identity: str
    mission: str
    flight_id: str
    target: str
    phase: str
    invariants: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    authorization_state: bool = False

    def validate(self) -> bool:
        return bool(
            self.identity
            and self.mission
            and self.flight_id
            and self.target
            and self.phase
            and self.authorization_state
        )

    def require_valid(self) -> None:
        if not self.validate():
            raise C2StateValidationError(
                "C2 execution envelope invalid: authorization, mission, or flight state missing."
            )

    def to_context(self) -> dict[str, Any]:
        self.require_valid()
        return {
            "identity": self.identity,
            "mission": self.mission,
            "flight_id": self.flight_id,
            "target": self.target,
            "phase": self.phase,
            "invariants": self.invariants,
            "evidence_requirements": self.evidence_requirements,
        }
