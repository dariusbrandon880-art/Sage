"""Runtime entry point for the repository-defined ChatGPT C2 immersion surface.

This module is the integration boundary between canonical immersion state and a
text-capable ChatGPT host. It deliberately contains no state invention or
mutation: callers provide canonical state and this module only renders the
already-governed projection.

Architecture:
    GPT -> SAGE RUNTIME -> GOVERNOR -> IMMERSION PROJECTION -> ORGANISM PROJECTION -> HOST RESPONSE
"""

from __future__ import annotations

import json
from typing import Any

from sage.c2.chatgpt_immersion import (
    ChatGPTImmersionResponse,
    project_chatgpt_immersion_response,
)
from sage.c2.hub_presentation_boundary import HubSurface
from sage.c2.immersion_projection import MilestoneStrike, StrikeFeedProjection
from sage.c2.immersion_state import ImmersionState
from sage.runtime.model_gateway import ModelResponse, SAGERuntime


_ORGANISM_CONTEXT_TERMS = (
    "organism", "agent projection", "career", "career xp", "xp", "points",
    "rank", "badge", "boss", "promotion", "progression", "qualification",
)
_COMPOSITE_CONTEXT_TERMS = (
    "full c2", "full picture", "organism state", "rehydrate", "reconvergence",
    "mission briefing", "mission debrief", "complete hud", "both hubs",
)


def select_contextual_hub_surface(
    task: str = "",
    body: str = "",
    *,
    explicit: HubSurface | None = None,
) -> HubSurface:
    """Select the canonical visual surface without creating a new HUD.

    Explicit selection always wins. Otherwise operational work defaults to Hub
    A, organism/progression work selects Hub B, and full-state transitions use
    the explicit composite. This is presentation routing only; canonical state
    and authority remain elsewhere.
    """
    if explicit is not None:
        return explicit
    normalized = f"{task} {body}".lower()
    if any(term in normalized for term in _COMPOSITE_CONTEXT_TERMS):
        return HubSurface.COMPOSITE
    if any(term in normalized for term in _ORGANISM_CONTEXT_TERMS):
        return HubSurface.HUB_B
    return HubSurface.HUB_A


def render_chatgpt_c2_response(
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
) -> str:
    """Render one canonical C2 response through the selected Hub surface."""
    response: ChatGPTImmersionResponse = project_chatgpt_immersion_response(
        state,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed,
        organism_manager=organism_manager,
        station_id=station_id,
        state_label=state_label,
        organism_projection=organism_projection,
        organism_tag=organism_tag,
        manager=manager,
        hud_visible=hud_visible,
        previous_hud_update_key=previous_hud_update_key,
        force_hud=force_hud,
        hub_surface=hub_surface,
    )
    return response.render()


def build_chatgpt_c2_response(
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
    """Return the structured read-only ChatGPT immersion response."""
    return project_chatgpt_immersion_response(
        state,
        body=body,
        milestone=milestone,
        strike_feed=strike_feed,
        organism_manager=organism_manager,
        station_id=station_id,
        state_label=state_label,
        organism_projection=organism_projection,
        organism_tag=organism_tag,
        manager=manager,
        hud_visible=hud_visible,
        previous_hud_update_key=previous_hud_update_key,
        force_hud=force_hud,
        hub_surface=hub_surface,
    )


def _model_display_text(response: ModelResponse) -> str:
    """Extract only an explicit display field; never expose model reasoning."""
    raw = response.raw_output
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(parsed, dict) and isinstance(parsed.get("response_text"), str):
            return parsed["response_text"]
    return "SAGE-governed model response accepted."


def render_governed_chatgpt_turn(
    runtime: SAGERuntime,
    adapter: object,
    task: str,
    *,
    model_role: str,
    immersion_state: ImmersionState,
    live_capability: object | None = None,
    organism_manager: object | None = None,
    station_id: Any = None,
    state_label: str = "READY",
    organism_projection: Any | None = None,
    organism_tag: str | None = None,
    manager: Any | None = None,
    hud_visible: bool = True,
    previous_hud_update_key: str | None = None,
    force_hud: bool = False,
    hub_surface: HubSurface | None = None,
) -> tuple[str, ModelResponse]:
    """Execute GPT through SAGE and render only the reconciled result."""
    response = runtime.invoke(
        adapter,
        task,
        model_role=model_role,
        live_capability=live_capability,
    )
    selected_surface = select_contextual_hub_surface(
        task,
        _model_display_text(response),
        explicit=hub_surface,
    )
    return render_chatgpt_c2_response(
        immersion_state,
        body=_model_display_text(response),
        organism_manager=organism_manager,
        station_id=station_id,
        state_label=state_label,
        organism_projection=organism_projection,
        organism_tag=organism_tag,
        manager=manager,
        hud_visible=hud_visible,
        previous_hud_update_key=previous_hud_update_key,
        force_hud=force_hud,
        hub_surface=selected_surface,
    ), response


def render_resolved_chatgpt_turn(
    *,
    manager: object,
    immersion_state: ImmersionState,
    resolution: Any,
    station_id: Any,
    body: str = "",
    state_label: str = "READY",
    hub_surface: HubSurface | None = None,
) -> str:
    """Render a freshly reconciled Hub after SAGE closes a verified turn."""
    status = getattr(resolution, "status", None)
    status_value = getattr(status, "value", status)
    if status_value != "CLOSED" or not bool(getattr(resolution, "verified", False)):
        raise ValueError("Only verified closed turns may refresh the organism HUD.")
    selected_surface = select_contextual_hub_surface(body, explicit=hub_surface)
    return render_chatgpt_c2_response(
        immersion_state,
        body=body,
        organism_manager=manager,
        station_id=station_id,
        state_label=state_label,
        hub_surface=selected_surface,
    )


def execute_playable_organism_turn(
    *,
    session_id: str,
    turn_id: str,
    station_id: str,
    action_name: str,
    evidence_refs: tuple[str, ...],
    verified_event_ref: str,
    ledger_path: object | None = None,
    mission_id: str = "MISSION-PLAYABLE-001",
    objective: str = "Execute persistent playable organism turn",
    target: str = "AIRSPACE_C2",
    exact_git_head: str | None = None,
    required_cql: int = 1,
    required_sql: int = 0,
    hub_surface: HubSurface = HubSurface.COMPOSITE,
    body_summary: str = "",
) -> Any:
    """Execute the complete 10-step playable organism interaction loop via C2 runtime."""
    from sage.c2.organism_runtime_contract import OrganismRuntimeContractEngine

    engine = OrganismRuntimeContractEngine(ledger_path=ledger_path)
    return engine.execute_playable_turn(
        session_id=session_id,
        turn_id=turn_id,
        station_id_str=station_id,
        action_name=action_name,
        evidence_refs=evidence_refs,
        verified_event_ref=verified_event_ref,
        mission_id=mission_id,
        objective=objective,
        target=target,
        exact_git_head=exact_git_head,
        required_cql=required_cql,
        required_sql=required_sql,
        hub_surface=hub_surface,
        body_summary=body_summary,
    )


def rehydrate_playable_organism_state(ledger_path: object | None = None) -> Any:
    """Rehydrate current AirspaceState directly from persistent event ledger."""
    from sage.c2.organism_runtime_contract import OrganismRuntimeContractEngine

    engine = OrganismRuntimeContractEngine(ledger_path=ledger_path)
    return engine.rehydrate_state()


def render_playable_organism_turn(
    runtime: Any = None,
    *,
    session_id: str,
    action_name: str,
    task: str = "",
    evidence_refs: tuple[str, ...] = (),
    manager: Any = None,
    c2_context: dict[str, Any] | None = None,
    xp_award: int = 50,
    points_award: int = 25,
) -> tuple[str, Any]:
    """Execute a complete 10-step playable turn and render the rehydrated C2 response."""
    from sage.c2.organism_runtime_contract import OrganismRuntimeContractEngine
    engine = OrganismRuntimeContractEngine(runtime=runtime, manager=manager)
    receipt = engine.execute_turn(
        session_id=session_id,
        action_name=action_name,
        task=task,
        evidence_refs=evidence_refs,
        c2_context=c2_context,
        xp_award=xp_award,
        points_award=points_award,
    )
    return receipt.hud_projection, receipt


__all__ = [
    "build_chatgpt_c2_response",
    "execute_playable_organism_turn",
    "rehydrate_playable_organism_state",
    "render_chatgpt_c2_response",
    "render_governed_chatgpt_turn",
    "render_playable_organism_turn",
    "render_resolved_chatgpt_turn",
    "select_contextual_hub_surface",
]
