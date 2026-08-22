"""Adversarial tests for longitudinal trajectory reliability metrics."""

import pytest

from sage.experimental.trajectory_reliability import (
    ReliabilityEpisode,
    TrajectoryReliabilityAnalyzer,
)


def test_measures_decay_recovery_regression_retention_and_time():
    episodes = [
        ReliabilityEpisode("e1", True, retained=True, elapsed_seconds=10),
        ReliabilityEpisode("e2", True, retained=True, elapsed_seconds=20),
        ReliabilityEpisode("e3", False, recovered_after_failure=True, retained=True, elapsed_seconds=30),
        ReliabilityEpisode("e4", True, regression_detected=True, retained=False, elapsed_seconds=40),
    ]

    report = TrajectoryReliabilityAnalyzer().analyze(episodes)

    assert report.episode_count == 4
    assert report.success_rate == 0.75
    assert report.reliability_decay == 0.5
    assert report.recovery_rate == 0.5
    assert report.regression_rate == 0.25
    assert report.retention_rate == 0.75
    assert report.mean_elapsed_seconds == 25


def test_empty_or_duplicate_episode_stream_fails_closed():
    analyzer = TrajectoryReliabilityAnalyzer()

    with pytest.raises(ValueError, match="EPISODES_REQUIRED"):
        analyzer.analyze([])

    with pytest.raises(ValueError, match="DUPLICATE_EPISODE_ID"):
        analyzer.analyze([
            ReliabilityEpisode("same", True),
            ReliabilityEpisode("same", True),
        ])


def test_missing_episode_id_fails_closed():
    with pytest.raises(ValueError, match="EPISODE_ID_REQUIRED"):
        TrajectoryReliabilityAnalyzer().analyze([ReliabilityEpisode("", True)])
