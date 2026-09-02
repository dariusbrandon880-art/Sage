"""Verification for Queue #02 shared SAGE rank architecture."""

import pytest

from sage.experimental.airspace.rank_system import (
    RANK_LADDER,
    RankBand,
    is_c2_rank_title,
    rank_for_level,
    validate_rank_progression,
)


def test_rank_ladder_is_long_ordered_and_shared():
    assert len(RANK_LADDER) == 30
    assert [rank.level for rank in RANK_LADDER] == list(range(1, 31))
    assert len({rank.title for rank in RANK_LADDER}) == 30
    assert {rank.band for rank in RANK_LADDER} == set(RankBand)


def test_rank_ladder_blends_operational_vocabulary_without_making_c2_a_rank():
    titles = {rank.title for rank in RANK_LADDER}
    assert "Lance Operator" in titles
    assert "Sergeant Operator" in titles
    assert "Airman Operator" in titles
    assert "Operations Flight Lead" in titles
    assert all(not is_c2_rank_title(title) for title in titles)


def test_rank_requires_capability_and_qualification_metadata():
    assert all(rank.capability for rank in RANK_LADDER)
    assert all(rank.qualification_requirement.startswith("CQL-") for rank in RANK_LADDER)
    assert all(rank.promotion_evidence for rank in RANK_LADDER)


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
        validate_rank_progression(29, 30) if False else validate_rank_progression(29, 31)


def test_negative_and_non_positive_targets_fail_closed():
    with pytest.raises(ValueError):
        validate_rank_progression(-1, 1)
    with pytest.raises(ValueError):
        validate_rank_progression(0, 0)
