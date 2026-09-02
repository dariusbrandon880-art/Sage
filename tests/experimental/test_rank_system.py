"""Verification for Queue #02 shared SAGE rank architecture."""

import pytest

from sage.experimental.airspace.rank_system import (
    BossClass,
    BossDisplay,
    RANK_LADDER,
    RankBand,
    is_c2_rank_title,
    rank_for_level,
    validate_rank_progression,
)

EXPECTED_RANK_TITLES = (
    "Recruit",
    "Private First Class",
    "Lance Operator",
    "Corporal Operator",
    "Sergeant Operator",
    "Airman Operator",
    "Airman First Class",
    "Senior Airman",
    "Technical Operator",
    "Staff Operator",
    "Joint Operator",
    "Joint Sergeant",
    "Joint Technical Sergeant",
    "Joint Master Sergeant",
    "Joint Gunnery Specialist",
    "Operations Flight Lead",
    "Mission Flight Lead",
    "Senior Mission Lead",
    "Command Master Specialist",
    "Master Operations Specialist",
    "Squadron Operations Lead",
    "Group Operations Lead",
    "Wing Operations Lead",
    "Fleet Operations Lead",
    "Senior Fleet Specialist",
    "Frontier Specialist",
    "Frontier Master",
    "Elite Mission Specialist",
    "Elite Systems Specialist",
    "Master of Operations",
)


def test_rank_ladder_is_locked_to_agreed_names_and_order():
    assert len(RANK_LADDER) == 30
    assert tuple(rank.level for rank in RANK_LADDER) == tuple(range(1, 31))
    assert tuple(rank.title for rank in RANK_LADDER) == EXPECTED_RANK_TITLES
    assert len(set(EXPECTED_RANK_TITLES)) == 30


def test_rank_ladder_is_shared_and_uses_all_progression_bands():
    assert {rank.band for rank in RANK_LADDER} == set(RankBand)


def test_rank_ladder_blends_operational_vocabulary_without_making_c2_a_rank():
    titles = {rank.title for rank in RANK_LADDER}
    assert "Lance Operator" in titles
    assert "Sergeant Operator" in titles
    assert "Airman Operator" in titles
    assert "Operations Flight Lead" in titles
    assert all(not is_c2_rank_title(title) for title in titles)


def test_rank_does_not_prescribe_capability_qualification_or_evidence():
    assert all(not hasattr(rank, "capability") for rank in RANK_LADDER)
    assert all(not hasattr(rank, "qualification_requirement") for rank in RANK_LADDER)
    assert all(not hasattr(rank, "promotion_evidence") for rank in RANK_LADDER)


def test_boss_classes_are_only_big_and_major():
    assert set(BossClass) == {BossClass.BIG, BossClass.MAJOR}


def test_boss_display_uses_one_or_two_stars_and_stripe_tally():
    big = BossDisplay(BossClass.BIG, 4)
    major = BossDisplay(BossClass.MAJOR, 2)
    assert big.stars == "⭐"
    assert big.stripes == "⚔️" * 4
    assert major.stars == "⭐⭐"
    assert major.stripes == "⚔️" * 2


def test_boss_display_rejects_negative_tally():
    with pytest.raises(ValueError):
        BossDisplay(BossClass.BIG, -1)


def test_rank_lookup_rejects_unknown_levels():
    assert rank_for_level(1).title == "Recruit"
    assert rank_for_level(30).title == "Master of Operations"
    with pytest.raises(ValueError):
        rank_for_level(0)
    with pytest.raises(ValueError):
        rank_for_level(31)


def test_rank_promotion_is_sequential_and_not_xp_driven():
    validate_rank_progression(0, 1)
    validate_rank_progression(14, 15)
    with pytest.raises(ValueError, match="skipping"):
        validate_rank_progression(1, 3)
    with pytest.raises(ValueError, match="skipping"):
        validate_rank_progression(29, 31)


def test_negative_and_non_positive_targets_fail_closed():
    with pytest.raises(ValueError):
        validate_rank_progression(-1, 1)
    with pytest.raises(ValueError):
        validate_rank_progression(0, 0)
