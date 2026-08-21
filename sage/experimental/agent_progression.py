"""Verified agent progression and immersive mission status.

This is a thin experimental layer over SAGE's existing mission/evidence model.
Progression is earned only from externally supplied verified events; the module
never self-attests success, capability, or rank.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class AgentRank(str, Enum):
    """CQL progression ranks; every station starts at CQL-0."""

    CQL_0 = "CQL-0"
    CQL_1 = "CQL-1"
    CQL_2 = "CQL-2"
    CQL_3 = "CQL-3"
    CQL_4 = "CQL-4"
    CQL_5 = "CQL-5"
    CQL_6 = "CQL-6"
    CQL_7 = "CQL-7"


class ProgressionEventKind(str, Enum):
    """Only verified event classes may award or remove progression XP."""

    MISSION_SUCCESS = "MISSION_SUCCESS"
    VERIFIED_CAPABILITY = "VERIFIED_CAPABILITY"
    FAILURE_RECOVERY = "FAILURE_RECOVERY"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"


@dataclass(frozen=True)
class VerifiedProgressionEvent:
    """A referee-issued event; callers must supply the verification reference."""

    event_id: str
    agent_id: str
    mission_id: str
    kind: ProgressionEventKind
    xp_delta: int
    verification_reference: str
    capability: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id or not self.agent_id or not self.mission_id:
            raise ValueError("Progression event identity is required")
        if not self.verification_reference:
            raise ValueError("Progression events require independent verification")
        if self.kind == ProgressionEventKind.GOVERNANCE_VIOLATION and self.xp_delta > 0:
            raise ValueError("Governance violations cannot award XP")
        if self.kind != ProgressionEventKind.GOVERNANCE_VIOLATION and self.xp_delta <= 0:
            raise ValueError("Positive progression events require positive XP")


@dataclass
class AgentProgression:
    """Durable-in-memory progression state for one operating station."""

    agent_id: str
    station: str
    xp: int = 0
    events: list[VerifiedProgressionEvent] = field(default_factory=list)

    def apply(self, event: VerifiedProgressionEvent) -> None:
        if event.agent_id != self.agent_id:
            raise ValueError("Progression event belongs to a different agent")
        if any(existing.event_id == event.event_id for existing in self.events):
            raise ValueError("Duplicate progression event")
        self.events.append(event)
        self.xp = max(0, self.xp + event.xp_delta)

    @property
    def rank(self) -> AgentRank:
        """Rank is derived from verified XP only; thresholds are intentionally conservative."""
        thresholds = (0, 100, 250, 500, 900, 1400, 2100, 3000)
        rank = AgentRank.CQL_0
        for index, threshold in enumerate(thresholds):
            if self.xp >= threshold:
                rank = AgentRank(f"CQL-{index}")
        return rank

    @property
    def mission_count(self) -> int:
        return len({event.mission_id for event in self.events})

    @property
    def governance_violations(self) -> int:
        return sum(event.kind == ProgressionEventKind.GOVERNANCE_VIOLATION for event in self.events)

    def qualification(self, capability: str) -> bool:
        """Qualification requires verified capability evidence, not XP alone."""
        return any(
            event.kind == ProgressionEventKind.VERIFIED_CAPABILITY
            and event.capability == capability
            for event in self.events
        )

    def canonical_digest(self) -> str:
        payload = {
            "agent_id": self.agent_id,
            "station": self.station,
            "xp": self.xp,
            "events": [
                {
                    "event_id": event.event_id,
                    "mission_id": event.mission_id,
                    "kind": event.kind.value,
                    "xp_delta": event.xp_delta,
                    "verification_reference": event.verification_reference,
                    "capability": event.capability,
                }
                for event in self.events
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def build_flight_status(
    *,
    theater: str,
    mission_id: str,
    frontier: str,
    threat: str,
    victory_condition: str,
    agent: AgentProgression,
) -> str:
    """Render a truthful, compact C2-style status card from canonical state."""
    qualification = "none"
    capabilities = sorted(
        {
            event.capability
            for event in agent.events
            if event.kind == ProgressionEventKind.VERIFIED_CAPABILITY and event.capability
        }
    )
    if capabilities:
        qualification = ", ".join(capabilities)

    return "\n".join(
        [
            "C2 FLIGHT STATUS",
            f"THEATER: {theater}",
            f"MISSION: {mission_id}",
            f"FRONTIER: {frontier}",
            f"THREAT: {threat}",
            f"AGENT: {agent.station} / {agent.agent_id}",
            f"RANK: {agent.rank.value}  XP: {agent.xp}",
            f"MISSIONS: {agent.mission_count}",
            f"QUALIFIED: {qualification}",
            f"GOVERNANCE VIOLATIONS: {agent.governance_violations}",
            f"VICTORY CONDITION: {victory_condition}",
        ]
    )


def apply_verified_events(
    agent: AgentProgression,
    events: Iterable[VerifiedProgressionEvent],
) -> AgentProgression:
    """Apply a verified event stream in order and return the updated agent state."""
    for event in events:
        agent.apply(event)
    return agent
