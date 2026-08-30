from sage.experimental.airspace.immersion import (
    render_capability_stack,
    render_capability_tags,
    render_immersion_nameplate,
    render_live_sortie_strip,
    render_sortie_glyph,
)
from sage.experimental.airspace.models import AirspaceState, Sortie, SortieState, StationID


def test_capability_stack_is_derived_from_canonical_levels():
    state = AirspaceState()
    rendered = render_capability_stack(state, StationID.MISSION_CONTROL)

    assert rendered == "CQL ⚙️⚙️⚙️⚙️  SQL 🛰️🛰️🛰️"


def test_capability_tags_are_persistent_read_only_projection():
    state = AirspaceState()
    before = state.model_dump()

    tags = render_capability_tags(state, StationID.MISSION_CONTROL)

    assert tags == ("CQL-4 OPERATIONAL", "SQL-3")
    assert state.model_dump() == before


def test_sortie_glyphs_follow_canonical_state():
    assert render_sortie_glyph(SortieState.ACTIVE) == "✈️"
    assert render_sortie_glyph(SortieState.EVIDENCE_CAPTURE) == "🛡️"
    assert render_sortie_glyph(SortieState.VERIFIED) == "⭐"
    assert render_sortie_glyph(SortieState.FAILED) == "⚠️"


def test_live_sortie_strip_reflects_real_active_sorties():
    state = AirspaceState()
    sortie = Sortie(
        sortie_id="sortie-immersion-test",
        mission_id="mission-immersion-test",
        station=StationID.ENGINEERING_FLIGHT,
        objective="test projection",
        target="immersion",
        status=SortieState.ACTIVE,
    )
    state.active_sorties.append(sortie)

    rendered = render_live_sortie_strip(state)

    assert "✈️ ENGINEERING_FLIGHT ACTIVE" in rendered


def test_immersion_nameplate_combines_identity_progression_and_live_state():
    state = AirspaceState()
    rendered = render_immersion_nameplate(state, StationID.MISSION_CONTROL)

    assert "[SAGE::C2::CHATGPT]" in rendered
    assert "CQL-4" in rendered
    assert "XP 0" in rendered
    assert "CQL ⚙️⚙️⚙️⚙️" in rendered
    assert "NO ACTIVE SORTIES" in rendered
