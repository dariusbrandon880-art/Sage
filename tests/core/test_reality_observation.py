import pytest

from sage.core.reality_observation import (
    RealityObservation,
    RealityObservationValidationError,
)


def make_observation(**overrides):
    values = {
        "observation_id": "obs-001",
        "context_id": "ctx-001",
        "source_id": "world-source",
        "source_version": "2026-08-21",
        "observed_at": "2026-08-21T19:00:00Z",
        "observation_ref": "artifact://outcome-001",
        "observation_kind": "GROUND_TRUTH_OUTCOME",
        "observer_class": "EXTERNAL",
    }
    values.update(overrides)
    return RealityObservation(**values)


def test_deterministic_digest_replays_identically():
    first = make_observation()
    second = make_observation()

    assert first.observation_digest == second.observation_digest
    assert first.to_dict() == second.to_dict()


def test_metadata_order_does_not_change_digest():
    first = make_observation(observer_class="EXTERNAL")
    second = make_observation(observer_class="EXTERNAL")

    assert first.observation_digest == second.observation_digest


def test_observation_digest_binds_context():
    first = make_observation(context_id="ctx-a")
    second = make_observation(context_id="ctx-b")

    assert first.observation_digest != second.observation_digest


def test_observation_digest_binds_source_version_and_time():
    base = make_observation()
    version_changed = make_observation(source_version="2026-08-22")
    time_changed = make_observation(observed_at="2026-08-21T20:00:00Z")

    assert base.observation_digest != version_changed.observation_digest
    assert base.observation_digest != time_changed.observation_digest


@pytest.mark.parametrize(
    "field",
    [
        "observation_id",
        "context_id",
        "source_id",
        "source_version",
        "observed_at",
        "observation_ref",
        "observation_kind",
    ],
)
def test_required_fields_fail_closed(field):
    with pytest.raises(RealityObservationValidationError):
        make_observation(**{field: ""})


def test_invalid_observer_class_fails_closed():
    with pytest.raises(RealityObservationValidationError):
        make_observation(observer_class="CLAIMED_TRUTH")


def test_authority_is_permanently_false():
    observation = make_observation()

    assert observation.authority_granted is False
    with pytest.raises((AttributeError, TypeError)):
        observation.authority_granted = True


def test_observation_kind_changes_identity():
    first = make_observation(observation_kind="STATE_SNAPSHOT")
    second = make_observation(observation_kind="GROUND_TRUTH_OUTCOME")

    assert first.observation_digest != second.observation_digest


def test_public_projection_is_complete_and_deterministic():
    observation = make_observation()
    projection = observation.to_dict()

    assert projection["observation_digest"] == observation.observation_digest
    assert projection["authority_granted"] is False
    assert projection["observer_class"] == "EXTERNAL"
