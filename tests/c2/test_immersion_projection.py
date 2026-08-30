from sage.c2.immersion_projection import project_impact_stars, project_milestone_strike


def test_passed_twenty_cells_projects_five_stars():
    impact = project_impact_stars(verified_cells=20, total_cells=20, verdict="PASS")
    assert impact.stars == 5
    assert impact.rank == "MASTER"


def test_partial_pass_projects_proportional_impact():
    impact = project_impact_stars(verified_cells=19, total_cells=20, verdict="PASS")
    assert impact.stars == 5
    assert impact.rank == "MASTER"


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
    assert strike.impact.stars == 5
