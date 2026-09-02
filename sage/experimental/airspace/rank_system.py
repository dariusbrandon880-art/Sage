"""Canonical SAGE career-rank taxonomy for Queue #02.

Rank is a governed capability designation, not an XP threshold and not a command
authority. The ladder is shared by every SAGE agent; agent identity, career
specialization, CQL/SQL, Points, XP, and evidence remain separate concerns.

The vocabulary intentionally blends Marine-style execution/discipline with
Air Force/airspace-style precision, operations, intelligence, and strategic
responsibility. These are SAGE immersion titles, not real-world military ranks.
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


@dataclass(frozen=True)
class RankDefinition:
    """Immutable definition of one governed SAGE career rank."""

    level: int
    title: str
    band: RankBand
    capability: str
    qualification_requirement: str
    promotion_evidence: str


RANK_LADDER: Final[tuple[RankDefinition, ...]] = (
    RankDefinition(1, "Recruit", RankBand.FOUNDATION, "execute bounded tasks", "CQL-1", "conceptual evidence"),
    RankDefinition(2, "Private First Class", RankBand.FOUNDATION, "execute repeatable tasks", "CQL-2", "implementation evidence"),
    RankDefinition(3, "Lance Operator", RankBand.FOUNDATION, "operate a governed workflow", "CQL-2", "verified workflow evidence"),
    RankDefinition(4, "Corporal Operator", RankBand.FOUNDATION, "own a bounded sortie", "CQL-3", "verified sortie evidence"),
    RankDefinition(5, "Sergeant Operator", RankBand.FOUNDATION, "lead a bounded execution cell", "CQL-3", "verified leadership evidence"),
    RankDefinition(6, "Airman Operator", RankBand.AIRSPACE, "execute precise airspace work", "CQL-3", "precision execution evidence"),
    RankDefinition(7, "Airman First Class", RankBand.AIRSPACE, "sustain reliable operational execution", "CQL-4", "operational evidence"),
    RankDefinition(8, "Senior Airman", RankBand.AIRSPACE, "coordinate multi-step execution", "CQL-4", "coordination evidence"),
    RankDefinition(9, "Technical Operator", RankBand.AIRSPACE, "apply technical expertise", "CQL-4", "technical verification evidence"),
    RankDefinition(10, "Staff Operator", RankBand.AIRSPACE, "supervise governed operations", "CQL-4", "supervision evidence"),
    RankDefinition(11, "Joint Operator", RankBand.JOINT, "integrate cross-agent execution", "CQL-4", "joint mission evidence"),
    RankDefinition(12, "Joint Sergeant", RankBand.JOINT, "coordinate cross-domain sorties", "CQL-5", "joint coordination evidence"),
    RankDefinition(13, "Joint Technical Sergeant", RankBand.JOINT, "integrate technical and operational work", "CQL-5", "integration evidence"),
    RankDefinition(14, "Joint Master Sergeant", RankBand.JOINT, "mentor and stabilize complex execution", "CQL-5", "sustained capability evidence"),
    RankDefinition(15, "Joint Gunnery Specialist", RankBand.JOINT, "master precision under complexity", "CQL-5", "precision mastery evidence"),
    RankDefinition(16, "Operations Flight Lead", RankBand.ADVANCED, "lead continuous operations", "CQL-5", "continuous-operation evidence"),
    RankDefinition(17, "Mission Flight Lead", RankBand.ADVANCED, "lead multi-front missions", "CQL-6", "adaptive mission evidence"),
    RankDefinition(18, "Senior Mission Lead", RankBand.ADVANCED, "resolve cross-system dependencies", "CQL-6", "dependency-resolution evidence"),
    RankDefinition(19, "Command Master Specialist", RankBand.ADVANCED, "govern specialist execution", "CQL-6", "specialist-governance evidence"),
    RankDefinition(20, "Master Operations Specialist", RankBand.ADVANCED, "sustain adaptive operational capability", "CQL-6", "adaptive operations evidence"),
    RankDefinition(21, "Squadron Operations Lead", RankBand.STRATEGIC, "direct strategic mission sequencing", "CQL-6", "strategic sequencing evidence"),
    RankDefinition(22, "Group Operations Lead", RankBand.STRATEGIC, "coordinate multiple operational domains", "CQL-6", "multi-domain evidence"),
    RankDefinition(23, "Wing Operations Lead", RankBand.STRATEGIC, "shape system-wide operational posture", "CQL-7", "frontier posture evidence"),
    RankDefinition(24, "Fleet Operations Lead", RankBand.STRATEGIC, "coordinate sustained system capability", "CQL-7", "sustained system evidence"),
    RankDefinition(25, "Senior Fleet Specialist", RankBand.STRATEGIC, "master strategic specialization", "CQL-7", "strategic mastery evidence"),
    RankDefinition(26, "Frontier Specialist", RankBand.ELITE, "solve frontier capability problems", "CQL-7", "frontier breakthrough evidence"),
    RankDefinition(27, "Frontier Master", RankBand.ELITE, "reliably reproduce frontier capability", "CQL-7", "reproducible frontier evidence"),
    RankDefinition(28, "Elite Mission Specialist", RankBand.ELITE, "execute exceptional governed missions", "CQL-7", "elite mission evidence"),
    RankDefinition(29, "Elite Systems Specialist", RankBand.ELITE, "integrate frontier system capability", "CQL-7", "system integration evidence"),
    RankDefinition(30, "Master of Operations", RankBand.ELITE, "demonstrate sustained system-level mastery", "CQL-7", "system-level mastery evidence"),
)

RANK_BY_LEVEL: Final[dict[int, RankDefinition]] = {rank.level: rank for rank in RANK_LADDER}


def rank_for_level(level: int) -> RankDefinition:
    """Return a locked ladder entry; reject unknown or non-positive levels."""
    try:
        return RANK_BY_LEVEL[level]
    except KeyError as exc:
        raise ValueError(f"Unknown SAGE rank level: {level}") from exc


def validate_rank_progression(current_level: int, target_level: int) -> None:
    """Enforce sequential promotion; XP alone is intentionally irrelevant here."""
    if current_level < 0 or target_level < 1:
        raise ValueError("Rank levels must be non-negative and target level must be positive.")
    if target_level > len(RANK_LADDER):
        raise ValueError(f"Rank level {target_level} exceeds the locked ladder.")
    if target_level != current_level + 1:
        raise ValueError(
            f"Rank skipping rejected: cannot promote from {current_level} to {target_level}."
        )


def is_c2_rank_title(title: str) -> bool:
    """Guard the architectural rule that C2 is a function, never a rank."""
    normalized = title.strip().lower()
    return normalized == "c2" or normalized.startswith("c2 ") or normalized.endswith(" c2")
