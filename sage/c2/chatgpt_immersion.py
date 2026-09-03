"""ChatGPT-facing C2 immersion response adapter.

This module composes already-canonical SAGE projections into the response
surface used by a text-capable ChatGPT integration. It does not create,
mutate, authorize, or infer canonical state.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT PRESENTATION

When an organism manager is supplied, the ChatGPT surface additionally
renders the canonical organism tag from the persisted Airspace ledger. The
manager-backed projection remains read-only; this adapter never creates a
second progression source.
"""

from __future__ import annotations

from dataclasses import dataclass

from sage.c2.immersion_projection import (
    C2ResponseContract,
    MilestoneStrike,
    StrikeFeedProjection,
    project_c2_response_contract,
)
from sage.c2.immersion_state import ImmersionState
from sage.c2.response_envelope import c2_chatgpt_presentation, render_station_response
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.nameplate import render_organism_nameplate


@dataclass(frozen=True)
class ChatGPTImmersionResponse:
    """Read-only response projection for the ChatGPT C2 station."""

    station_header: str
    immersion_envelope: C2ResponseContract
    body: str
    milestone: MilestoneStrike | None = None
    strike_feed: StrikeFeedProjection | None = None
    organism_tag: str | None = None

    def render(self) -> str:
        """Render the complete response without creating canonical state."""
        body = self.immersion_envelope.render_full_envelope(self.body)
        header = self.station_header
        if self.organism_tag:
            header = f"{self.organism_tag}\n\n{header}"
        return render_station_response(
            f"{header}\n\n{body}",
            c2_chatgpt_presentation(),
        )


def project_chatgpt_immersion_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
    strike_feed: StrikeFeedProjection | None = None,
    *,
    organism_manager: object | None = None,
    station_id: StationID = StationID.MISSION_CONTROL,
    state_label: str = "READY",
) -> ChatGPTImmersionResponse:
    """Project canonical state into the ChatGPT C2 response surface.

    ``organism_manager`` is optional for backwards compatibility. When
    supplied, the exact canonical organism tag is rendered from the same
    persisted AirspaceManager ledger used by the organism projection.
    """
    contract = project_c2_response_contract(state, strike_feed=strike_feed)
    organism_tag = None
    if organism_manager is not None:
        organism_tag = render_organism_nameplate(
            organism_manager,
            station_id,
            compact=True,
            state_label=state_label,
        )
    return ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed or contract.hud.strike_feed,
        organism_tag=organism_tag,
    )
