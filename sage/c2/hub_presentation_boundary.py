"""Transport-independent recognition and contextual canonical Hub rendering.

Pasted Markdown, fenced blocks, Jules reports, and archived text are transport
representations only. This boundary recognizes their semantic Hub markers,
then delegates presentation to the manager-owned canonical Airspace projection.
It never constructs a replacement HUD and never treats transport formatting as state.

Hub A and Hub B remain distinct canonical surfaces. They may be composed when
context calls for the full organism/C2 view, but composition is not required
on every turn and never creates a third HUD.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HubSurface(str, Enum):
    HUB_A = "HUB_A"
    HUB_B = "HUB_B"
    COMPOSITE = "COMPOSITE"


_HUB_A_LAYERS = (
    "01 — COMMAND BAND",
    "02 — OPERATING PICTURE",
    "03 — PROGRESSION / IMPACT",
    "04 — STRIKE FEED",
)
_HUB_B_MARKERS = (
    "05 — ORGANISM PROGRESSION",
    "SAGE ORGANISM // AGENT PROJECTION",
)


@dataclass(frozen=True)
class CanonicalHubObject:
    """Semantic Hub identity extracted from an arbitrary transport representation."""

    surface: HubSurface
    has_hub_a: bool
    has_hub_b: bool
    transport_framing: str

    @property
    def is_hub(self) -> bool:
        return self.has_hub_a or self.has_hub_b


def _transport_framing(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        return "fenced"
    if "[SAGE::C2::CHATGPT]" in stripped and "Jules" in stripped:
        return "mixed-report"
    return "plain"


def recognize_hub(text: str) -> CanonicalHubObject | None:
    """Recognize Hub semantics without trusting transport formatting."""
    if not isinstance(text, str) or not text.strip():
        return None

    normalized = text.replace("\\u2014", "—")
    has_hub_a = all(layer in normalized for layer in _HUB_A_LAYERS)
    has_hub_b = any(marker in normalized for marker in _HUB_B_MARKERS)
    if not (has_hub_a or has_hub_b):
        return None

    if has_hub_a and has_hub_b:
        surface = HubSurface.COMPOSITE
    elif has_hub_a:
        surface = HubSurface.HUB_A
    else:
        surface = HubSurface.HUB_B

    return CanonicalHubObject(
        surface=surface,
        has_hub_a=has_hub_a,
        has_hub_b=has_hub_b,
        transport_framing=_transport_framing(text),
    )


def render_canonical_hub(
    manager: Any,
    *,
    surface: HubSurface = HubSurface.HUB_A,
    status: str = "READY",
) -> str:
    """Render the requested canonical Hub surface through the Airspace manager.

    The C2 boundary owns semantic surface selection; the experimental Airspace
    implementation owns the concrete projection. This preserves the one-way
    dependency boundary without hiding an experimental import behind importlib.
    """
    if manager is None:
        raise ValueError("Canonical Hub rendering requires an Airspace manager")

    renderer = getattr(manager, "render_canonical_hub", None)
    if not callable(renderer):
        raise TypeError("Airspace manager does not expose canonical Hub rendering")

    rendered = renderer(surface=surface, status=status)
    if not isinstance(rendered, str) or not rendered.strip():
        raise ValueError("Canonical Hub renderer returned empty presentation")
    return rendered


def normalize_hub_presentation(
    text: str,
    manager: Any,
    *,
    surface: HubSurface | None = None,
    status: str = "READY",
) -> str | None:
    """Convert Hub transport input into contextual canonical presentation.

    If no explicit surface is supplied, the recognized transport surface is
    preserved. A composite input remains composite; a Hub A or Hub B input is
    not expanded merely because both surfaces exist in the system.
    """
    recognized = recognize_hub(text)
    if recognized is None:
        return None
    selected_surface = surface or recognized.surface
    return render_canonical_hub(manager, surface=selected_surface, status=status)


__all__ = [
    "CanonicalHubObject",
    "HubSurface",
    "recognize_hub",
    "render_canonical_hub",
    "normalize_hub_presentation",
]
