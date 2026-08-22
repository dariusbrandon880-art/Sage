import pytest

from sage.experimental.horizon_residual import HorizonEpisode, HorizonResidualAnalyzer


def test_horizon_residual_measures_observed_long_horizon_loss() -> None:
    report = HorizonResidualAnalyzer().analyze(
        [
            HorizonEpisode("s1", "short", True),
            HorizonEpisode("s2", "short", True),
            HorizonEpisode("l1", "long", True, retained=True),
            HorizonEpisode("l2", "long", False, recovered_after_failure=True),
        ]
    )

    assert report.short_success_rate == 1.0
    assert report.long_success_rate == 0.5
    assert report.observed_long_horizon_residual == 0.5
    assert report.long_recovery_rate == 1.0
    assert report.long_retention_rate == 0.5
    assert report.long_regression_rate == 0.0


def test_horizon_residual_requires_both_horizons() -> None:
    with pytest.raises(ValueError, match="SHORT_AND_LONG_EPISODES_REQUIRED"):
        HorizonResidualAnalyzer().analyze([HorizonEpisode("s1", "short", True)])


def test_horizon_residual_rejects_duplicate_episode_ids() -> None:
    with pytest.raises(ValueError, match="DUPLICATE_EPISODE_ID"):
        HorizonResidualAnalyzer().analyze(
            [
                HorizonEpisode("same", "short", True),
                HorizonEpisode("same", "long", True),
            ]
        )


def test_horizon_residual_rejects_unknown_horizon() -> None:
    with pytest.raises(ValueError, match="INVALID_HORIZON"):
        HorizonResidualAnalyzer().analyze(
            [
                HorizonEpisode("s1", "short", True),
                HorizonEpisode("x1", "medium", True),
            ]
        )
