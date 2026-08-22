"""Adversarial tests for the causal effect observation boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sage.core.effect_observation import (
    EffectObservation,
    EffectObservationValidationError,
    TransitionOutcome,
)


BASE = {
    "execution_id": "execution-1",
    "target_boundary_id": "capability-state:agent-1:flight",
    "expected_state_hash": "expected-hash",
    "observed_at": "2026-08-22T03:30:00+00:00",
    "telemetry_source": "independent-probe-1",
}


def make_observation(
    *,
    outcome: TransitionOutcome = TransitionOutcome.CONFIRMED,
    observed_state_hash: str | None = "expected-hash",
    observed_at: str = BASE["observed_at"],
) -> EffectObservation:
    payload = {
        **BASE,
        "observed_at": observed_at,
        "observed_state_hash": observed_state_hash,
        "outcome": outcome,
    }
    return EffectObservation(**payload)


def test_confirmed_requires_observed_state_to_match_expected() -> None:
    observation = make_observation()

    assert observation.outcome is TransitionOutcome.CONFIRMED
    assert observation.observed_state_hash == observation.expected_state_hash
    assert observation.authority_granted is False


def test_confirmed_mismatch_cannot_claim_success() -> None:
    with pytest.raises(EffectObservationValidationError):
        make_observation(observed_state_hash="different-hash")


def test_unknown_is_first_class_and_has_no_observed_state_claim() -> None:
    observation = make_observation(
        outcome=TransitionOutcome.UNKNOWN,
        observed_state_hash=None,
    )

    assert observation.outcome is TransitionOutcome.UNKNOWN
    assert observation.observed_state_hash is None
    assert observation.authority_granted is False


def test_unknown_cannot_be_coerced_into_an_observed_hash() -> None:
    with pytest.raises(EffectObservationValidationError):
        make_observation(
            outcome=TransitionOutcome.UNKNOWN,
            observed_state_hash="unexpected-hash",
        )


def test_non_unknown_requires_actual_observed_state_hash() -> None:
    for outcome in (TransitionOutcome.REJECTED, TransitionOutcome.FAILED):
        with pytest.raises(EffectObservationValidationError):
            make_observation(outcome=outcome, observed_state_hash=None)


def test_utc_timestamp_is_required() -> None:
    with pytest.raises(EffectObservationValidationError):
        make_observation(observed_at="2026-08-22T03:30:00")


def test_non_utc_timestamp_is_rejected() -> None:
    with pytest.raises(EffectObservationValidationError):
        make_observation(observed_at="2026-08-21T23:30:00-04:00")


def test_observation_digest_is_deterministic() -> None:
    first = make_observation()
    second = make_observation()

    assert first.observation_id == second.observation_id
    assert len(first.observation_id) == 64


def test_observation_digest_changes_when_effect_changes() -> None:
    confirmed = make_observation()
    failed = make_observation(
        outcome=TransitionOutcome.FAILED,
        observed_state_hash="previous-hash",
    )

    assert confirmed.observation_id != failed.observation_id


def test_observation_is_immutable() -> None:
    observation = make_observation()

    with pytest.raises(FrozenInstanceError):
        observation.outcome = TransitionOutcome.FAILED


def test_public_projection_is_read_only_and_non_authoritative() -> None:
    projection = make_observation(
        outcome=TransitionOutcome.UNKNOWN,
        observed_state_hash=None,
    ).to_dict()

    assert projection["outcome"] == "UNKNOWN"
    assert projection["observed_state_hash"] is None
    assert projection["authority_granted"] is False
    assert "retry" not in projection
    assert "mutation" not in projection
