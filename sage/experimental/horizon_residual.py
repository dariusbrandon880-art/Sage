"""Fail-closed horizon-residual measurements for longitudinal SAGE flights.

The analyzer compares observed short-horizon reliability with observed
long-horizon reliability for matched episodes. It is descriptive evidence only:
it never qualifies capability, mutates state, or changes evaluation authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class HorizonEpisode:
    """One observed episode with an explicit horizon classification."""

    episode_id: str
    horizon: str
    success: bool
    recovered_after_failure: bool = False
    retained: bool = False
    regression_detected: bool = False


@dataclass(frozen=True)
class HorizonResidualReport:
    """Observed horizon residual; never a capability verdict."""

    short_episode_count: int
    long_episode_count: int
    short_success_rate: float
    long_success_rate: float
    observed_long_horizon_residual: float
    long_recovery_rate: float
    long_retention_rate: float
    long_regression_rate: float


class HorizonResidualAnalyzer:
    """Measure observed short-to-long reliability loss on a matched stream."""

    def analyze(self, episodes: Sequence[HorizonEpisode]) -> HorizonResidualReport:
        if not episodes:
            raise ValueError("EPISODES_REQUIRED")
        if any(not episode.episode_id for episode in episodes):
            raise ValueError("EPISODE_ID_REQUIRED")
        if len({episode.episode_id for episode in episodes}) != len(episodes):
            raise ValueError("DUPLICATE_EPISODE_ID")
        if any(episode.horizon not in {"short", "long"} for episode in episodes):
            raise ValueError("INVALID_HORIZON")

        short = [episode for episode in episodes if episode.horizon == "short"]
        long = [episode for episode in episodes if episode.horizon == "long"]
        if not short or not long:
            raise ValueError("SHORT_AND_LONG_EPISODES_REQUIRED")

        short_success_rate = sum(e.success for e in short) / len(short)
        long_success_rate = sum(e.success for e in long) / len(long)
        recovery_cases = [e for e in long if e.recovered_after_failure or e.regression_detected]
        long_recovery_rate = (
            sum(e.recovered_after_failure for e in recovery_cases) / len(recovery_cases)
            if recovery_cases else 1.0
        )

        return HorizonResidualReport(
            short_episode_count=len(short),
            long_episode_count=len(long),
            short_success_rate=short_success_rate,
            long_success_rate=long_success_rate,
            observed_long_horizon_residual=short_success_rate - long_success_rate,
            long_recovery_rate=long_recovery_rate,
            long_retention_rate=sum(e.retained for e in long) / len(long),
            long_regression_rate=sum(e.regression_detected for e in long) / len(long),
        )
