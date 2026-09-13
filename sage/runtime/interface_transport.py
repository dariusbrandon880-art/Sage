"""Transport-neutral boundary for external SAGE interface surfaces.

The adapter is deliberately narrower than a model adapter: browser/UI traffic is
untrusted observation data, while canonical identity and immersion projection
remain owned by the existing SAGE runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from sage.c2.immersion_state import ImmersionState


CHATGPT_DOM_SURFACE = "CHATGPT_DOM_SURFACE"


@dataclass(frozen=True)
class InterfaceObservation:
    """Untrusted telemetry captured from an external presentation surface."""

    session_id: str
    source_event_id: str
    sequence: int
    raw_text: str
    is_complete: bool = False
    origin_boundary: str = CHATGPT_DOM_SURFACE

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("interface observation requires session_id")
        if not self.source_event_id.strip():
            raise ValueError("interface observation requires source_event_id")
        if self.sequence < 0:
            raise ValueError("interface observation sequence must be non-negative")
        if self.origin_boundary != CHATGPT_DOM_SURFACE:
            raise ValueError("unsupported interface observation origin")


@dataclass(frozen=True)
class InterfaceProjection:
    """Read-only projection emitted from canonical runtime-derived immersion."""

    session_id: str
    station_identity: str
    immersion: Mapping[str, object]
    provenance_head: str
    field_c2_envelope: Mapping[str, object] | None = None
    hud_update_key: str | None = None
    rendered_response: str | None = None

    @classmethod
    def from_immersion(
        cls,
        session_id: str,
        state: ImmersionState,
        *,
        field_c2_envelope: Mapping[str, object] | None = None,
        hud_update_key: str | None = None,
        rendered_response: str | None = None,
    ) -> "InterfaceProjection":
        if state.station_identity != "[SAGE::C2::CHATGPT]":
            raise ValueError("interface projection requires canonical ChatGPT station")
        if not state.validate():
            raise ValueError("interface projection requires valid immersion state")
        return cls(
            session_id=session_id,
            station_identity=state.station_identity,
            immersion=state.to_dict(),
            provenance_head=state.provenance_head,
            field_c2_envelope=field_c2_envelope,
            hud_update_key=hud_update_key,
            rendered_response=rendered_response,
        )


class ImmersionProjector(Protocol):
    def __call__(self, session_id: str) -> ImmersionState: ...


class CommandAuthorizer(Protocol):
    def __call__(self, session_id: str, command: str) -> str: ...


class InterfaceTransportAdapter:
    """Bind an external interface to an existing SAGE runtime without authority duplication."""

    def __init__(
        self,
        runtime: Any,
        *,
        immersion_projector: ImmersionProjector,
        command_authorizer: CommandAuthorizer | None = None,
    ) -> None:
        self._runtime = runtime
        self._immersion_projector = immersion_projector
        self._command_authorizer = command_authorizer

    def _validate_session(self, session_id: str) -> None:
        canonical_state = getattr(self._runtime, "state", None)
        canonical_session = getattr(canonical_state, "session_id", None)
        if not canonical_session:
            raise ValueError("interface transport requires canonical runtime session")
        if session_id != canonical_session:
            raise ValueError("interface transport session identity mismatch")

    def observe(self, observation: InterfaceObservation) -> InterfaceProjection:
        """Accept telemetry but never promote it to canonical state."""
        self._validate_session(observation.session_id)
        state = self._immersion_projector(observation.session_id)
        return InterfaceProjection.from_immersion(observation.session_id, state)

    def authorize_command(self, session_id: str, command: str) -> str:
        """Route commands only through an explicitly supplied governance callback."""
        self._validate_session(session_id)
        if self._command_authorizer is None:
            raise ValueError("interface transport command path is not configured")
        if not command.strip():
            raise ValueError("interface command cannot be empty")
        return self._command_authorizer(session_id, command)

    def ingest_jules_report(
        self,
        report: Any,
        *,
        canonical_git_sha: str,
        organism_manager: Any | None = None,
        previous_hud_update_key: str | None = None,
        force_hud: bool = False,
    ) -> InterfaceProjection:
        """Ingest a Jules report and return a read-only InterfaceProjection driving Tower-C2 HUD."""
        import importlib
        ingestion_mod = importlib.import_module("sage.c2.jules_report_ingestion")

        immersion_state, response, result = ingestion_mod.rehydrate_c2_from_jules_report(
            self._runtime,
            report,
            canonical_git_sha=canonical_git_sha,
            organism_manager=organism_manager,
            previous_hud_update_key=previous_hud_update_key,
            force_hud=force_hud,
        )

        session_id = str(getattr(report, "session_id", None) or getattr(result, "session_id", "session"))
        return InterfaceProjection.from_immersion(
            session_id=session_id,
            state=immersion_state,
            field_c2_envelope=result.field_c2_envelope,
            hud_update_key=result.hud_update_key,
            rendered_response=response.render() if hasattr(response, "render") else str(response),
        )


__all__ = [
    "CHATGPT_DOM_SURFACE",
    "CommandAuthorizer",
    "ImmersionProjector",
    "InterfaceObservation",
    "InterfaceProjection",
    "InterfaceTransportAdapter",
]
