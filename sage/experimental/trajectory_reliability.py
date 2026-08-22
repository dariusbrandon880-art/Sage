"""Fail-closed reliability measurements for longitudinal SAGE trajectories.

This module measures repeated-horizon reliability without becoming a second
qualification authority. It consumes already-observed episode outcomes and
returns descriptive trajectory metrics only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ReliabilityEpisode:
    """One observed episode in a locked longitudinal sequence."""

    episode_id: str
    success: bool
    recovered_after_failure: bool = False
    regression_detected: bool = False
    retained: bool = False
    elapsed_seconds: float | None = None


@dataclass(frozen=True)
class ReliabilityReport:
    """Descriptive trajectory evidence; never a capability verdict."""

    episode_count: int
    success_rate: float
    reliability_decay: float
    recovery_rate: float
    regression_rate: float
    retention_rate: float
    mean_elapsed_seconds: float | None


class TrajectoryReliabilityAnalyzer:
    """Compute repeated-episode reliability metrics from real observations."""

    def analyze(self, episodes: Sequence[ReliabilityEpisode]) -> ReliabilityReport:
        if not episodes:
            raise ValueError("EPISODES_REQUIRED")
        ids = [episode.episode_id for episode in episodes]
        if any(not episode_id for episode_id in ids):
            raise ValueError("EPISODE_ID_REQUIRED")
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_EPISODE_ID")

        successes = [episode.success for episode in episodes]
        success_rate = sum(successes) / len(successes)

        midpoint = max(1, len(episodes) // 2)
        early = successes[:midpoint]
        late = successes[midpoint:]
        early_rate = sum(early) / len(early)
        late_rate = sum(late) / len(late) if late else early_rate

        recovery_cases = [
            episode for episode in episodes
            if episode.recovered_after_failure or episode.regression_detected
        ]
        recovery_rate = (
            sum(episode.recovered_after_failure for episode in recovery_cases)
            / len(recovery_cases)
            if recovery_cases else 1.0
        )
        regression_rate = sum(episode.regression_detected for episode in episodes) / len(episodes)
        retention_rate = sum(episode.retained for episode in episodes) / len(episodes)
        elapsed = [
            episode.elapsed_seconds
            for episode in episodes
            if episode.elapsed_seconds is not None
        ]

        return ReliabilityReport(
            episode_count=len(episodes),
            success_rate=success_rate,
            reliability_decay=early_rate - late_rate,
            recovery_rate=recovery_rate,
            regression_rate=regression_rate,
            retention_rate=retention_rate,
            mean_elapsed_seconds=sum(elapsed) / len(elapsed) if elapsed else None,
        )
