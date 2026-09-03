"""Canonical presentation envelope for SAGE station responses.

The envelope is a read-only projection of already-governed provenance. It does
not grant authority, mutate canonical state, or attempt to control a host UI.
Host adapters may render the identity fields visually; plain-text clients use
the canonical nameplate prefix.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class StationPresentation:
    """Immutable presentation contract for one SAGE station response."""

    station: str
    display_name: str
    role: str
    provenance: str = "canonical_sage_station"
    read_only: bool = True

    @property
    def nameplate(self) -> str:
        return f"[SAGE::{self.station}]"

    def as_dict(self) -> dict[str, Any]:
        return {
            "station": self.station,
            "display_name": self.display_name,
            "role": self.role,
            "nameplate": self.nameplate,
            "provenance": self.provenance,
            "read_only": self.read_only,
        }


def c2_chatgpt_presentation() -> StationPresentation:
    return StationPresentation(
        station="C2::CHATGPT",
        display_name="C2 Mission Control",
        role="C2 control, synthesis, reconciliation, and governed execution",
    )


def gemini_presentation() -> StationPresentation:
    return StationPresentation(
        station="INTEL::GEMINI",
        display_name="Intelligence Station",
        role="external intelligence, reconnaissance, and falsification challenge",
    )


def jules_presentation() -> StationPresentation:
    return StationPresentation(
        station="ENGINEER::JULES",
        display_name="Engineering Execution Station",
        role="engineering execution and substrate verification",
    )


def render_station_response(text: str, presentation: StationPresentation) -> str:
    """Return a canonical station-tagged response without duplicate nameplates."""
    body = str(text).strip()
    prefix = presentation.nameplate
    if body.startswith(prefix):
        return body
    return f"{prefix} {presentation.display_name}\n\n{body}"


def build_response_envelope(text: str, presentation: StationPresentation) -> dict[str, Any]:
    """Build structured metadata plus the canonical rendered response."""
    return {
        "presentation": presentation.as_dict(),
        "response_text": render_station_response(text, presentation),
    }


def hud_update_key(hud: object) -> str:
    """Return a deterministic key for the exact visible HUD projection."""
    rendered = getattr(hud, "render", None)
    if not callable(rendered):
        raise ValueError("HUD continuity requires a renderable HUD projection")
    text = str(rendered())
    if not text.strip():
        raise ValueError("HUD continuity requires non-empty HUD output")
    return sha256(text.encode("utf-8")).hexdigest()


def should_render_hud(
    current_key: str,
    *,
    previous_key: str | None = None,
    force: bool = False,
) -> bool:
    """Decide whether a HUD needs to be surfaced without silently dropping updates.

    A first HUD, a changed HUD, or an explicitly forced HUD must render. An
    unchanged HUD may be suppressed by a host to avoid visual noise. The key
    is content-derived, so suppression cannot hide a changed HUD accidentally.
    """
    if not current_key or not current_key.strip():
        raise ValueError("HUD continuity requires a non-empty current key")
    return force or previous_key is None or current_key != previous_key
