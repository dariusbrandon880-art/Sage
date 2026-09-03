"""Runtime entry point for the repository-defined ChatGPT C2 immersion surface.

This module is the integration boundary between canonical immersion state and a
text-capable ChatGPT host. It deliberately contains no state invention or
mutation: callers provide the canonical state and this module only renders the
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
from sage.c2.immersion_projection import MilestoneStrike, StrikeFeedProjection
from sage.c2.immersion_state import ImmersionState
from sage.experimental.airspace.turn_engine import TurnResolution, TurnStatus
from sage.runtime.model_gateway import ModelResponse, SAGERuntime, SAGEStateSnapshot


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
) -> str:
    """Render one canonical C2 response through the ChatGPT immersion surface."""
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
) -> tuple[str, ModelResponse]:
    """Execute GPT through SAGE and render only the reconciled result."""
    response = runtime.invoke(
        adapter,
        task,
        model_role=model_role,
        live_capability=live_capability,
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
    ), response


def render_resolved_chatgpt_turn(
    *,
    manager: object,
    immersion_state: ImmersionState,
    resolution: TurnResolution,
    station_id: Any,
    body: str = "",
    state_label: str = "READY",
) -> str:
    """Render a freshly reconciled HUD after SAGE closes a verified turn."""
    if resolution.status is not TurnStatus.CLOSED or not resolution.verified:
        raise ValueError("Only verified closed turns may refresh the organism HUD.")
    return render_chatgpt_c2_response(
        immersion_state,
        body=body,
        organism_manager=manager,
        station_id=station_id,
        state_label=state_label,
    )


__all__ = [
    "build_chatgpt_c2_response",
    "render_chatgpt_c2_response",
    "render_governed_chatgpt_turn",
    "render_resolved_chatgpt_turn",
]
