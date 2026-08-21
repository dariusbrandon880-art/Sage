from sage.agent_context_envelope import (
    ACKNOWLEDGED,
    ENVELOPE_VERSION,
    PENDING,
    acknowledge_envelope,
    build_agent_context_envelope,
)


def _envelope():
    return build_agent_context_envelope(
        sender="SAGE::INTEL::GEMINI",
        recipient="SAGE::C2::CHATGPT",
        event_id="evt-1",
        context_id="ctx-1",
        timestamp="2026-08-21T20:00:00+00:00",
        event_type="AGENT_CHALLENGE",
        payload={"challenge_ref": "PR-152"},
        sender_identity_projection={
            "nameplate": "[SAGE::INTEL::GEMINI]",
            "cql": 1,
            "sql": 3,
            "xp": 1450,
            "state": "RECON_POST_MERGE_SYNC",
        },
    )


def test_envelope_has_transport_neutral_contract():
    envelope = _envelope()

    assert envelope["envelope_version"] == ENVELOPE_VERSION
    assert envelope["sender"] == "SAGE::INTEL::GEMINI"
    assert envelope["recipient"] == "SAGE::C2::CHATGPT"
    assert envelope["context_id"] == "ctx-1"
    assert envelope["event_id"] == "evt-1"
    assert envelope["delivery_state"] == PENDING
    assert envelope["delivery_semantics"] == "pull_projection_only"
    assert envelope["read_only"] is True
    assert envelope["authority"] == "canonical_airspace_state_and_event_ledger"
    assert "sender_identity_projection" in envelope
    assert "<" not in str(envelope["sender_identity_projection"])


def test_acknowledgement_is_pure_and_does_not_mutate_input():
    envelope = _envelope()
    acknowledged = acknowledge_envelope(envelope)

    assert envelope["delivery_state"] == PENDING
    assert acknowledged["delivery_state"] == ACKNOWLEDGED
    assert acknowledged["event_id"] == envelope["event_id"]
    assert acknowledged["sender_identity_projection"] == envelope["sender_identity_projection"]


def test_invalid_delivery_state_is_rejected():
    try:
        build_agent_context_envelope(
            sender="A",
            recipient="B",
            event_id="evt",
            context_id=None,
            timestamp=None,
            event_type="AGENT_CHALLENGE",
            payload={},
            sender_identity_projection=None,
            delivery_state="DELIVERED",
        )
    except ValueError as exc:
        assert "unsupported delivery_state" in str(exc)
    else:
        raise AssertionError("invalid delivery state was accepted")
