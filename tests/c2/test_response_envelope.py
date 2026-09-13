from sage.c2.response_envelope import (
    c2_chatgpt_presentation,
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


def test_envelope_attaches_field_c2_projection():
    from sage.c2.response_envelope import FieldC2ProjectionEnvelope

    field_env = FieldC2ProjectionEnvelope(
        session_id="session_001",
        report_id="report_001",
        canonical_git_sha="e8589d31629feb5ee6a5ea3f44f327f0b2c91885",
        hud_projection={"frontier": "field_c2"},
        hud_update_key="abc123key",
        session_lineage=("session_000", "session_001"),
    )
    envelope = build_response_envelope(
        "Field C2 ingested", c2_chatgpt_presentation(), field_c2_envelope=field_env
    )
    assert envelope["field_c2_envelope"]["session_id"] == "session_001"
    assert envelope["field_c2_envelope"]["hud_update_key"] == "abc123key"
    assert envelope["field_c2_envelope"]["authority"] == "field_c2_jules_report"
