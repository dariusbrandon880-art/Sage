"""Governed career XP conversion primitives for SAGE.

Queue #03 deliberately keeps the conversion deterministic. Casino-style
variable reinforcement is useful for optional presentation/reward loops, but
career XP must remain auditable and attributable to verified work. Randomness
must never change the amount of career XP earned for the same verified Point
value.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


POINT_TO_XP = Decimal("10")


@dataclass(frozen=True)
class XPEvent:
    """Auditable conversion of one verified Point award into career XP."""

    event_id: str
    agent_id: str
    verified_points: int
    xp_awarded: int


def points_to_xp(verified_points: int) -> int:
    """Convert verified Points to career XP using the locked 10:1 ratio."""
    if isinstance(verified_points, bool) or not isinstance(verified_points, int):
        raise TypeError("verified_points must be an integer")
    if verified_points < 0:
        raise ValueError("verified_points cannot be negative")
    return int(
        (Decimal(verified_points) * POINT_TO_XP).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def build_xp_event(event_id: str, agent_id: str, verified_points: int) -> XPEvent:
    """Create a deterministic XP event from a verified Point award."""
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


def accumulate_xp(events: list[XPEvent]) -> int:
    """Return lifetime XP from the supplied verified XP events."""
    return sum(event.xp_awarded for event in events)
