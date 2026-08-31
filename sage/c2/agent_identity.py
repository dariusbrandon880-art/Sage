"""Governed agent-boundary identity projections for SAGE interfaces.

External builders may expose a stable self-owned nameplate, but the nameplate is
never an authority grant. Session identity must come from the governed runtime;
callers cannot supply a synthetic flight or station identity through this API.
"""
from __future__ import annotations

from dataclasses import dataclass


GOOGLE_AGENT_NAMEPLATE = "[SAGE::INTEL::GEMINI]"
JULES_AGENT_NAMEPLATE = "[SAGE::ENGINEER::JULES]"
CHATGPT_AGENT_NAMEPLATE = "[SAGE::C2::CHATGPT]"


@dataclass(frozen=True)
class AgentBoundaryIdentity:
    """Read-only identity projection for an external interface participant."""

    agent: str
    session_id: str
    nameplate: str

    @property
    def authority(self) -> str:
        """Identity provenance; never an authorization grant."""
        return "governed_runtime_session"


def build_google_nameplate(*, session_id: str) -> AgentBoundaryIdentity:
    """Generate Google's Gemini boundary nameplate for one runtime session.

    ``session_id`` must be supplied by the governed runtime. A browser, prompt,
    or caller cannot manufacture a session identity through this function.
    """
    normalized = str(session_id).strip()
    if not normalized:
        raise ValueError("Google nameplate requires a governed runtime session_id")
    if normalized.startswith("FLIGHT_"):
        raise ValueError("Synthetic flight identity cannot bind Google nameplate")
    return AgentBoundaryIdentity(
        agent="GEMINI",
        session_id=normalized,
        nameplate=GOOGLE_AGENT_NAMEPLATE,
    )
