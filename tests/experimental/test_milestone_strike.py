from sage.experimental.airspace.nameplate import render_milestone_strike


def test_milestone_strike_renders_increasing_earned_stars():
    assert render_milestone_strike(1) == "MILESTONE STRIKE: ⭐"
    assert render_milestone_strike(3) == "MILESTONE STRIKE: ⭐⭐⭐"
    assert render_milestone_strike(5) == "MILESTONE STRIKE: ⭐⭐⭐⭐⭐"


def test_milestone_strike_zero_is_explicitly_unearned():
    assert render_milestone_strike(0) == "MILESTONE STRIKE: —"


def test_milestone_strike_rejects_invalid_levels():
    for value in (-1, 6):
        try:
            render_milestone_strike(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid star level was accepted")

    try:
        render_milestone_strike(True)
    except TypeError:
        pass
    else:
        raise AssertionError("boolean star level was accepted")


def test_milestone_strike_is_projection_only():
    rendered = render_milestone_strike(4)
    assert rendered == "MILESTONE STRIKE: ⭐⭐⭐⭐"
