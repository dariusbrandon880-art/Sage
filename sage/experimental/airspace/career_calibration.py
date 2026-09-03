"""Research-only replay harness for Queue #09 career-threshold calibration.

This module deliberately does not define authoritative promotion thresholds or
mutate career/rank state. It replays supplied verified-event observations
through the canonical Points -> XP economy and evaluates configurable,
non-authoritative threshold curve candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence

from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy


class Profile(str, Enum):
    ROUTINE = "routine"
    BUILDER = "builder"
    BREAKTHROUGH = "breakthrough"
    ELITE = "elite"
    COLLABORATIVE = "collaborative"
    RECOVERY_HEAVY = "recovery-heavy"


@dataclass(frozen=True)
class CalibrationEvent:
    """One verified event observation or simulation input."""

    event_id: str
    event_type: PointEventType
    difficulty: int = 1
    verification_quality: int = 1
    impact: int = 1
    reuse: int = 1
    volume: int = 1

    def __post_init__(self) -> None:
        if self.volume <= 0:
            raise ValueError("volume must be positive")


@dataclass(frozen=True)
class ReplayStep:
    event_index: int
    event_id: str
    event_type: PointEventType
    points: int
    cumulative_points: int
    cumulative_xp: int


@dataclass(frozen=True)
class PromotionInputs:
    """Inputs used only for research readiness evaluation."""

    current_rank: int
    next_rank: int
    lifetime_xp: int
    threshold_xp: int
    qualification_ok: bool
    evidence_ok: bool


@dataclass(frozen=True)
class PromotionReadiness:
    xp_threshold_reached: bool
    eligible: bool
    reason: str


class ThresholdCurve:
    """Non-authoritative candidate threshold curve interface."""

    name = "base"

    def threshold(self, rank: int) -> int:
        raise NotImplementedError

    def thresholds(self, first_rank: int, last_rank: int) -> tuple[int, ...]:
        values = tuple(self.threshold(rank) for rank in range(first_rank, last_rank + 1))
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{self.name} produced non-monotonic thresholds: {values}")
        return values


@dataclass(frozen=True)
class IncreasingDeltaCurve(ThresholdCurve):
    """Cumulative thresholds with a linearly increasing increment."""

    start_threshold: int
    first_delta: int
    delta_growth: int
    name: str = "increasing-delta"

    def threshold(self, rank: int) -> int:
        if rank < 1:
            raise ValueError("rank must be >= 1")
        if min(self.start_threshold, self.first_delta, self.delta_growth) < 0:
            raise ValueError("curve parameters must be non-negative")
        if rank == 1:
            return self.start_threshold
        steps = rank - 1
        return self.start_threshold + steps * self.first_delta + self.delta_growth * steps * (steps - 1) // 2


@dataclass(frozen=True)
class PiecewiseBandCurve(ThresholdCurve):
    """Cumulative thresholds using supplied per-rank deltas by six bands."""

    start_threshold: int
    band_deltas: tuple[int, int, int, int, int, int]
    name: str = "piecewise-band"

    def threshold(self, rank: int) -> int:
        if not 1 <= rank <= 30:
            raise ValueError("rank must be in the 1..30 ladder")
        if self.start_threshold < 0 or any(delta < 0 for delta in self.band_deltas):
            raise ValueError("curve parameters must be non-negative")
        total = self.start_threshold
        for prior_rank in range(2, rank + 1):
            band = (prior_rank - 2) // 5
            total += self.band_deltas[band]
        return total


@dataclass(frozen=True)
class HybridCurve(ThresholdCurve):
    """Increasing-delta curve plus explicit research-only corrections."""

    base: IncreasingDeltaCurve
    corrections: Mapping[int, int]
    name: str = "hybrid"

    def threshold(self, rank: int) -> int:
        value = self.base.threshold(rank) + self.corrections.get(rank, 0)
        if value < 0:
            raise ValueError("hybrid threshold cannot be negative")
        return value

    def thresholds(self, first_rank: int, last_rank: int) -> tuple[int, ...]:
        values = tuple(self.threshold(rank) for rank in range(first_rank, last_rank + 1))
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{self.name} produced non-monotonic thresholds: {values}")
        return values


def replay_events(events: Iterable[CalibrationEvent]) -> tuple[ReplayStep, ...]:
    """Replay event inputs through the canonical verified-event scoring formula."""
    cumulative_points = 0
    previous_xp = 0
    steps: list[ReplayStep] = []
    for index, event in enumerate(events):
        for occurrence in range(event.volume):
            award = PointsXPEconomy.score_verified_event(
                event_id=f"{event.event_id}:{occurrence}",
                station_id=StationID.MISSION_CONTROL,
                event_type=event.event_type,
                verified_event_ref=f"calibration:{event.event_id}:{occurrence}",
                evidence_refs=(f"calibration-evidence:{event.event_id}",),
                difficulty=event.difficulty,
                verification_quality=event.verification_quality,
                impact=event.impact,
                reuse=event.reuse,
            )
            cumulative_points += award.points
            cumulative_xp = cumulative_points // PointsXPEconomy.POINTS_PER_XP
            steps.append(
                ReplayStep(
                    event_index=index,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    points=award.points,
                    cumulative_points=cumulative_points,
                    cumulative_xp=cumulative_xp,
                )
            )
            previous_xp = cumulative_xp
    return tuple(steps)


def evaluate_readiness(inputs: PromotionInputs) -> PromotionReadiness:
    """Separate XP threshold crossing from actual governed eligibility."""
    if inputs.next_rank != inputs.current_rank + 1:
        return PromotionReadiness(False, False, "sequential-next-rank invariant failed")
    if inputs.lifetime_xp < inputs.threshold_xp:
        return PromotionReadiness(False, False, "candidate XP threshold not reached")
    if not inputs.qualification_ok:
        return PromotionReadiness(True, False, "qualification gate not satisfied")
    if not inputs.evidence_ok:
        return PromotionReadiness(True, False, "promotion evidence gate not satisfied")
    return PromotionReadiness(True, True, "research candidate is threshold-ready and gate inputs are satisfied")


def profile_events(profile: Profile) -> tuple[CalibrationEvent, ...]:
    """Return deterministic simulation inputs; these are not empirical observations."""
    common = dict(difficulty=2, verification_quality=4, impact=2, reuse=2)
    if profile == Profile.ROUTINE:
        return (
            CalibrationEvent("routine-recon", PointEventType.RECON, **common, volume=20),
            CalibrationEvent("routine-analysis", PointEventType.ANALYSIS, **common, volume=10),
            CalibrationEvent("routine-verification", PointEventType.VERIFICATION, **common, volume=10),
        )
    if profile == Profile.BUILDER:
        return (
            CalibrationEvent("builder-build", PointEventType.BUILD, difficulty=3, verification_quality=4, impact=3, reuse=3, volume=12),
            CalibrationEvent("builder-repair", PointEventType.REPAIR, **common, volume=8),
            CalibrationEvent("builder-verification", PointEventType.VERIFICATION, **common, volume=8),
        )
    if profile == Profile.BREAKTHROUGH:
        return (
            CalibrationEvent("breakthrough-build", PointEventType.BUILD, difficulty=3, verification_quality=4, impact=4, reuse=3, volume=10),
            CalibrationEvent("breakthrough", PointEventType.BREAKTHROUGH, difficulty=4, verification_quality=5, impact=5, reuse=4, volume=2),
            CalibrationEvent("breakthrough-capture", PointEventType.CAPABILITY_CAPTURE, difficulty=4, verification_quality=5, impact=5, reuse=5, volume=1),
        )
    if profile == Profile.ELITE:
        return (
            CalibrationEvent("elite-routine", PointEventType.BUILD, **common, volume=15),
            CalibrationEvent("elite-boss", PointEventType.BOSS_CAPTURE, difficulty=5, verification_quality=5, impact=5, reuse=5, volume=1),
            CalibrationEvent("elite-recovery", PointEventType.RECOVERY, **common, volume=3),
        )
    if profile == Profile.COLLABORATIVE:
        return (
            CalibrationEvent("collab-analysis", PointEventType.ANALYSIS, **common, volume=10),
            CalibrationEvent("collab-work", PointEventType.COLLABORATION, difficulty=3, verification_quality=5, impact=3, reuse=4, volume=12),
            CalibrationEvent("collab-reuse", PointEventType.REUSE, difficulty=3, verification_quality=5, impact=4, reuse=5, volume=4),
        )
    return (
        CalibrationEvent("recovery-failure", PointEventType.RECOVERY, difficulty=4, verification_quality=4, impact=3, reuse=2, volume=12),
        CalibrationEvent("recovery-repair", PointEventType.REPAIR, **common, volume=10),
        CalibrationEvent("recovery-verification", PointEventType.VERIFICATION, **common, volume=10),
    )


def summarize_profiles(profiles: Sequence[Profile] = tuple(Profile)) -> dict[str, dict[str, int]]:
    """Produce a compact deterministic simulation dataset for later comparison."""
    summary: dict[str, dict[str, int]] = {}
    for profile in profiles:
        replay = replay_events(profile_events(profile))
        summary[profile.value] = {
            "verified_events": len(replay),
            "verified_points": replay[-1].cumulative_points if replay else 0,
            "career_xp": replay[-1].cumulative_xp if replay else 0,
        }
    return summary
