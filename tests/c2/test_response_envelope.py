from sage.c2.response_envelope import (
    FieldC2ProjectionEnvelope,
    c2_chatgpt_presentation,
    jules_presentation,
    build_response_envelope,
    render_station_response,
)


def test_c2_response_always_exposes_canonical_nameplate():
    presentation = c2_chatgpt_presentation()
    rendered = render_station_response("Mission status is verified.", presentation)
    assert rendered.startswith("[SAGE::C2::CHATGPT] C2 Mission Control")


def test_c2_response_does_not_duplicate_nameplate():
    presentation = c2_chatgpt_presentation()
    original = "[SAGE::C2::CHATGPT] C2 Mission Control\n\nAlready tagged."
    assert render_station_response(original, presentation) == original


def test_envelope_preserves_read_only_provenance():
    envelope = build_response_envelope("Evidence reconciled.", c2_chatgpt_presentation())
    assert envelope["presentation"]["nameplate"] == "[SAGE::C2::CHATGPT]"
    assert envelope["presentation"]["provenance"] == "canonical_sage_station"
    assert envelope["presentation"]["read_only"] is True
    assert "Evidence reconciled." in envelope["response_text"]


def test_field_c2_projection_envelope_attachment():
    proj = FieldC2ProjectionEnvelope(
        station="ENGINEER::JULES",
        session_id="session-jules-123",
        mission_hud={"mission": "Build Self-Improving Organism", "trust": "VERIFIED"},
        provenance_head="e8589d31629feb5ee6a5ea3f44f327f0b2c91885",
        progression_hud={"points": 500, "rank_level": 5},
        hud_update_key="key-12345",
    )
    envelope = build_response_envelope("Execution finished.", jules_presentation(), projection_envelope=proj)
    assert envelope["presentation"]["nameplate"] == "[SAGE::ENGINEER::JULES]"
    assert "projection_envelope" in envelope
    attached = envelope["projection_envelope"]
    assert attached["station"] == "ENGINEER::JULES"
    assert attached["session_id"] == "session-jules-123"
    assert attached["mission_hud"]["mission"] == "Build Self-Improving Organism"
    assert attached["progression_hud"]["points"] == 500
    assert attached["hud_update_key"] == "key-12345"
    assert attached["provenance_head"] == "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"
