"""ChatGPT-facing C2 immersion response adapter.

This module composes already-canonical SAGE projections into the response
surface used by a text-capable ChatGPT integration. It does not create,
mutate, authorize, or infer canonical state.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT PRESENTATION

The C2 presentation boundary is read-only and canonical. Hub A is the normal
operational surface; Hub B and the composite are selected contextually.
Pasted reports may contain serialized Hub text as transport input, but that
transport representation is never emitted as the C2 presentation surface.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from sage.c2.hub_presentation_boundary import HubSurface, render_canonical_hub
from sage.c2.immersion_projection import (
    C2ResponseContract,
    MilestoneStrike,
    StrikeFeedProjection,
    project_c2_response_contract,
)
from sage.c2.immersion_state import ImmersionState
from sage.c2.response_envelope import (
    c2_chatgpt_presentation,
    hud_update_key,
    render_station_response,
)


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
    tag = nameplate_mod.render_organism_nameplate(
        manager,
        station_id,
        compact=True,
        state_label=state_label,
    )
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError("SAGE organism name tag rendered empty")
    return tag.strip()


def _render_organism_projection(projection: Any) -> str | None:
    """Render an already-created OrganismAgentProjection without mutation."""
    if projection is None:
        return None
    try:
        renderer = getattr(projection, "render_agent_tag", None)
        if callable(renderer):
            try:
                tag = str(renderer())
            except TypeError:
                tag = str(renderer(projection))
        else:
            projection_mod = importlib.import_module(
                "sage.experimental.airspace.organism_projection"
            )
            tag = str(projection_mod.OrganismProjection.render_agent_tag(projection))
    except Exception as exc:
        raise ValueError("SAGE organism name tag projection failed") from exc
    if not tag.strip():
        raise ValueError("SAGE organism name tag projection rendered empty")
    return tag.strip()


@dataclass(frozen=True)
class ChatGPTImmersionResponse:
    """Read-only response projection for the ChatGPT C2 station.

    Hub visibility is contextual, not sticky: continuity metadata cannot force
    a composite surface, and callers can explicitly select Hub A, Hub B, or the
    composite when the full organism/C2 picture is required.
    """

    station_header: str
    immersion_envelope: C2ResponseContract
    body: str
    milestone: MilestoneStrike | None = None
    strike_feed: StrikeFeedProjection | None = None
    organism_projection: Any | None = None
    organism_tag: str | None = None
    hud_visible: bool = True
    previous_hud_update_key: str | None = None
    force_hud: bool = False
    hub_surface: HubSurface = HubSurface.HUB_A

    @property
    def hud_update_key(self) -> str:
        """Expose the canonical Hub identity for host continuity tracking."""
        return hud_update_key(self.immersion_envelope.hud)

    @property
    def should_render_hud(self) -> bool:
        """Return whether the selected canonical Hub surface must be rendered."""
        return bool(self.hud_visible or self.force_hud)

    def render(self) -> str:
        """Render the selected canonical C2 immersion response."""
        tag = self.organism_tag
        if not tag and self.organism_projection is not None:
            tag = _render_organism_projection(self.organism_projection)
        if not tag:
            raise ValueError("SAGE organism name tag required for C2 immersion response")

        parts = [tag, "", self.immersion_envelope.nameplate.render(), ""]
        if self.should_render_hud:
            hud = self.immersion_envelope.hud.render()
            manager = self.immersion_envelope.hud.organism_manager
            if manager is not None:
                hud = render_canonical_hub(manager, surface=self.hub_surface)
            parts.append(hud)
        parts.extend(["", self.station_header])
        if self.body and self.body.strip():
            parts.extend(["", self.body.strip()])
        return render_station_response("\n".join(parts), c2_chatgpt_presentation())


def project_chatgpt_immersion_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
    strike_feed: StrikeFeedProjection | None = None,
    *,
    organism_manager: object | None = None,
    station_id: Any = None,
    state_label: str = "READY",
    organism_projection: Any | None = None,
    organism_tag: str | None = None,
    manager: Any | None = None,
    hud_visible: bool = True,
    previous_hud_update_key: str | None = None,
    force_hud: bool = False,
    hub_surface: HubSurface = HubSurface.HUB_A,
) -> ChatGPTImmersionResponse:
    """Project canonical state into the read-only ChatGPT C2 surface.

    ``organism_projection`` and ``organism_tag`` preserve explicit
    projection/tag injection capabilities. ``manager`` is a compatibility
    alias for ``organism_manager``. Explicit inputs win; otherwise the
    canonical manager-backed projection is rendered read-only.

    ``hub_surface`` is the presentation choice only; it never creates or
    mutates canonical state.
    """
    tag = organism_tag.strip() if isinstance(organism_tag, str) else organism_tag
    projection = organism_projection
    mgr = organism_manager if organism_manager is not None else manager

    if not tag and projection is not None:
        tag = _render_organism_projection(projection)

    if not tag and mgr is None and projection is None:
        try:
            mgr = _load_airspace_manager()
        except Exception:
            mgr = None

    if not tag and mgr is not None:
        try:
            target_station = _get_station_id(station_id)
            tag = _render_organism_tag(mgr, target_station, state_label)
        except Exception:
            tag = None

    if not tag:
        raise ValueError("SAGE organism name tag required for C2 immersion response")

    contract = project_c2_response_contract(
        state,
        strike_feed=strike_feed,
        organism_projection=projection,
        organism_manager=mgr,
        station_id=station_id,
    )

    return ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed or contract.hud.strike_feed,
        organism_projection=projection,
        organism_tag=tag,
        hud_visible=hud_visible,
        previous_hud_update_key=previous_hud_update_key,
        force_hud=force_hud,
        hub_surface=hub_surface,
    )
