"""Operational verified Points -> Career XP integration.

This layer uses the existing AirspaceManager append-only event ledger as its
persistence boundary. It does not create a second career store and it never
awards progression from unverified activity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory


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


BASE_POINTS: Dict[PointEventType, int] = {
    PointEventType.RECON: 5,
    PointEventType.ANALYSIS: 10,
    PointEventType.BUILD: 25,
    PointEventType.REPAIR: 25,
    PointEventType.VERIFICATION: 10,
    PointEventType.BREAKTHROUGH: 50,
    PointEventType.CAPABILITY_CAPTURE: 100,
    PointEventType.BOSS_KILL: 100,
    PointEventType.BOSS_CAPTURE: 100,
    PointEventType.COLLABORATION: 10,
    PointEventType.REUSE: 50,
    PointEventType.RECOVERY: 25,
}


@dataclass(frozen=True)
class VerifiedPointAward:
    event_id: str
    station_id: StationID
    event_type: PointEventType
    base_points: int
    difficulty: int
    verification_quality: int
    impact: int
    reuse: int
    verified_event_ref: str
    evidence_refs: tuple[str, ...]

    @property
    def points(self) -> int:
        """Score from 1x through 5x base value using a bounded average multiplier."""
        return max(1, round(self.base_points * (self.difficulty + self.verification_quality + self.impact + self.reuse) / 4))

    def model_payload(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "station_id": self.station_id.value,
            "event_type": self.event_type.value,
            "base_points": self.base_points,
            "difficulty": self.difficulty,
            "verification_quality": self.verification_quality,
            "impact": self.impact,
            "reuse": self.reuse,
            "verified_points": self.points,
            "verified_event_ref": self.verified_event_ref,
        }


@dataclass(frozen=True)
class PointsXPResult:
    award: VerifiedPointAward
    cumulative_verified_points: int
    cumulative_career_xp: int
    xp_minted: int


class PointsXPEconomy:
    """Translate verified event value into persistent Points and deterministic XP."""

    POINTS_PER_XP = 10

    @staticmethod
    def base_points(event_type: PointEventType) -> int:
        return BASE_POINTS[event_type]

    @staticmethod
    def _validate_dimensions(difficulty: int, verification_quality: int, impact: int, reuse: int) -> None:
        for name, value in (
            ("difficulty", difficulty),
            ("verification_quality", verification_quality),
            ("impact", impact),
            ("reuse", reuse),
        ):
            if value < 1 or value > 5:
                raise ValueError(f"{name} must be between 1 and 5")

    @classmethod
    def score_verified_event(
        cls,
        *,
        event_id: str,
        station_id: StationID,
        event_type: PointEventType,
        verified_event_ref: str,
        evidence_refs: tuple[str, ...],
        base_points: Optional[int] = None,
        difficulty: int = 1,
        verification_quality: int = 1,
        impact: int = 1,
        reuse: int = 1,
    ) -> VerifiedPointAward:
        if not verified_event_ref.strip():
            raise ValueError("Verified point award rejected: verified_event_ref is required.")
        if not evidence_refs:
            raise ValueError("Verified point award rejected: evidence_refs are required.")
        cls._validate_dimensions(difficulty, verification_quality, impact, reuse)
        resolved_base = base_points if base_points is not None else cls.base_points(event_type)
        if resolved_base <= 0:
            raise ValueError("Verified point award rejected: base_points must be positive.")
        return VerifiedPointAward(
            event_id=event_id,
            station_id=station_id,
            event_type=event_type,
            base_points=resolved_base,
            difficulty=difficulty,
            verification_quality=verification_quality,
            impact=impact,
            reuse=reuse,
            verified_event_ref=verified_event_ref,
            evidence_refs=evidence_refs,
        )

    @staticmethod
    def _historical_points(manager: AirspaceManager, station_id: StationID) -> int:
        total = 0
        for raw in manager._load_raw_events():
            if raw.get("event_type") != "POINTS_AWARDED":
                continue
            payload = raw.get("payload", {})
            if payload.get("station_id") == station_id.value:
                total += int(payload.get("verified_points", 0))
        return total

    @classmethod
    def verified_points_for_station(cls, manager: AirspaceManager, station_id: StationID) -> int:
        """Return reconstructed verified Points from the canonical event ledger."""
        return cls._historical_points(manager, station_id)

    @staticmethod
    def _find_existing_points_event(manager: AirspaceManager, verified_event_ref: str) -> Optional[dict[str, object]]:
        for raw in manager._load_raw_events():
            if raw.get("event_type") != "POINTS_AWARDED":
                continue
            payload = raw.get("payload", {})
            if payload.get("verified_event_ref") == verified_event_ref:
                return payload
        return None

    @classmethod
    def award_verified_event(
        cls,
        manager: AirspaceManager,
        *,
        actor: str,
        event_id: str,
        station_id: StationID,
        event_type: PointEventType,
        verified_event_ref: str,
        evidence_refs: tuple[str, ...],
        reason: str,
        category: XPCategory = XPCategory.MISSION_XP,
        base_points: Optional[int] = None,
        difficulty: int = 1,
        verification_quality: int = 1,
        impact: int = 1,
        reuse: int = 1,
    ) -> PointsXPResult:
        """Persist one verified point event and mint only newly earned whole XP."""
        existing = cls._find_existing_points_event(manager, verified_event_ref)
        if existing is not None:
            award = cls.score_verified_event(
                event_id=str(existing["event_id"]),
                station_id=StationID(str(existing["station_id"])),
                event_type=PointEventType(str(existing["event_type"])),
                verified_event_ref=str(existing["verified_event_ref"]),
                evidence_refs=tuple(evidence_refs),
                base_points=int(existing["base_points"]),
                difficulty=int(existing["difficulty"]),
                verification_quality=int(existing["verification_quality"]),
                impact=int(existing["impact"]),
                reuse=int(existing["reuse"]),
            )
        else:
            award = cls.score_verified_event(
                event_id=event_id,
                station_id=station_id,
                event_type=event_type,
                verified_event_ref=verified_event_ref,
                evidence_refs=evidence_refs,
                base_points=base_points,
                difficulty=difficulty,
                verification_quality=verification_quality,
                impact=impact,
                reuse=reuse,
            )
            manager.record_event(
                event_type="POINTS_AWARDED",
                actor=actor,
                payload={**award.model_payload(), "reason": reason},
                evidence_refs=list(evidence_refs),
            )

        cumulative_points = cls._historical_points(manager, station_id)
        target_xp = cumulative_points // cls.POINTS_PER_XP
        current_xp = manager.reconstruct_airspace_state().game_progression.get_total_xp_for_station(station_id)
        xp_minted = max(0, target_xp - current_xp)

        if xp_minted:
            manager.award_xp(
                actor=actor,
                station_id=station_id,
                category=category,
                amount=xp_minted,
                reason=f"Career XP minted from {cumulative_points} verified Points ({reason})",
                verified_event_ref=f"{verified_event_ref}:xp:{target_xp}",
            )

        return PointsXPResult(
            award=award,
            cumulative_verified_points=cumulative_points,
            cumulative_career_xp=target_xp,
            xp_minted=xp_minted,
        )
