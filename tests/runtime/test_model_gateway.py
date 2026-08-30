import pytest

from sage.runtime.model_gateway import (
    ModelResponse,
    SAGERuntime,
    SAGEStateSnapshot,
    SAGERuntimeEnvelope,
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


def test_envelope_binds_identity_state_policy_and_provenance():
    runtime = SAGERuntime(state())
    envelope = runtime.envelope("recon")
    assert envelope.station == "[SAGE::C2::CHATGPT]"
    assert envelope.agent_identity == envelope.station
    assert envelope.state_digest == envelope.state.digest()
    assert envelope.policy_version == "sage-runtime-v1"
    assert envelope.policy_digest == SAGERuntimeEnvelope._policy_digest(
        station=envelope.station,
        model_role="recon",
        policy_version=envelope.policy_version,
    )
    assert envelope.provenance_digest == SAGERuntimeEnvelope._provenance_digest(envelope.state)


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


def test_reconcile_rejects_station_identity_drift():
    runtime = SAGERuntime(state())
    with pytest.raises(ValueError, match="station identity"):
        runtime.reconcile(
            response(
                runtime,
                station="[SAGE::INTEL::GEMINI]",
                policy_version="sage-runtime-v1",
                policy_digest=SAGERuntimeEnvelope._policy_digest(
                    station="[SAGE::INTEL::GEMINI]",
                    model_role="recon",
                    policy_version="sage-runtime-v1",
                ),
                provenance_digest=SAGERuntimeEnvelope._provenance_digest(runtime.state),
            ),
            expected_station="[SAGE::C2::CHATGPT]",
            model_role="recon",
        )


def test_reconcile_rejects_policy_context_drift():
    runtime = SAGERuntime(state())
    with pytest.raises(ValueError, match="policy context"):
        runtime.reconcile(
            response(
                runtime,
                station="[SAGE::C2::CHATGPT]",
                policy_version="sage-runtime-v1",
                policy_digest="stale-policy-digest",
                provenance_digest=SAGERuntimeEnvelope._provenance_digest(runtime.state),
            ),
            expected_station="[SAGE::C2::CHATGPT]",
            model_role="recon",
        )


def test_reconcile_rejects_provenance_drift():
    runtime = SAGERuntime(state())
    with pytest.raises(ValueError, match="provenance"):
        runtime.reconcile(
            response(
                runtime,
                station="[SAGE::C2::CHATGPT]",
                policy_version="sage-runtime-v1",
                policy_digest=SAGERuntimeEnvelope._policy_digest(
                    station="[SAGE::C2::CHATGPT]",
                    model_role="recon",
                    policy_version="sage-runtime-v1",
                ),
                provenance_digest="stale-provenance-digest",
            ),
            expected_station="[SAGE::C2::CHATGPT]",
            model_role="recon",
        )


def test_state_digest_changes_when_canonical_state_changes():
    first = state()
    second = SAGEStateSnapshot(**{**first.__dict__, "active_frontier": "different-frontier"})
    assert first.digest() != second.digest()
