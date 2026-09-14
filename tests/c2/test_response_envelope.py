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


import pytest
from sage.c2.response_envelope import (
    validate_hud_presentation_structure,
    hud_update_key,
)


from sage.c2.immersion_projection import project_mission_hud
from sage.c2.immersion_state import (
    ExecutionPhase,
    FlightStatus,
    ImmersionState,
    TrustStatus,
)


def test_validate_hud_presentation_structure_mission_hud_projection_pass():
    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Operating Picture",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="Immersion Seam",
        gate="HUD_VERIFICATION",
        next_move="verify real progression in HUD",
        evidence_refs=("ref-101",),
        provenance_head="0123456789012345678901234567890123456789",
    )
    hud = project_mission_hud(state)
    validated = validate_hud_presentation_structure(hud)
    assert "01 — COMMAND BAND" in validated
    assert "02 — OPERATING PICTURE" in validated
    assert "04 — STRIKE FEED" in validated


def test_validate_hud_presentation_structure_4_layer_and_5_layer_pass():
    valid_4_layer = (
        "01 — COMMAND BAND\n"
        "STATUS   : ACTIVE\n"
        "02 — OPERATING PICTURE\n"
        "MISSION  : RECON\n"
        "03 — PROGRESSION / IMPACT\n"
        "RANK     : Recruit\n"
        "04 — STRIKE FEED\n"
        "🎯 TARGET ACQUIRED"
    )
    validated = validate_hud_presentation_structure(valid_4_layer)
    assert validated == valid_4_layer

    valid_5_layer = (
        valid_4_layer + "\n"
        "05 — ORGANISM PROGRESSION\n"
        "ROSTER STATE"
    )
    validated_5 = validate_hud_presentation_structure(
        valid_5_layer, organism_present=True
    )
    assert validated_5 == valid_5_layer


def test_validate_hud_presentation_structure_missing_layer_fails():
    missing_2 = (
        "01 — COMMAND BAND\n"
        "03 — PROGRESSION / IMPACT\n"
        "04 — STRIKE FEED\n"
    )
    with pytest.raises(ValueError, match="missing required layer 02 — OPERATING PICTURE"):
        validate_hud_presentation_structure(missing_2)


def test_validate_hud_presentation_structure_reordered_layers_fails():
    reordered = (
        "02 — OPERATING PICTURE\n"
        "01 — COMMAND BAND\n"
        "03 — PROGRESSION / IMPACT\n"
        "04 — STRIKE FEED\n"
    )
    with pytest.raises(ValueError, match="reordered layers"):
        validate_hud_presentation_structure(reordered)


def test_validate_hud_presentation_structure_reformatted_header_fails():
    reformatted = (
        "01 - COMMAND BAND\n"
        "02 — OPERATING PICTURE\n"
        "03 — PROGRESSION / IMPACT\n"
        "04 — STRIKE FEED\n"
    )
    with pytest.raises(ValueError, match="missing required layer 01 — COMMAND BAND"):
        validate_hud_presentation_structure(reformatted)


def test_validate_hud_presentation_structure_missing_05_when_organism_present_fails():
    valid_4_layer = (
        "01 — COMMAND BAND\n"
        "02 — OPERATING PICTURE\n"
        "03 — PROGRESSION / IMPACT\n"
        "04 — STRIKE FEED\n"
    )
    with pytest.raises(
        ValueError, match="missing required layer 05 — ORGANISM PROGRESSION when organism projection is present"
    ):
        validate_hud_presentation_structure(valid_4_layer, organism_present=True)


def test_hud_update_key_rejects_malformed_hud():
    malformed = "INVALID HUD PROJECTION"
    with pytest.raises(ValueError, match="HUD structural validation failed"):
        hud_update_key(malformed)
