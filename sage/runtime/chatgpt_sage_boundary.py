"""Hard GPT-to-SAGE boundary for ChatGPT-facing model turns.

The boundary is intentionally the only supported path from a ChatGPT model
adapter to the SAGE immersion renderer.  It revalidates model output even when
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

    def respond(
        self,
        task: str,
        *,
        model_role: str,
        immersion_state: ImmersionState,
        live_capability: Any | None = None,
    ) -> tuple[str, ModelResponse]:
        """Run one model turn and expose only the SAGE-rendered response."""
        response = self._runtime.invoke(
            self._adapter,
            task,
            model_role=model_role,
            live_capability=live_capability,
        )

        raw_output = response.raw_output if isinstance(response.raw_output, str) else ""
        structured = SAGEProtocolGovernor.validate_and_parse(raw_output)
        if structured.violations:
            raise ValueError("SAGE boundary rejection: " + " | ".join(structured.violations))
        if structured.station != "[SAGE::C2::CHATGPT]":
            raise ValueError("SAGE boundary rejection: model station identity mismatch")

        rendered = render_chatgpt_c2_response(
            immersion_state,
            body=self._display_text(response),
        )
        return rendered, response


__all__ = ["SAGEChatGPTBoundary"]
