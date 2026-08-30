from sage.c2.chatgpt_c2_contract import classify_directive, render_system_contract
from sage.c2.immersion_projection import project_impact_stars, project_milestone_strike
from sage.c2.response_envelope import c2_chatgpt_presentation, gemini_presentation, jules_presentation, render_station_response


def test_station_nameplates_are_canonical_and_distinct():
    assert c2_chatgpt_presentation().nameplate == "[SAGE::C2::CHATGPT]"
    assert jules_presentation().nameplate == "[SAGE::ENGINEER::JULES]"
    assert gemini_presentation().nameplate == "[SAGE::INTEL::GEMINI]"


def test_station_response_renderer_does_not_duplicate_nameplate():
    presentation = c2_chatgpt_presentation()
    rendered = render_station_response("C2 online", presentation)
    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert render_station_response(rendered, presentation) == rendered


def test_repo_truth_lock_still_requires_rehydration():
    decision = classify_directive("lock onto repo and whole repo truth")
    assert decision.requires_rehydration is True
    assert decision.matched_rehydration_triggers


def test_immersion_contract_is_present_in_rendered_c2_contract():
    rendered = render_system_contract()
    assert "REHYDRATION TRIGGERS" in rendered
    assert "PRESERVE EXACTLY" in rendered


def test_failed_or_unknown_progress_never_earns_stars():
    projection = project_impact_stars(verified_cells=20, total_cells=20, verdict="HOLD")
    assert projection.stars == 0
    assert projection.rank == "UNRANKED"


def test_verified_progress_projects_five_star_frontier_impact():
    projection = project_impact_stars(verified_cells=20, total_cells=20, verdict="PASS")
    assert projection.stars == 5
    assert projection.rank == "MASTER"


def test_milestone_strike_projects_only_reconciled_wave_state():
    strike = project_milestone_strike(
        wave_id="wave-test",
        reconvergence={"verdict": "PASS", "verified_cells": 20},
    )
    assert strike.verdict == "PASS"
    assert strike.impact.stars == 5
    assert strike.impact.verified_cells == 20
