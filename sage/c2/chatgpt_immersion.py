"""ChatGPT-facing C2 immersion response adapter.

This module composes already-canonical SAGE projections into the response
surface used by a text-capable ChatGPT integration. It does not create,
mutate, authorize, or infer canonical state.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT PRESENTATION

The ChatGPT surface renders the canonical organism tag from the persisted
Airspace ledger as its top-level immersion layer. The manager-backed projection
remains read-only; this adapter never creates a second progression source.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from sage.c2.immersion_projection import (
    C2ResponseContract,
    MilestoneStrike,
    StrikeFeedProjection,
    project_c2_response_contract,
)
from sage.c2.immersion_state import ImmersionState
from sage.c2.response_envelope import c2_chatgpt_presentation, render_station_response


def _load_airspace_manager() -> object:
    manager_mod = importlib.import_module("sage.experimental.airspace.manager")
    return manager_mod.AirspaceManager()


def _get_station_id(station_id_val: Any) -> Any:
    models_mod = importlib.import_module("sage.experimental.airspace.models")
    if station_id_val is None:
        return models_mod.StationID.MISSION_CONTROL
    if isinstance(station_id_val, models_mod.StationID):
        return station_id_val
    if isinstance(station_id_val, str):
        try:
            return models_mod.StationID(station_id_val)
        except ValueError:
            return models_mod.StationID.MISSION_CONTROL
    return station_id_val


def _render_organism_tag(manager: object, station_id: Any, state_label: str) -> str:
    nameplate_mod = importlib.import_module("sage.experimental.airspace.nameplate")
    return nameplate_mod.render_organism_nameplate(
        manager,
        station_id,
        compact=True,
        state_label=state_label,
    )


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
    station_id: Any = None,
    state_label: str = "READY",
) -> ChatGPTImmersionResponse:
    """Project canonical state into the ChatGPT C2 response surface.

    The organism manager defaults to canonical AirspaceManager so the top-level
    organism tag is always rendered as the canonical top-level immersion header.
    """
    contract = project_c2_response_contract(state, strike_feed=strike_feed)
    target_station = _get_station_id(station_id)
    mgr = organism_manager
    if mgr is None:
        try:
            mgr = _load_airspace_manager()
        except Exception:
            mgr = None

    organism_tag = None
    if mgr is not None:
        try:
            organism_tag = _render_organism_tag(mgr, target_station, state_label)
        except Exception:
            organism_tag = None

    return ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed or contract.hud.strike_feed,
        organism_tag=organism_tag,
    )
