"""Adversarial tests for QualificationAssessment v0.1."""

from dataclasses import FrozenInstanceError

import pytest

from sage.core.qualification_assessment import (
    CapabilityEvidenceEpisode,
    EpisodeVerdict,
    FailureAttribution,
    QualificationAssessment,
    QualificationAssessmentValidationError,
    QualificationRecommendation,
)


def ep(
    digest,
    verdict=EpisodeVerdict.VERIFIED_SUPPORT,
    attribution=FailureAttribution.NONE,
    weight=1.0,
    independent=True,
):
    return CapabilityEvidenceEpisode(
        digest,
        "capability.alpha",
        verdict,
        attribution,
        weight,
        independent,
    )


def assess(*episodes):
    return QualificationAssessment.assess(
        capability_id="capability.alpha",
        episodes=episodes,
    )


def test_three_independent_supports_recommend_without_promotion():
    result = assess(ep("a"), ep("b"), ep("c"))
    assert result.recommendation is QualificationRecommendation.PROMOTION_RECOMMENDED
    assert result.confidence_score == 1.0
    assert result.reviewer_authorization_required is True
    assert result.authority_granted is False
    assert result.current_qualification_state == "UNQUALIFIED"


def test_single_success_does_not_qualify():
    assert assess(ep("a")).recommendation is QualificationRecommendation.HOLD


def test_two_successes_do_not_meet_minimum_episode_count():
    result = assess(ep("a"), ep("b"))
    assert result.recommendation is QualificationRecommendation.HOLD


def test_environment_noise_is_not_agent_fault():
    result = assess(
        ep("a"),
        ep("b"),
        ep(
            "c",
            EpisodeVerdict.VERIFIED_CONTRADICTION,
            FailureAttribution.ENVIRONMENT_NOISE,
        ),
    )
    assert result.agent_fault_rate == 0.0
    assert result.recommendation is QualificationRecommendation.HOLD


def test_contradiction_blocks_promotion():
    result = assess(
        ep("a"),
        ep("b"),
        ep("c"),
        ep(
            "d",
            EpisodeVerdict.VERIFIED_CONTRADICTION,
            FailureAttribution.AGENT_FAULT,
        ),
    )
    assert result.confidence_score == 0.75
    assert result.recommendation is QualificationRecommendation.HOLD


def test_indeterminate_and_unresolved_are_not_positive_evidence():
    result = assess(
        ep("a"),
        ep("b", EpisodeVerdict.UNRESOLVED, FailureAttribution.UNKNOWN),
        ep("c", EpisodeVerdict.INDETERMINATE, FailureAttribution.UNKNOWN),
    )
    assert result.confidence_score == 1.0
    assert result.recommendation is QualificationRecommendation.HOLD


def test_non_independent_episode_does_not_satisfy_minimum():
    result = assess(
        ep("a"),
        ep("b", independent=False),
        ep("c", independent=False),
    )
    assert len(result.independent_episodes) == 1
    assert result.recommendation is QualificationRecommendation.HOLD


def test_weight_changes_digest_deterministically():
    first = assess(ep("a", weight=1.0), ep("b"), ep("c"))
    second = assess(ep("a", weight=0.5), ep("b"), ep("c"))
    assert first.assessment_digest != second.assessment_digest
    assert first.confidence_score == second.confidence_score == 1.0


def test_replay_is_deterministic():
    items = (ep("a", weight=0.8), ep("b", weight=0.9), ep("c"))
    assert assess(*items).assessment_digest == assess(*items).assessment_digest


def test_mutation_is_blocked():
    result = assess(ep("a"), ep("b"), ep("c"))
    with pytest.raises(FrozenInstanceError):
        result.capability_id = "other"  # type: ignore[misc]


def test_support_cannot_carry_failure_attribution():
    with pytest.raises(QualificationAssessmentValidationError):
        ep("a", attribution=FailureAttribution.AGENT_FAULT)


def test_contradiction_requires_failure_attribution():
    with pytest.raises(QualificationAssessmentValidationError):
        ep("a", verdict=EpisodeVerdict.VERIFIED_CONTRADICTION)


def test_invalid_weight_fails_closed():
    with pytest.raises(QualificationAssessmentValidationError):
        ep("a", weight=0.0)


def test_projection_contains_governance_fields():
    projection = assess(ep("a"), ep("b"), ep("c")).to_dict()
    expected_fields = {
        "capability_id",
        "confidence_score",
        "recommendation",
        "current_qualification_state",
        "reviewer_authorization_required",
        "authority_granted",
        "agent_fault_rate",
        "assessment_digest",
        "episodes",
    }
    assert expected_fields <= projection.keys()


def test_recommendation_never_changes_qualification_or_authority():
    result = assess(ep("a"), ep("b"), ep("c"))
    assert result.recommendation is QualificationRecommendation.PROMOTION_RECOMMENDED
    assert result.current_qualification_state == "UNQUALIFIED"
    assert result.authority_granted is False
    assert result.reviewer_authorization_required is True
