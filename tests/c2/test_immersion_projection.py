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


def test_pick_action_visual_projection():
    from sage.c2.immersion_projection import project_pick_action_visual

    projection = project_pick_action_visual(
        selection="Shohei Ohtani - Over 1.5 Total Bases",
        market="Player Props",
        decimal_price=1.85,
        expected_value=0.085,
        edge_score=0.062,
        kelly_stake=0.028,
        recommendation="GENUINE_PLUS_EV",
        outcome_status="UNRESOLVED",
    )

    rendered = projection.render()
    assert "📈 PICK [Shohei Ohtani - Over 1.5 Total Bases | Player Props]" in rendered
    assert "@ 1.85" in rendered
    assert "EV 📈 +8.50%" in rendered
    assert "EDGE ⚡ +6.20%" in rendered
    assert "KELLY 💰 2.80%" in rendered
    assert "STATUS 🎲 UNRESOLVED" in rendered


def test_strike_event_and_feed_projection():
    from sage.c2.immersion_projection import StrikeEvent, StrikeFeedProjection

    e1 = StrikeEvent("TARGET ACQUIRED", "🎯", "Interface Progression", "Seam: Strike feed")
    e2 = StrikeEvent("MARINE STRIKE", "⚡", "Flight F1", "Phase: EXECUTE")
    feed = StrikeFeedProjection(events=(e1, e2))

    rendered = feed.render()
    assert "HIGH-TEMPO STRIKE FEED" in rendered
    assert "🎯 TARGET ACQUIRED // Interface Progression" in rendered
    assert "Seam: Strike feed" in rendered
    assert "⚡ MARINE STRIKE // Flight F1" in rendered


def test_project_strike_feed_from_state():
    from sage.c2.immersion_projection import project_strike_feed_from_state
    from sage.c2.immersion_state import ImmersionState, ExecutionPhase, TrustStatus, FlightStatus

    state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Game Immersion Substrate",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="INTERFACE-CONVERGENCE",
        gate="Read-only projection",
        next_move="Verify with pytest",
        evidence_refs=("ref_a1", "ref_a2"),
    )

    feed = project_strike_feed_from_state(state)
    rendered = feed.render()
    assert "🎯 TARGET ACQUIRED // INTERFACE-CONVERGENCE" in rendered
    assert "⚡ MARINE STRIKE // Flight F1" in rendered
    assert "🛡️ EVIDENCE CAPTURED // 2 Verified Ref(s)" in rendered
    assert "✓ HIT CONFIRMED // Game Immersion Substrate" in rendered
    assert "◆ TARGET KILLED // Frontier Seam Cleared" in rendered
    assert "→ NEXT TARGET // Verify with pytest" in rendered
