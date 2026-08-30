from sage.c2.immersion_projection import project_impact_stars, project_milestone_strike


def test_passed_twenty_cells_projects_five_stars():
    impact = project_impact_stars(verified_cells=20, total_cells=20, verdict="PASS")
    assert impact.stars == 4
    assert impact.rank == "ADVANCED"


def test_partial_pass_cannot_claim_mastery():
    impact = project_impact_stars(verified_cells=19, total_cells=20, verdict="PASS")
    assert impact.stars == 3
    assert impact.rank == "OPERATIONAL"


def test_failed_wave_projects_no_impact():
    impact = project_impact_stars(verified_cells=20, total_cells=20, verdict="FAIL")
    assert impact.stars == 0
    assert impact.rank == "UNRANKED"


def test_invalid_cell_count_fails_closed():
    try:
        project_impact_stars(verified_cells=21, total_cells=20, verdict="PASS")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid evidence must fail closed")


def test_strike_is_projection_only():
    strike = project_milestone_strike(
        wave_id="wave-test",
        reconvergence={"verdict": "PASS", "verified_cells": 20},
    )
    assert strike.wave_id == "wave-test"
    assert strike.impact.stars == 4
