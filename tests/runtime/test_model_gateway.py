import pytest

from sage.runtime.model_gateway import (
    ModelResponse,
    SAGERuntime,
    SAGEStateSnapshot,
)


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="model-agnostic-runtime",
        stop_boundary="independent-verification",
        evidence_refs=("receipt-1",),
        known_state_refs=("known-1",),
        candidate_state_refs=("candidate-1",),
        negative_memory_refs=("negative-1",),
    )


def response(runtime: SAGERuntime, **overrides) -> ModelResponse:
    data = dict(
        model_id="test-model",
        instance_id=runtime.state.instance_id,
        mission_id=runtime.state.mission_id,
        session_id=runtime.state.session_id,
        input_state_digest=runtime.state.digest(),
    )
    data.update(overrides)
    return ModelResponse(**data)


def test_envelope_binds_identity_state_and_policy():
    runtime = SAGERuntime(state())
    envelope = runtime.envelope("recon")
    assert envelope.station == "[SAGE::C2::CHATGPT]"
    assert envelope.state.instance_id == "sage-instance"
    assert envelope.state_digest == envelope.state.digest()
    assert envelope.policy_version == "sage-runtime-v1"


def test_reconcile_accepts_matching_response():
    runtime = SAGERuntime(state())
    runtime.reconcile(response(runtime))


@pytest.mark.parametrize(
    "field,value",
    [
        ("instance_id", "other-instance"),
        ("mission_id", "other-mission"),
        ("session_id", "other-session"),
        ("input_state_digest", "bad-digest"),
    ],
)
def test_reconcile_rejects_cross_boundary_response(field, value):
    runtime = SAGERuntime(state())
    with pytest.raises(ValueError):
        runtime.reconcile(response(runtime, **{field: value}))


def test_state_digest_changes_when_canonical_state_changes():
    first = state()
    second = SAGEStateSnapshot(
        **{**first.__dict__, "active_frontier": "different-frontier"}
    )
    assert first.digest() != second.digest()
