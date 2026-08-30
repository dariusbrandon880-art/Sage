"""ChatGPT-facing C2 immersion response adapter.

This module composes already-canonical SAGE projections into the response
surface used by a text-capable ChatGPT integration. It does not create,
mutate, authorize, or infer canonical state.

Architecture:
    CANONICAL STATE -> PROJECTION -> CHATGPT PRESENTATION
"""

from __future__ import annotations

from dataclasses import dataclass

from sage.c2.immersion_projection import (
    C2ResponseContract,
    MilestoneStrike,
    project_c2_response_contract,
)
from sage.c2.immersion_state import ImmersionState
from sage.c2.response_envelope import c2_chatgpt_presentation, render_station_response


@dataclass(frozen=True)
class ChatGPTImmersionResponse:
    """Read-only response projection for the ChatGPT C2 station."""

    station_header: str
    immersion_envelope: C2ResponseContract
    body: str
    milestone: MilestoneStrike | None = None

    def render(self) -> str:
        """Render the complete response without creating canonical state."""
        body = self.immersion_envelope.render_full_envelope(self.body)
        return render_station_response(body, c2_chatgpt_presentation())


def project_chatgpt_immersion_response(
    state: ImmersionState,
    body: str = "",
    milestone: MilestoneStrike | None = None,
) -> ChatGPTImmersionResponse:
    """Project a canonical state into the ChatGPT C2 response surface."""
    contract = project_c2_response_contract(state)
    return ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body=body,
        milestone=milestone,
    )
