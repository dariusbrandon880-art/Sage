"""Read-only immersion projections derived from verified C2 wave state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ImpactStars:
    """Evidence-bound visual progression; never an authority or source of truth."""

    verified_cells: int
    stars: int
    rank: str


@dataclass(frozen=True)
class MilestoneStrike:
    """A presentation event projected from an already verified wave result."""

    wave_id: str
    verdict: str
    impact: ImpactStars


def project_impact_stars(*, verified_cells: int, total_cells: int, verdict: str) -> ImpactStars:
    """Project SAFE-impact stars from verified milestone cells only.

    A failed/unknown wave always projects zero stars. Successful waves earn one
    star per completed five-cell tier, capped at five. This is presentation
    state only; it cannot promote or authorize capabilities.
    """
    if verified_cells < 0 or total_cells < 0 or verified_cells > total_cells:
        raise ValueError("verified_cells must be between zero and total_cells")
    if verdict != "PASS":
        return ImpactStars(verified_cells=verified_cells, stars=0, rank="UNRANKED")
    stars = min(5, verified_cells // 5)
    rank = ("UNRANKED", "QUALIFIED", "OPERATIONAL", "ADVANCED", "ELITE", "MASTER")[stars]
    return ImpactStars(verified_cells=verified_cells, stars=stars, rank=rank)


def project_milestone_strike(
    *, wave_id: str, reconvergence: Mapping[str, object], total_cells: int = 20
) -> MilestoneStrike:
    """Convert reconciled wave evidence into a safe visual milestone projection."""
    verdict = str(reconvergence.get("verdict", "HOLD"))
    verified = int(reconvergence.get("verified_cells", 0))
    return MilestoneStrike(
        wave_id=wave_id,
        verdict=verdict,
        impact=project_impact_stars(
            verified_cells=verified, total_cells=total_cells, verdict=verdict
        ),
    )
