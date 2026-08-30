"""Runtime entry point for the repository-defined ChatGPT C2 immersion surface.

This module is the integration boundary between canonical immersion state and a
text-capable ChatGPT host. It deliberately contains no state invention or
mutation: callers provide the canonical ``ImmersionState`` and this module
only renders the already-governed projection.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT ADAPTER -> HOST RESPONSE
"""

from __future__ import annotations

from sage.c2.chatgpt_immersion import (
    ChatGPTImmersionResponse,
    project_chatgpt_immersion_response,
)
from sage.c2.immersion_projection import MilestoneStrike
from sage.c2.immersion_state import ImmersionState


def render_chatgpt_c2_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
) -> str:
    """Render one canonical C2 response through the ChatGPT immersion surface.

    The canonical state is the sole source of truth.  This function is a pure
    presentation boundary and cannot create, authorize, mutate, or award state.
    """
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
