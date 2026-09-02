"""Verified Points -> Career XP economy for SAGE career progression.

Points are event-level performance accounting. Career XP is durable progression.
Both require evidence-backed, unique verified events. This module composes with
existing Airspace/GameProgression state and does not create a second career store.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable


class PointEventType(str, Enum):
    RECON = "RECON"
    ANALYSIS = "ANALYSIS"
    BUILD = "BUILD"
    REPAIR = "REPAIR"
    VERIFICATION = "VERIFICATION"
    BREAKTHROUGH = "BREAKTHROUGH"
    CAPABILITY_CAPTURE = "CAPABILITY_CAPTURE"
    BOSS_KILL = "BOSS_KILL"
    BOSS_CAPTURE = "BOSS_CAPTURE"
    COLLABORATION = "COLLABORATION"
    REUSE = "REUSE"
    RECOVERY = "RECOVERY"


@dataclass(frozen=True)
class PointAward:
    event_id: str
    agent_id: str
    event_type: PointEventType
    base_points: int
    difficulty: int
    verification_quality: int
    impact: int
    reuse: int
    verified_event_ref: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.base_points <= 0:
            raise ValueError("Point award rejected: base_points must be positive.")
        for name, value in (("difficulty", self.difficulty), ("verification_quality", self.verification_quality), ("impact", self.impact), ("reuse", self.reuse)):
            if value < 1 or value > 5:
                raise ValueError(f"Point award rejected: {name} must be between 1 and 5.")
        if not self.verified_event_ref.strip():
            raise ValueError("Point award rejected: verified_event_ref is required.")
        if not self.evidence_refs:
            raise ValueError("Point award rejected: evidence_refs are required.")

    @property
    def verified_points(self) -> int:
        return max(1, round(self.base_points * self.difficulty * self.verification_quality * self.impact * self.reuse / 625))


class PointsLedger:
    """Append-only point ledger with replay protection and deterministic XP conversion."""

    POINTS_PER_XP = 10

    def __init__(self, awards: Iterable[PointAward] = ()) -> None:
        self._awards: Dict[str, PointAward] = {}
        for award in awards:
            self.record(award)

    def record(self, award: PointAward) -> PointAward:
        existing = self._awards.get(award.verified_event_ref)
        if existing is not None:
            if existing != award:
                raise ValueError("Point award rejected: verified_event_ref already belongs to a different award.")
            return existing
        self._awards[award.verified_event_ref] = award
        return award

    def awards(self) -> tuple[PointAward, ...]:
        return tuple(self._awards.values())

    def verified_points_for_agent(self, agent_id: str) -> int:
        return sum(a.verified_points for a in self._awards.values() if a.agent_id == agent_id)

    def verified_points_total(self) -> int:
        return sum(a.verified_points for a in self._awards.values())

    def career_xp_for_agent(self, agent_id: str) -> int:
        return self.verified_points_for_agent(agent_id) // self.POINTS_PER_XP

    def career_xp_total(self) -> int:
        return self.verified_points_total() // self.POINTS_PER_XP

    def unconverted_points_for_agent(self, agent_id: str) -> int:
        return self.verified_points_for_agent(agent_id) % self.POINTS_PER_XP
