"""Canonical SAGE career-rank taxonomy for the shared progression model.

Rank is an aggregate designation of demonstrated career evolution. It does not
grant, unlock, or prescribe capabilities and is not defined by XP alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class RankBand(str, Enum):
    FOUNDATION = "FOUNDATION"
    AIRSPACE = "AIRSPACE"
    JOINT = "JOINT"
    ADVANCED = "ADVANCED"
    STRATEGIC = "STRATEGIC"
    ELITE = "ELITE"


class BossClass(str, Enum):
    BIG = "BIG"
    MAJOR = "MAJOR"


@dataclass(frozen=True)
class RankDefinition:
    level: int
    title: str
    band: RankBand


@dataclass(frozen=True)
class BossDisplay:
    boss_class: BossClass
    boss_kill_count: int = 0
    boss_capture_count: int = 0

    def __post_init__(self) -> None:
        if self.boss_kill_count < 0 or self.boss_capture_count < 0:
            raise ValueError("Boss kill and capture counts must be non-negative.")

    @property
    def stars(self) -> str:
        return "⭐" if self.boss_class is BossClass.BIG else "⭐⭐"

    @property
    def kills(self) -> str:
        return "⚔️" * self.boss_kill_count

    @property
    def captures(self) -> str:
        return "┃" * self.boss_capture_count


RANK_LADDER: Final[tuple[RankDefinition, ...]] = (
    RankDefinition(1, "Recruit", RankBand.FOUNDATION),
    RankDefinition(2, "Private First Class", RankBand.FOUNDATION),
    RankDefinition(3, "Lance Operator", RankBand.FOUNDATION),
    RankDefinition(4, "Corporal Operator", RankBand.FOUNDATION),
    RankDefinition(5, "Sergeant Operator", RankBand.FOUNDATION),
    RankDefinition(6, "Airman Operator", RankBand.AIRSPACE),
    RankDefinition(7, "Airman First Class", RankBand.AIRSPACE),
    RankDefinition(8, "Senior Airman", RankBand.AIRSPACE),
    RankDefinition(9, "Technical Operator", RankBand.AIRSPACE),
    RankDefinition(10, "Staff Operator", RankBand.AIRSPACE),
    RankDefinition(11, "Joint Operator", RankBand.JOINT),
    RankDefinition(12, "Joint Sergeant", RankBand.JOINT),
    RankDefinition(13, "Joint Technical Sergeant", RankBand.JOINT),
    RankDefinition(14, "Joint Master Sergeant", RankBand.JOINT),
    RankDefinition(15, "Joint Gunnery Specialist", RankBand.JOINT),
    RankDefinition(16, "Operations Flight Lead", RankBand.ADVANCED),
    RankDefinition(17, "Mission Flight Lead", RankBand.ADVANCED),
    RankDefinition(18, "Senior Mission Lead", RankBand.ADVANCED),
    RankDefinition(19, "Command Master Specialist", RankBand.ADVANCED),
    RankDefinition(20, "Master Operations Specialist", RankBand.ADVANCED),
    RankDefinition(21, "Squadron Operations Lead", RankBand.STRATEGIC),
    RankDefinition(22, "Group Operations Lead", RankBand.STRATEGIC),
    RankDefinition(23, "Wing Operations Lead", RankBand.STRATEGIC),
    RankDefinition(24, "Fleet Operations Lead", RankBand.STRATEGIC),
    RankDefinition(25, "Senior Fleet Specialist", RankBand.STRATEGIC),
    RankDefinition(26, "Frontier Specialist", RankBand.ELITE),
    RankDefinition(27, "Frontier Master", RankBand.ELITE),
    RankDefinition(28, "Elite Mission Specialist", RankBand.ELITE),
    RankDefinition(29, "Elite Systems Specialist", RankBand.ELITE),
    RankDefinition(30, "Master of Operations", RankBand.ELITE),
)

RANK_BY_LEVEL: Final[dict[int, RankDefinition]] = {r.level: r for r in RANK_LADDER}


def rank_for_level(level: int) -> RankDefinition:
    try:
        return RANK_BY_LEVEL[level]
    except KeyError as exc:
        raise ValueError(f"Unknown SAGE rank level: {level}") from exc


def validate_rank_progression(current_level: int, target_level: int) -> None:
    if current_level < 0 or target_level < 1:
        raise ValueError("Rank levels must be non-negative and target level must be positive.")
    if target_level != current_level + 1:
        raise ValueError(f"Rank skipping rejected: cannot promote from {current_level} to {target_level}.")
    if target_level > len(RANK_LADDER):
        raise ValueError(f"Rank level {target_level} exceeds the locked ladder.")


def is_c2_rank_title(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized == "c2" or normalized.startswith("c2 ") or normalized.endswith(" c2")


def xp_threshold_for_level(level: int) -> int:
    """Return the minimum lifetime career XP required for rank level (1..30)."""
    if level < 1 or level > len(RANK_LADDER):
        raise ValueError(f"Rank level must be between 1 and {len(RANK_LADDER)}")
    if level == 1:
        return 0
    steps = level - 1
    return 100 * steps + 50 * steps * (steps - 1) // 2


def rank_level_for_xp(career_xp: int) -> int:
    """Return the integer rank level (1..30) earned for a given career XP total."""
    if isinstance(career_xp, bool) or not isinstance(career_xp, int) or career_xp < 0:
        raise ValueError("career_xp must be a non-negative integer.")

    achieved = 1
    for lvl in range(1, len(RANK_LADDER) + 1):
        if career_xp >= xp_threshold_for_level(lvl):
            achieved = lvl
        else:
            break
    return achieved


def rank_for_xp(career_xp: int) -> RankDefinition:
    """Return the RankDefinition earned for a given career XP total."""
    return rank_for_level(rank_level_for_xp(career_xp))


def xp_for_next_rank(career_xp: int) -> tuple[int, int]:
    """Return (current_rank_threshold, next_rank_threshold) for career_xp."""
    lvl = rank_level_for_xp(career_xp)
    current_thresh = xp_threshold_for_level(lvl)
    if lvl >= len(RANK_LADDER):
        return (current_thresh, current_thresh)
    next_thresh = xp_threshold_for_level(lvl + 1)
    return (current_thresh, next_thresh)
