"""Transport-independent recognition and canonical rendering for SAGE Hubs.

Pasted Markdown, fenced blocks, Jules reports, and archived text are transport
representations only. This boundary recognizes their semantic Hub markers,
then delegates presentation to the canonical Airspace renderer. It never
constructs a replacement HUD and never treats transport formatting as state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
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
_HUB_B_LAYER = "05 — ORGANISM PROGRESSION"


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
    """Recognize Hub semantics without treating Markdown/code framing as meaning.

    Hub A requires all four canonical layer headers. Hub B requires its canonical
    organism header. A composite contains both. Arbitrary prose containing only
    one layer is not promoted to Hub state.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    normalized = text.replace("\\u2014", "—")
    has_hub_a = all(layer in normalized for layer in _HUB_A_LAYERS)
    has_hub_b = _HUB_B_LAYER in normalized
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


def render_canonical_hub(manager: Any, *, status: str = "READY") -> str:
    """Render a recognized Hub through the canonical Airspace presentation path."""
    if manager is None:
        raise ValueError("Canonical Hub rendering requires an Airspace manager")

    import importlib
    immersion = importlib.import_module("sage.experimental.airspace.immersion")
    rendered = immersion.render_four_layer_hud_from_manager(manager, status=status)
    if not rendered or not rendered.strip():
        raise ValueError("Canonical Hub renderer returned empty presentation")
    return rendered


def normalize_hub_presentation(text: str, manager: Any, *, status: str = "READY") -> str | None:
    """Convert Hub transport input into canonical presentation output.

    The input text is used only for semantic recognition. Its Markdown, code
    fences, indentation, and surrounding report prose never become output
    presentation authority.
    """
    recognized = recognize_hub(text)
    if recognized is None:
        return None
    return render_canonical_hub(manager, status=status)


__all__ = [
    "CanonicalHubObject",
    "HubSurface",
    "recognize_hub",
    "render_canonical_hub",
    "normalize_hub_presentation",
]
