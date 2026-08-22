from dataclasses import FrozenInstanceError

import pytest

from sage.core.qualification_assessment import (
    CapabilityEvidenceEpisode,
    EpisodeVerdict,
    FailureAttribution,
    QualificationAssessment,
)
from sage.core.transition_sufficiency import (
    SufficiencyVerdict,
    TransitionSufficiency,
    TransitionSufficiencyPolicy,
    TransitionSufficiencyValidationError,
)


def episode(
    digest: str,
    verdict: EpisodeVerdict = EpisodeVerdict.VERIFIED_SUPPORT,
    *,
    attribution: FailureAttribution = FailureAttribution.NONE,
    independent: bool = True,
) -> CapabilityEvidenceEpisode:
    return CapabilityEvidenceEpisode(
        projection_digest=digest,
        capability_id="capability.alpha",
        verdict=verdict,
        failure_attribution=attribution,
        independent=independent,
    )


def assessment(*episodes: CapabilityEvidenceEpisode) -> QualificationAssessment:
    return QualificationAssessment.assess(
        capability_id="capability.alpha", episodes=episodes
    )


def test_sufficient_requires_explicit_policy_and_never_grants_authority() -> None:
    result = TransitionSufficiency.evaluate(
        assessment=assessment(episode("a"), episode("b"), episode("c")),
        policy=TransitionSufficiencyPolicy(minimum_confidence_score=0.85),
    )

    assert result.verdict is SufficiencyVerdict.SUFFICIENT
    assert result.authority_granted is False
    assert result.reviewer_authorization_required is True
    assert result.failed_requirements == ()


def test_insufficient_when_sample_size_is_below_policy() -> None:
    result = TransitionSufficiency.evaluate(
        assessment(episode("a")),
        policy=TransitionSufficiencyPolicy(
            minimum_independent_episodes=3,
            minimum_supporting_episodes=2,
        ),
    )

    assert result.verdict is SufficiencyVerdict.INSUFFICIENT
    assert "minimum_independent_episodes" in result.failed_requirements
    assert "minimum_supporting_episodes" in result.failed_requirements


def test_contradiction_is_conflicted_not_sufficient() -> None:
    result = TransitionSufficiency.evaluate(
        assessment(
            episode("a"),
            episode("b"),
            episode(
                "c",
                EpisodeVerdict.VERIFIED_CONTRADICTION,
                attribution=FailureAttribution.AGENT_FAULT,
            ),
        )
    )

    assert result.verdict is SufficiencyVerdict.CONFLICTED
    assert "contradiction_free" in result.failed_requirements
    assert result.authority_granted is False


def test_unresolved_and_indeterminate_are_indeterminate() -> None:
    unresolved = TransitionSufficiency.evaluate(
        assessment(
            episode("a"),
            episode("b"),
            episode("c", EpisodeVerdict.UNRESOLVED),
        )
    )
    indeterminate = TransitionSufficiency.evaluate(
        assessment(
            episode("a"),
            episode("b"),
            episode("c", EpisodeVerdict.INDETERMINATE),
        )
    )

    assert unresolved.verdict is SufficiencyVerdict.INDETERMINATE
    assert indeterminate.verdict is SufficiencyVerdict.INDETERMINATE
    assert "unresolved_free" in unresolved.failed_requirements
    assert "unresolved_free" in indeterminate.failed_requirements


def test_environment_noise_does_not_count_as_agent_fault() -> None:
    result = TransitionSufficiency.evaluate(
        assessment(
            episode("a"),
            episode("b"),
            episode(
                "c",
                EpisodeVerdict.VERIFIED_CONTRADICTION,
                attribution=FailureAttribution.ENVIRONMENT_NOISE,
            ),
        )
    )

    assert result.verdict is SufficiencyVerdict.CONFLICTED
    assert "maximum_agent_fault_rate" not in result.failed_requirements


def test_confidence_threshold_is_policy_driven() -> None:
    result = TransitionSufficiency.evaluate(
        assessment(
            episode("a"),
            episode("b"),
            episode(
                "c",
                EpisodeVerdict.VERIFIED_CONTRADICTION,
                attribution=FailureAttribution.ENVIRONMENT_NOISE,
            ),
        ),
        policy=TransitionSufficiencyPolicy(minimum_confidence_score=1.0),
    )

    assert result.verdict is SufficiencyVerdict.CONFLICTED
    assert "minimum_confidence_score" in result.failed_requirements


def test_digest_is_deterministic_and_policy_sensitive() -> None:
    evidence = assessment(episode("a"), episode("b"), episode("c"))
    first = TransitionSufficiency.evaluate(assessment=evidence)
    second = TransitionSufficiency.evaluate(assessment=evidence)
    changed = TransitionSufficiency.evaluate(
        assessment=evidence,
        policy=TransitionSufficiencyPolicy(minimum_confidence_score=0.90),
    )

    assert first.sufficiency_digest == second.sufficiency_digest
    assert first.sufficiency_digest != changed.sufficiency_digest


def test_result_is_immutable() -> None:
    result = TransitionSufficiency.evaluate(
        assessment(episode("a"), episode("b"), episode("c"))
    )

    with pytest.raises(FrozenInstanceError):
        result.authority_granted = True


def test_invalid_policy_is_rejected() -> None:
    with pytest.raises(TransitionSufficiencyValidationError):
        TransitionSufficiencyPolicy(
            minimum_independent_episodes=1,
            minimum_supporting_episodes=2,
        )


def test_non_assessment_input_is_rejected() -> None:
    with pytest.raises(TransitionSufficiencyValidationError):
        TransitionSufficiency.evaluate(assessment="not-an-assessment")  # type: ignore[arg-type]
