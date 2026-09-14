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


@dataclass(frozen=True)
class FieldC2ProjectionEnvelope:
    """Read-only Field-C2 projection envelope derived from structured report ingestion."""

    session_id: str
    report_id: str
    canonical_git_sha: str
    hud_projection: dict[str, Any] | None = None
    hud_update_key: str | None = None
    session_lineage: tuple[str, ...] = ()
    read_only: bool = True
    authority: str = "field_c2_jules_report"

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "report_id": self.report_id,
            "canonical_git_sha": self.canonical_git_sha,
            "hud_projection": self.hud_projection,
            "hud_update_key": self.hud_update_key,
            "session_lineage": list(self.session_lineage),
            "read_only": self.read_only,
            "authority": self.authority,
        }


def build_response_envelope(
    text: str,
    presentation: StationPresentation,
    field_c2_envelope: FieldC2ProjectionEnvelope | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build structured metadata plus the canonical rendered response."""
    envelope = {
        "presentation": presentation.as_dict(),
        "response_text": render_station_response(text, presentation),
    }
    if field_c2_envelope is not None:
        if isinstance(field_c2_envelope, FieldC2ProjectionEnvelope):
            envelope["field_c2_envelope"] = field_c2_envelope.as_dict()
        else:
            envelope["field_c2_envelope"] = dict(field_c2_envelope)
    return envelope


REQUIRED_HUD_LAYERS = (
    "01 — COMMAND BAND",
    "02 — OPERATING PICTURE",
    "04 — STRIKE FEED",
)
LAYER_03_PREFIX = "03 — PROGRESSION / IMPACT"
ORGANISM_PROGRESSION_LAYER = "05 — ORGANISM PROGRESSION"


def validate_hud_presentation_structure(
    hud: object, *, organism_present: bool = False
) -> str:
    """Validate canonical HUD presentation structure fail-closed under Failure Class P.

    Requirements:
    - Must be a non-empty string or renderable object producing non-empty text.
    - Must contain required canonical layers in exact sequence:
      01 — COMMAND BAND
      02 — OPERATING PICTURE
      03 — PROGRESSION / IMPACT (when present in AirspaceRenderer HUD)
      04 — STRIKE FEED
      05 — ORGANISM PROGRESSION (when organism_present=True or layer 05 present)
    - Reordered, missing, renamed, or reformatted layer headers fail closed.
    - Omission of layer 05 when an organism projection is present fails closed.
    """
    if isinstance(hud, str):
        text = hud
    elif hasattr(hud, "render") and callable(getattr(hud, "render")):
        text = str(getattr(hud, "render")())
    else:
        raise ValueError(
            "HUD structural validation failed: HUD projection must be non-empty text or renderable HUD projection"
        )

    if not text or not text.strip():
        raise ValueError("HUD structural validation failed: HUD projection is empty")

    lines = text.splitlines()

    layer_indices: dict[str, int] = {}
    for idx, line in enumerate(lines):
        line_s = line.strip()

        matched_layer = None
        if line_s.startswith("01 — COMMAND BAND"):
            matched_layer = "01 — COMMAND BAND"
        elif line_s.startswith("02 — OPERATING PICTURE"):
            matched_layer = "02 — OPERATING PICTURE"
        elif line_s.startswith(LAYER_03_PREFIX):
            matched_layer = LAYER_03_PREFIX
        elif line_s.startswith("04 — STRIKE FEED") or line_s.startswith(
            "⚡ HIGH-TEMPO STRIKE FEED"
        ):
            matched_layer = "04 — STRIKE FEED"
        elif line_s.startswith(ORGANISM_PROGRESSION_LAYER):
            matched_layer = ORGANISM_PROGRESSION_LAYER

        if matched_layer is not None:
            if matched_layer in layer_indices:
                if matched_layer == "04 — STRIKE FEED":
                    continue
                raise ValueError(
                    f"HUD structural validation failed: duplicate layer header {matched_layer}"
                )
            layer_indices[matched_layer] = idx

    for req in REQUIRED_HUD_LAYERS:
        if req not in layer_indices:
            raise ValueError(
                f"HUD structural validation failed: missing required layer {req}"
            )

    if organism_present and ORGANISM_PROGRESSION_LAYER not in layer_indices:
        raise ValueError(
            f"HUD structural validation failed: missing required layer {ORGANISM_PROGRESSION_LAYER} when organism projection is present"
        )

    canonical_order = (
        "01 — COMMAND BAND",
        "02 — OPERATING PICTURE",
        LAYER_03_PREFIX,
        "04 — STRIKE FEED",
        ORGANISM_PROGRESSION_LAYER,
    )

    ordered_present = [layer for layer in canonical_order if layer in layer_indices]
    for i in range(len(ordered_present) - 1):
        curr_layer = ordered_present[i]
        next_layer = ordered_present[i + 1]
        if layer_indices[curr_layer] >= layer_indices[next_layer]:
            raise ValueError(
                f"HUD structural validation failed: reordered layers ({next_layer} appears before {curr_layer})"
            )

    return text


def hud_update_key(hud: object, *, organism_present: bool = False) -> str:
    """Return a deterministic key for the exact visible HUD projection."""
    text = validate_hud_presentation_structure(hud, organism_present=organism_present)
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
