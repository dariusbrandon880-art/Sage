"""Runtime entry point for the repository-defined ChatGPT C2 immersion surface.

This module is the integration boundary between canonical immersion state and a
text-capable ChatGPT host. It deliberately contains no state invention or
mutation: callers provide the canonical state and this module only renders the
already-governed projection.

Architecture:
    GPT -> SAGE RUNTIME -> GOVERNOR -> IMMERSION PROJECTION -> HOST RESPONSE
"""

from __future__ import annotations

import json

from sage.c2.chatgpt_immersion import (
    ChatGPTImmersionResponse,
    project_chatgpt_immersion_response,
)
from sage.c2.immersion_projection import MilestoneStrike
from sage.c2.immersion_state import ImmersionState
from sage.runtime.model_gateway import ModelResponse, SAGERuntime, SAGEStateSnapshot


def render_chatgpt_c2_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
) -> str:
    """Render one canonical C2 response through the ChatGPT immersion surface."""
    if not isinstance(state, ImmersionState) or not state.validate():
        raise ValueError("Cannot render response: canonical ImmersionState is invalid or missing.")
    response: ChatGPTImmersionResponse = project_chatgpt_immersion_response(
        state,
        body=body,
        milestone=milestone,
    )
    return response.render()


def build_chatgpt_c2_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
) -> ChatGPTImmersionResponse:
    """Return the structured read-only ChatGPT immersion response."""
    return project_chatgpt_immersion_response(
        state,
        body=body,
        milestone=milestone,
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
) -> tuple[str, ModelResponse]:
    """Execute GPT through SAGE and render only the reconciled result.

    The model cannot supply the immersion state or bypass ``SAGERuntime``.
    ``SAGERuntime.invoke`` performs envelope construction, optional live
    verification, response reconciliation, and model-output governance before
    anything reaches the renderer.
    """
    response = runtime.invoke(
        adapter,
        task,
        model_role=model_role,
        live_capability=live_capability,
    )
    return render_chatgpt_c2_response(
        immersion_state,
        body=_model_display_text(response),
    ), response


__all__ = [
    "build_chatgpt_c2_response",
    "render_chatgpt_c2_response",
    "render_governed_chatgpt_turn",
]
