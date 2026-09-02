"""Governed career XP conversion primitives for SAGE.

Queue #03 keeps the conversion deterministic. Casino-style variable
reinforcement may inform optional presentation, but career XP remains
auditable and attributable to verified work.

The conversion layer does not own career state. Canonical ``GameProgression``
remains the authoritative XP ledger; ``award_verified_points`` is the governed
adapter from verified Points into that existing ledger.
"""

from dataclasses import dataclass
from decimal import Decimal

from sage.experimental.airspace.models import GameProgression, StationID, XPCategory, XPEvent as CanonicalXPEvent


# 100 verified Points = 10 career XP.
POINT_TO_XP = Decimal("0.1")


@dataclass(frozen=True)
class XPEvent:
    """Auditable conversion receipt before writing to canonical progression."""

    event_id: str
    agent_id: str
    verified_points: int
    xp_awarded: Decimal


def points_to_xp(verified_points: int) -> Decimal:
    """Convert verified Points to career XP at 100 Points = 10 XP."""
    if isinstance(verified_points, bool) or not isinstance(verified_points, int):
        raise TypeError("verified_points must be an integer")
    if verified_points < 0:
        raise ValueError("verified_points cannot be negative")
    return Decimal(verified_points) * POINT_TO_XP


def build_xp_event(event_id: str, agent_id: str, verified_points: int) -> XPEvent:
    """Create a deterministic conversion receipt from verified Points."""
    if not event_id:
        raise ValueError("event_id is required")
    if not agent_id:
        raise ValueError("agent_id is required")
    return XPEvent(
        event_id=event_id,
        agent_id=agent_id,
        verified_points=verified_points,
        xp_awarded=points_to_xp(verified_points),
    )


def accumulate_xp(events: list[XPEvent]) -> Decimal:
    """Return the XP represented by verified conversion receipts."""
    return sum((event.xp_awarded for event in events), Decimal("0"))


def award_verified_points(
    progression: GameProgression,
    station_id: StationID,
    verified_points: int,
    category: XPCategory,
    reason: str,
    verified_event_ref: str,
) -> CanonicalXPEvent:
    """Convert verified Points and append the result to canonical GameProgression.

    Canonical progression currently stores integer XP amounts, so this adapter
    accepts only conversions that resolve to whole XP. Fractional conversions
    remain representable by the conversion receipt and must not be silently
    rounded.
    """
    amount = points_to_xp(verified_points)
    if amount != amount.to_integral_value():
        raise ValueError("Canonical XP ledger requires whole XP for this award")
    return progression.award_xp(
        station_id=station_id,
        category=category,
        amount=int(amount),
        reason=reason,
        verified_event_ref=verified_event_ref,
    )
