"""Canonical verified Boss outcome accounting for SAGE career immersion.

Boss classification remains upstream and Mission-Director governed. This module
only records an already verified Boss outcome in the existing append-only
Airspace event ledger and reconstructs the locked Queue #02/#08 semantics.
It creates no parallel store and never mutates rank, qualification, Points, or XP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID


class BossClass(str, Enum):
    BIG = "BIG"
    MAJOR = "MAJOR"


BOSS_BADGE_CADENCE = {
    BossClass.MAJOR: 20,
    BossClass.BIG: 30,
}


@dataclass(frozen=True)
class BossOutcome:
    event_id: str
    station_id: StationID
    boss_class: BossClass
    verified_event_ref: str
    evidence_refs: tuple[str, ...]
    kill: bool = False
    capture: bool = False

    def __post_init__(self) -> None:
        if not self.verified_event_ref.strip():
            raise ValueError("Boss outcome requires verified_event_ref")
        if not self.evidence_refs:
            raise ValueError("Boss outcome requires evidence_refs")
        if not self.kill and not self.capture:
            raise ValueError("Boss outcome must contain a verified kill or capture")

    def payload(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "station_id": self.station_id.value,
            "boss_class": self.boss_class.value,
            "verified_event_ref": self.verified_event_ref,
            "kill": self.kill,
            "capture": self.capture,
        }


@dataclass(frozen=True)
class BossProgression:
    big_kills: int = 0
    big_captures: int = 0
    major_kills: int = 0
    major_captures: int = 0
    big_badges: int = 0
    major_badges: int = 0

    @property
    def total_kills(self) -> int:
        return self.big_kills + self.major_kills

    @property
    def total_captures(self) -> int:
        return self.big_captures + self.major_captures

    @property
    def total_badges(self) -> int:
        return self.big_badges + self.major_badges

    @property
    def badge_summary(self) -> str:
        parts = []
        if self.major_badges:
            parts.append(f"⭐⭐×{self.major_badges}")
        if self.big_badges:
            parts.append(f"⭐×{self.big_badges}")
        return " | ".join(parts) if parts else "—"


class BossProgressionAuthority:
    """Record/reconstruct verified Boss outcomes from the canonical event ledger."""

    EVENT_TYPE = "BOSS_OUTCOME_VERIFIED"

    @classmethod
    def record_verified_outcome(
        cls,
        manager: AirspaceManager,
        *,
        actor: str,
        outcome: BossOutcome,
        reason: str,
    ) -> BossOutcome:
        existing = cls._find_by_verified_ref(manager, outcome.verified_event_ref)
        if existing is not None:
            return existing

        manager.record_event(
            event_type=cls.EVENT_TYPE,
            actor=actor,
            payload={**outcome.payload(), "reason": reason},
            evidence_refs=list(outcome.evidence_refs),
        )
        return outcome

    @classmethod
    def _find_by_verified_ref(
        cls, manager: AirspaceManager, verified_event_ref: str
    ) -> Optional[BossOutcome]:
        for raw in manager._load_raw_events():
            if raw.get("event_type") != cls.EVENT_TYPE:
                continue
            payload = raw.get("payload", {})
            if payload.get("verified_event_ref") != verified_event_ref:
                continue
            return cls._from_payload(payload, evidence_refs=tuple(raw.get("evidence_refs", ())))
        return None

    @staticmethod
    def _from_payload(payload: dict[str, object], *, evidence_refs: tuple[str, ...]) -> BossOutcome:
        return BossOutcome(
            event_id=str(payload["event_id"]),
            station_id=StationID(str(payload["station_id"])),
            boss_class=BossClass(str(payload["boss_class"])),
            verified_event_ref=str(payload["verified_event_ref"]),
            evidence_refs=evidence_refs,
            kill=bool(payload.get("kill", False)),
            capture=bool(payload.get("capture", False)),
        )

    @classmethod
    def project_station(
        cls, manager: AirspaceManager, station_id: StationID
    ) -> BossProgression:
        counts = {"big_kills": 0, "big_captures": 0, "major_kills": 0, "major_captures": 0}
        for raw in manager._load_raw_events():
            if raw.get("event_type") != cls.EVENT_TYPE:
                continue
            payload = raw.get("payload", {})
            if payload.get("station_id") != station_id.value:
                continue
            boss_class = BossClass(str(payload["boss_class"]))
            prefix = "big" if boss_class is BossClass.BIG else "major"
            if bool(payload.get("kill", False)):
                counts[f"{prefix}_kills"] += 1
            if bool(payload.get("capture", False)):
                counts[f"{prefix}_captures"] += 1

        big_badges = (counts["big_kills"] // BOSS_BADGE_CADENCE[BossClass.BIG]) + (
            counts["big_captures"] // BOSS_BADGE_CADENCE[BossClass.BIG]
        )
        major_badges = (counts["major_kills"] // BOSS_BADGE_CADENCE[BossClass.MAJOR]) + (
            counts["major_captures"] // BOSS_BADGE_CADENCE[BossClass.MAJOR]
        )
        return BossProgression(**counts, big_badges=big_badges, major_badges=major_badges)

    @classmethod
    def project_from_state(cls, manager: AirspaceManager, station_id: StationID) -> BossProgression:
        """Alias emphasizing that reconstruction is from canonical persisted state."""
        return cls.project_station(manager, station_id)
