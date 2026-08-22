"""Adversarial tests for governed longitudinal evidence composition."""

import pytest

from sage.experimental.longitudinal_evidence import (
    AttributedEpisode,
    LongitudinalEvidenceComposer,
)
from sage.experimental.trajectory_reliability import ReliabilityEpisode


def _episode(observation_id: str, mission_id: str, success: bool, *, retained: bool = True) -> AttributedEpisode:
    return AttributedEpisode(
        episode=ReliabilityEpisode(
            episode_id=observation_id,
            success=success,
            retained=retained,
            recovered_after_failure=not success,
        ),
        system="baseline",
        mission_id=mission_id,
        session_id=f"session-{observation_id}",
        observation_id=observation_id,
        provenance_digest=f"digest-{observation_id}",
    )


def test_composes_matched_baseline_and_sage_evidence_with_digest():
    baseline = [_episode("b1", "m1", True), _episode("b2", "m2", False)]
    sage = [_episode("s1", "m1", True), _episode("s2", "m2", True)]
    sage = [
        AttributedEpisode(
            episode=item.episode,
            system="sage",
            mission_id=item.mission_id,
            session_id=item.session_id,
            observation_id=item.observation_id,
            provenance_digest=item.provenance_digest,
        )
        for item in sage
    ]

    report = LongitudinalEvidenceComposer().compose(baseline, sage)

    assert report.baseline.success_rate == 0.5
    assert report.sage.success_rate == 1.0
    assert report.relative_success_gain == 1.0
    assert report.provenance_complete is True
    assert report.attribution_complete is True
    assert len(report.receipt_digest) == 64


def test_mismatched_mission_sets_fail_closed():
    baseline = [_episode("b1", "m1", True)]
    sage = [_episode("s1", "m2", True)]

    with pytest.raises(ValueError, match="BASELINE_SAGE_MISSION_SET_MISMATCH"):
        LongitudinalEvidenceComposer().compose(baseline, sage)


def test_missing_provenance_fails_closed():
    item = _episode("b1", "m1", True)
    invalid = AttributedEpisode(
        episode=item.episode,
        system="baseline",
        mission_id=item.mission_id,
        session_id=item.session_id,
        observation_id=item.observation_id,
        provenance_digest="",
    )

    with pytest.raises(ValueError, match="BASELINE_PROVENANCE_REQUIRED"):
        LongitudinalEvidenceComposer().compose([invalid], [
            _episode("s1", "m1", True),
        ])
