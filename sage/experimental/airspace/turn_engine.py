"""Turn-based SAGE scoring authority.

A turn is the smallest game-loop unit that can connect an agent action to
verified evidence, contribution attribution, Points/XP, and a fresh organism
projection. ChatGPT may describe or propose a contribution, but this module
is the SAGE-side authority that verifies evidence and persists rewards.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory
from sage.experimental.airspace.organism_projection import OrganismAgentProjection, OrganismProjection
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy, PointsXPResult


class TurnStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class TurnContribution:
    """A contribution candidate supplied to SAGE for verification."""

    contribution_id: str
    station_id: StationID
    role: str
    evidence_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...] = ()
    parent_activity_id: str | None = None


@dataclass(frozen=True)
class TurnResolution:
    """Immutable result of resolving one turn."""

    turn_id: str
    sequence_number: int
    status: TurnStatus
    verified: bool
    event_type: PointEventType
    verified_event_ref: str
    total_verified_points: int
    contribution_results: tuple[PointsXPResult, ...]
    projections: tuple[OrganismAgentProjection, ...]

    @property
    def total_xp_minted(self) -> int:
        return sum(result.xp_minted for result in self.contribution_results)


class TurnEngine:
    """Resolve sequential turns against the canonical append-only ledger."""

    def __init__(self, manager: AirspaceManager):
        self.manager = manager

    def open_turn(
        self,
        *,
        actor: str,
        turn_id: str,
        input_ref: str,
        encounter_id: str | None = None,
        mission_id: str | None = None,
    ) -> int:
        """Open the next sequential turn and persist its immutable boundary."""
        if self._turn_exists(turn_id):
            raise ValueError(f"Turn '{turn_id}' already exists.")
        sequence = self._next_sequence()
        self.manager.record_event(
            event_type="TURN_OPENED",
            actor=actor,
            mission_id=mission_id,
            payload={
                "turn_id": turn_id,
                "encounter_id": encounter_id,
                "sequence_number": sequence,
                "input_ref": input_ref,
                "status": TurnStatus.OPEN.value,
            },
            evidence_refs=[input_ref],
        )
        return sequence

    def resolve_turn(
        self,
        *,
        actor: str,
        turn_id: str,
        event_type: PointEventType,
        verified_event_ref: str,
        evidence_refs: tuple[str, ...],
        contributions: Iterable[TurnContribution],
        reason: str,
        category: XPCategory = XPCategory.MISSION_XP,
        difficulty: int = 1,
        verification_quality: int = 1,
        impact: int = 1,
        reuse: int = 1,
    ) -> TurnResolution:
        """Verify and score a turn, splitting one verified outcome deterministically."""
        turn = self._latest_turn(turn_id)
        if turn is None or turn.get("payload", {}).get("status") != TurnStatus.OPEN.value:
            raise ValueError(f"Turn '{turn_id}' is not open.")
        if not verified_event_ref.strip() or not evidence_refs:
            raise ValueError("Turn resolution requires a verified event reference and evidence.")

        contribution_list = tuple(contributions)
        if not contribution_list:
            raise ValueError("Turn resolution requires at least one contribution.")
        for contribution in contribution_list:
            if not contribution.evidence_refs:
                raise ValueError(f"Contribution '{contribution.contribution_id}' requires evidence.")

        # Score the outcome once. Allocation is intentionally equal-share with a
        # deterministic remainder until SAGE has enough empirical data to justify
        # a role/causal weighting policy.
        scored = PointsXPEconomy.score_verified_event(
            event_id=turn_id,
            station_id=contribution_list[0].station_id,
            event_type=event_type,
            verified_event_ref=verified_event_ref,
            evidence_refs=evidence_refs,
            difficulty=difficulty,
            verification_quality=verification_quality,
            impact=impact,
            reuse=reuse,
        )
        allocations = self._equal_share(scored.points, len(contribution_list))
        results: list[PointsXPResult] = []
        for index, (contribution, points) in enumerate(zip(contribution_list, allocations)):
            if points <= 0:
                continue
            contribution_ref = f"{verified_event_ref}:contribution:{contribution.contribution_id}"
            result = PointsXPEconomy.award_verified_event(
                self.manager,
                actor=actor,
                event_id=f"{turn_id}:contribution:{index + 1}",
                station_id=contribution.station_id,
                event_type=event_type,
                verified_event_ref=contribution_ref,
                evidence_refs=tuple(dict.fromkeys(evidence_refs + contribution.evidence_refs + contribution.artifact_refs)),
                reason=f"{reason}; role={contribution.role}; turn={turn_id}",
                category=category,
                base_points=points,
                difficulty=1,
                verification_quality=1,
                impact=1,
                reuse=1,
            )
            results.append(result)
            self.manager.record_event(
                event_type="CONTRIBUTION_VERIFIED",
                actor=actor,
                payload={
                    "turn_id": turn_id,
                    "contribution_id": contribution.contribution_id,
                    "station_id": contribution.station_id.value,
                    "role": contribution.role,
                    "activity_id": contribution.parent_activity_id,
                    "evidence_refs": list(contribution.evidence_refs),
                    "artifact_refs": list(contribution.artifact_refs),
                    "verified_points": points,
                    "verified_event_ref": verified_event_ref,
                },
                evidence_refs=list(dict.fromkeys(evidence_refs + contribution.evidence_refs)),
            )

        self.manager.record_event(
            event_type="TURN_CLOSED",
            actor=actor,
            payload={
                "turn_id": turn_id,
                "sequence_number": turn["payload"]["sequence_number"],
                "status": TurnStatus.CLOSED.value,
                "verified": True,
                "event_type": event_type.value,
                "verified_event_ref": verified_event_ref,
                "total_verified_points": scored.points,
                "contribution_ids": [c.contribution_id for c in contribution_list],
            },
            evidence_refs=list(evidence_refs),
        )

        state = self.manager.reconstruct_airspace_state()
        projections = tuple(
            OrganismProjection.reconcile(self.manager, state, status="READY").values()
        )
        return TurnResolution(
            turn_id=turn_id,
            sequence_number=int(turn["payload"]["sequence_number"]),
            status=TurnStatus.CLOSED,
            verified=True,
            event_type=event_type,
            verified_event_ref=verified_event_ref,
            total_verified_points=scored.points,
            contribution_results=tuple(results),
            projections=projections,
        )

    def render_hud(self, station_id: StationID, *, state_label: str = "READY") -> str:
        """Re-read canonical state and render a fresh organism tag every turn."""
        state = self.manager.reconstruct_airspace_state()
        projection = OrganismProjection.project_station(
            self.manager, state, station_id, status=state_label
        )
        return OrganismProjection.render_agent_tag(projection)

    def _turn_exists(self, turn_id: str) -> bool:
        return self._latest_turn(turn_id) is not None

    def _latest_turn(self, turn_id: str) -> dict | None:
        matches = [
            raw for raw in self.manager._load_raw_events()
            if raw.get("payload", {}).get("turn_id") == turn_id
            and raw.get("event_type") in {"TURN_OPENED", "TURN_CLOSED"}
        ]
        if not matches:
            return None
        return matches[-1]

    def _next_sequence(self) -> int:
        sequences = [
            int(raw.get("payload", {}).get("sequence_number", 0))
            for raw in self.manager._load_raw_events()
            if raw.get("event_type") == "TURN_OPENED"
        ]
        return max(sequences, default=0) + 1

    @staticmethod
    def _equal_share(total: int, count: int) -> tuple[int, ...]:
        base, remainder = divmod(total, count)
        return tuple(base + (1 if index < remainder else 0) for index in range(count))


__all__ = ["TurnContribution", "TurnEngine", "TurnResolution", "TurnStatus"]
