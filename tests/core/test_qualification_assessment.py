"""Adversarial tests for QualificationAssessment v0.1."""

import pytest
from dataclasses import FrozenInstanceError

from sage.core.qualification_assessment import (
    CapabilityEvidenceEpisode,
    EpisodeVerdict,
    FailureAttribution,
    QualificationAssessment,
    QualificationAssessmentValidationError,
    QualificationRecommendation,
)


def ep(d, verdict=EpisodeVerdict.VERIFIED_SUPPORT, attribution=FailureAttribution.NONE, weight=1.0, independent=True):
    return CapabilityEvidenceEpisode(d, "capability.alpha", verdict, attribution, weight, independent)


def assess(*episodes):
    return QualificationAssessment.assess(capability_id="capability.alpha", episodes=episodes)


def test_three_independent_supports_recommend_without_promotion():
    r = assess(ep("a"), ep("b"), ep("c"))
    assert r.recommendation is QualificationRecommendation.PROMOTION_RECOMMENDED
    assert r.confidence_score == 1.0
    assert r.reviewer_authorization_required is True
    assert r.authority_granted is False
    assert r.current_qualification_state == "UNQUALIFIED"


def test_single_success_does_not_qualify():
    assert assess(ep("a")).recommendation is QualificationRecommendation.HOLD


def test_two_successes_do_not_meet_minimum_episode_count():
    assert assess(ep("a"), ep("b")).recommendation is QualificationRecommendation.HOLD


def test_environment_noise_is_not_agent_fault():
    r = assess(ep("a"), ep("b"), ep("c", EpisodeVerdict.VERIFIED_CONTRADICTION, FailureAttribution.ENVIRONMENT_NOISE))
    assert r.agent_fault_rate == 0.0
    assert r.recommendation is QualificationRecommendation.HOLD


def test_contradiction_blocks_promotion():
    r = assess(ep("a"), ep("b"), ep("c"), ep("d", EpisodeVerdict.VERIFIED_CONTRADICTION, FailureAttribution.AGENT_FAULT))
    assert r.confidence_score == 0.75
    assert r.recommendation is QualificationRecommendation.HOLD


def test_indeterminate_and_unresolved_are_not_positive_evidence():
    r = assess(ep("a"), ep("b", EpisodeVerdict.UNRESOLVED, FailureAttribution.UNKNOWN), ep("c", EpisodeVerdict.INDETERMINATE, FailureAttribution.UNKNOWN))
    assert r.confidence_score == 1.0
    assert r.recommendation is QualificationRecommendation.HOLD


def test_non_independent_episode_does_not_satisfy_minimum():
    r = assess(ep("a"), ep("b", independent=False), ep("c", independent=False))
    assert len(r.independent_episodes) == 1
    assert r.recommendation is QualificationRecommendation.HOLD


def test_weight_changes_digest_deterministically():
    a = assess(ep("a", weight=1.0), ep("b"), ep("c"))
    b = assess(ep("a", weight=0.5), ep("b"), ep("c"))
    assert a.assessment_digest != b.assessment_digest
    assert a.confidence_score == b.confidence_score == 1.0


def test_replay_is_deterministic():
    items = (ep("a", weight=0.8), ep("b", weight=0.9), ep("c"))
    assert assess(*items).assessment_digest == assess(*items).assessment_digest


def test_mutation_is_blocked():
    r = assess(ep("a"), ep("b"), ep("c"))
    with pytest.raises(FrozenInstanceError):
        r.capability_id = "other"  # type: ignore[misc]


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
    p = assess(ep("a"), ep("b"), ep("c")).to_dict()
    assert {"capability_id", "confidence_score", "recommendation", "current_qualification_state", "reviewer_authorization_required", "authority_granted", "agent_fault_rate", "assessment_digest", "episodes"} <= p.keys()


def test_recommendation_never_changes_qualification_or_authority():
    r = assess(ep("a"), ep("b"), ep("c"))
    assert r.recommendation is QualificationRecommendation.PROMOTION_RECOMMENDED
    assert r.current_qualification_state == "UNQUALIFIED"
    assert r.authority_granted is False
    assert r.reviewer_authorization_required is True
