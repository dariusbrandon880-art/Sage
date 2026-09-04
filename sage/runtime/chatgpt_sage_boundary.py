"""Hard GPT-to-SAGE boundary for ChatGPT-facing model turns.

The boundary is intentionally the only supported path from a ChatGPT model
adapter to the SAGE immersion renderer. It revalidates model output even when
a custom adapter is supplied, then routes state-changing proposals through
the canonical C2 transition bridge before rendering the resulting state.
"""
from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from sage.c2.canonical_transition_bridge import CanonicalC2TransitionBridge
from sage.c2.chatgpt_runtime import render_chatgpt_c2_response
from sage.c2.immersion_rehydration import build_chatgpt_immersion_state
from sage.c2.immersion_state import ImmersionState
from sage.runtime.model_gateway import ModelAdapter, ModelResponse, SAGERuntime, SAGEProtocolGovernor

class SAGEChatGPTBoundary:
    """Execute ChatGPT only through SAGE governance and canonical state authority."""

    def __init__(self, runtime: SAGERuntime, adapter: ModelAdapter, operational_runtime: Any | None = None) -> None:
        self._runtime = runtime
        self._adapter = adapter
        self._operational_runtime = operational_runtime

    @staticmethod
    def _display_text(response: ModelResponse) -> str:
        raw = response.raw_output
        if not isinstance(raw, str):
            return "SAGE-governed model response accepted."
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(payload, dict) and isinstance(payload.get("response_text"), str):
            return payload["response_text"]
        return "SAGE-governed model response accepted."

    @staticmethod
    def _reject(message: str) -> None:
        raise ValueError(f"SAGE boundary rejection: {message}")

    def respond(
        self,
        task: str,
        *,
        model_role: str,
        immersion_state: ImmersionState,
        live_capability: Any | None = None,
        organism_manager: Any | None = None,
        station_id: Any = None,
        state_label: str = "READY",
        organism_projection: Any | None = None,
        organism_tag: str | None = None,
        manager: Any | None = None,
        session_id: str | None = None,
    ) -> tuple[str, ModelResponse]:
        try:
            response = self._runtime.invoke(self._adapter, task, model_role=model_role, live_capability=live_capability)
        except ValueError as exc:
            self._reject(str(exc))
        raw_output = response.raw_output if isinstance(response.raw_output, str) else ""
        structured = SAGEProtocolGovernor.validate_and_parse(raw_output)
        if structured.violations:
            self._reject("; ".join(structured.violations))
        if structured.station != "[SAGE::C2::CHATGPT]":
            self._reject("station identity mismatch")
        if structured.proposed_actions:
            if self._operational_runtime is None:
                self._reject("state transition proposal has no canonical operational runtime")
            try:
                transition = CanonicalC2TransitionBridge(self._operational_runtime).apply(structured)
            except Exception as exc:
                self._reject(str(exc))
            if transition.accepted:
                response = replace(response, evidence_refs=tuple(dict.fromkeys((*response.evidence_refs, *transition.evidence_refs))), output_state_digest=transition.after_state_digest)
                if not session_id:
                    session_id = immersion_state.flight_id.removeprefix("C2:")
                try:
                    immersion_state = build_chatgpt_immersion_state(
                        self._operational_runtime,
                        session_id=session_id,
                        c2_context={"active_frontier": immersion_state.frontier, "gate": immersion_state.gate},
                        evidence_refs=response.evidence_refs,
                    )
                except Exception as exc:
                    self._reject(f"post-transition immersion rehydration failed: {exc}")
        rendered = render_chatgpt_c2_response(
            immersion_state,
            body=self._display_text(response),
            organism_manager=organism_manager,
            station_id=station_id,
            state_label=state_label,
            organism_projection=organism_projection,
            organism_tag=organism_tag,
            manager=manager,
        )
        return rendered, response

__all__ = ["SAGEChatGPTBoundary"]
