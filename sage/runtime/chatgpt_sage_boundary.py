"""Hard GPT-to-SAGE boundary for ChatGPT-facing model turns.

The boundary is intentionally the only supported path from a ChatGPT model
adapter to the SAGE immersion renderer. It revalidates model output even when
a custom adapter is supplied, so an adapter cannot bypass SAGE governance.
"""
from __future__ import annotations

import json
from typing import Any

from sage.c2.chatgpt_runtime import render_chatgpt_c2_response
from sage.c2.immersion_state import ImmersionState
from sage.runtime.model_gateway import ModelAdapter, ModelResponse, SAGERuntime, SAGEProtocolGovernor


class SAGEChatGPTBoundary:
    """Execute a ChatGPT model only through the SAGE runtime and renderer."""

    def __init__(self, runtime: SAGERuntime, adapter: ModelAdapter) -> None:
        self._runtime = runtime
        self._adapter = adapter

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
        """Expose one stable fail-closed contract at the ChatGPT boundary."""
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
    ) -> tuple[str, ModelResponse]:
        """Run one model turn and expose only the SAGE-rendered response.

        Organism projection/tag inputs are presentation-only and remain behind
        the same fail-closed governance boundary as the model response.
        """
        try:
            response = self._runtime.invoke(
                self._adapter,
                task,
                model_role=model_role,
                live_capability=live_capability,
            )
        except ValueError as exc:
            self._reject(str(exc))

        raw_output = response.raw_output if isinstance(response.raw_output, str) else ""
        structured = SAGEProtocolGovernor.validate_and_parse(raw_output)
        if structured.violations:
            self._reject("; ".join(structured.violations))
        if structured.station != "[SAGE::C2::CHATGPT]":
            self._reject("station identity mismatch")

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
