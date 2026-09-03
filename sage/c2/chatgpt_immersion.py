"""ChatGPT-facing C2 immersion response adapter.

This module composes already-canonical SAGE projections into the response
surface used by a text-capable ChatGPT integration. It does not create,
mutate, authorize, or infer canonical state.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT PRESENTATION
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any

from sage.c2.immersion_projection import (
    C2ResponseContract,
    MilestoneStrike,
    StrikeFeedProjection,
    project_c2_response_contract,
)
from sage.c2.immersion_state import ImmersionState
from sage.c2.response_envelope import c2_chatgpt_presentation, render_station_response


def _render_organism_projection(proj: Any) -> str | None:
    if proj is None:
        return None
    try:
        if hasattr(proj, "render_agent_tag") and callable(getattr(proj, "render_agent_tag")):
            try:
                return str(proj.render_agent_tag())
            except TypeError:
                return str(proj.render_agent_tag(proj))
        proj_mod = sys.modules.get("sage.experimental.airspace.organism_projection")
        if proj_mod is None:
            import importlib
            proj_mod = importlib.import_module("sage.experimental.airspace.organism_projection")
        return str(proj_mod.OrganismProjection.render_agent_tag(proj))
    except Exception:
        return None


@dataclass(frozen=True)
class ChatGPTImmersionResponse:
    """Read-only response projection for the ChatGPT C2 station."""

    station_header: str
    immersion_envelope: C2ResponseContract
    body: str
    milestone: MilestoneStrike | None = None
    strike_feed: StrikeFeedProjection | None = None
    organism_projection: Any | None = None
    organism_tag: str | None = None

    def render(self) -> str:
        """Render the complete response without creating canonical state."""
        body = self.immersion_envelope.render_full_envelope(self.body)
        tag = self.organism_tag
        if not tag and self.organism_projection is not None:
            tag = _render_organism_projection(self.organism_projection)

        header = f"{self.station_header}\n{tag}" if tag else self.station_header
        return render_station_response(
            f"{header}\n\n{body}",
            c2_chatgpt_presentation(),
        )


def project_chatgpt_immersion_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
    strike_feed: StrikeFeedProjection | None = None,
    organism_projection: Any | None = None,
    organism_tag: str | None = None,
    manager: Any | None = None,
    station_id: Any | None = None,
) -> ChatGPTImmersionResponse:
    """Project a canonical state into the ChatGPT C2 response surface."""
    contract = project_c2_response_contract(state, strike_feed=strike_feed)

    tag = organism_tag
    if not tag and organism_projection is not None:
        tag = _render_organism_projection(organism_projection)
    elif not tag and manager is not None:
        try:
            airspace_state = manager.reconstruct_airspace_state()
            proj_mod = sys.modules.get("sage.experimental.airspace.organism_projection")
            models_mod = sys.modules.get("sage.experimental.airspace.models")
            if proj_mod is None:
                import importlib
                proj_mod = importlib.import_module("sage.experimental.airspace.organism_projection")
            if models_mod is None:
                import importlib
                models_mod = importlib.import_module("sage.experimental.airspace.models")

            st_id = station_id or models_mod.StationID.MISSION_CONTROL
            proj = proj_mod.OrganismProjection.project_station(
                manager, airspace_state, st_id
            )
            tag = _render_organism_projection(proj)
            if organism_projection is None:
                organism_projection = proj
        except Exception:
            pass

    return ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed or contract.hud.strike_feed,
        organism_projection=organism_projection,
        organism_tag=tag,
    )
