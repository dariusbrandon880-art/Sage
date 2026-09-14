import pytest
from sage.c2.response_envelope import (
    c2_chatgpt_presentation,
    build_response_envelope,
    hud_update_key,
    render_station_response,
    validate_hud_presentation_structure,
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


def test_validate_hud_presentation_structure_accepts_valid_four_layer_hud():
    hud = (
        "01 — COMMAND BAND | CANONICAL\n"
        "02 — OPERATING PICTURE | ACTIVE\n"
        "03 — PROGRESSION / IMPACT | RANK Lvl 12\n"
        "04 — STRIKE FEED | VERIFIED\n"
    )
    assert validate_hud_presentation_structure(hud) is True


def test_validate_hud_presentation_structure_rejects_generic_tables_or_prose():
    substitute_table = "| C2 Layer | State |\n| --- | --- |\n| Command | Active |"
    assert validate_hud_presentation_structure(substitute_table) is False
    assert validate_hud_presentation_structure("Just some plain status text.") is False


def test_hud_update_key_rejects_invalid_hud_structure():
    class MalformedHUD:
        def render(self):
            return "Generic markdown table without 4-layer bands"

    with pytest.raises(ValueError, match="Failure Class P: HUD presentation structure violation"):
        hud_update_key(MalformedHUD())
