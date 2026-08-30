"""Fail-closed GPT -> SAGE C2 runtime boundary.

The boundary is the only supported path for a GPT-facing SAGE turn:

    GPT request
        -> SAGE runtime envelope
        -> model adapter
        -> protocol/evidence validation
        -> immutable immersion projection
        -> ChatGPT response surface

This module owns transport only. Canonical state, authorization, evidence, and
presentation state remain SAGE-owned inputs. It never mutates or invents state.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from sage.c2.chatgpt_runtime import render_chatgpt_c2_response
from sage.c2.immersion_state import ImmersionState
from sage.runtime.model_gateway import (
    ModelResponse,
    SAGEProtocolGovernor,
    SAGERuntime,
    SAGERuntimeEnvelope,
    SAGEStateSnapshot,
)


@dataclass(frozen=True)
class SAGEBoundChatGPTResponse:
    """Response that has crossed the SAGE governance and render boundary."""

    raw_output: str
    rendered_output: str
    state_digest: str
    evidence_refs: tuple[str, ...]


class OpenAIChatGPTAdapter:
    """OpenAI transport adapter. It has no authority outside ``SAGERuntime``."""

    model_id = "gpt-4o-mini"
    station = "[SAGE::C2::CHATGPT]"

    def __init__(self, *, api_key: str | None = None, response_override: str | None = None):
        self.api_key = (api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
        self.response_override = response_override

    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse:
        if self.response_override is not None:
            raw_output = self.response_override
        else:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            import openai

            instructions = (
                "You are the model adapter operating inside SAGE C2.\n"
                "Return ONLY a JSON object conforming to structured_sage_response_v1.\n"
                "The runtime, not the model, owns authorization and canonical state.\n"
                "Do not claim completion, mutation, authorization, verification, or repository changes without evidence_refs.\n"
                f"SAGE runtime envelope: {json.dumps(envelope.to_payload(), default=str, sort_keys=True)}\n"
            )
            response = openai.OpenAI(api_key=self.api_key).responses.create(
                model=self.model_id,
                instructions=instructions,
                input=task,
            )
            raw_output = str(response.output_text or "").strip()
            if not raw_output:
                raise ValueError("Empty or malformed output received from OpenAI Responses API")

        structured = SAGEProtocolGovernor.validate_and_parse(
            raw_output,
            required_station=self.station,
        )
        if structured.violations:
            raise RuntimeError(
                "SAGE Protocol Governance Violation: " + "; ".join(structured.violations)
            )

        return ModelResponse(
            model_id=self.model_id,
            instance_id=envelope.state.instance_id,
            mission_id=envelope.state.mission_id,
            session_id=envelope.state.session_id,
            input_state_digest=envelope.state_digest,
            proposed_actions=tuple(
                {
                    "action_type": action.action_type,
                    "target": action.target,
                    "parameters": action.parameters,
                    "justification": action.justification,
                }
                for action in structured.proposed_actions
            ),
            evidence_refs=structured.evidence_refs,
            raw_output=raw_output,
            structured_response=structured,
        )


def execute_sage_bound_chatgpt(
    *,
    runtime_state: SAGEStateSnapshot,
    immersion_state: ImmersionState,
    task: str,
    response_override: str | None = None,
    live_capability: Any = None,
) -> SAGEBoundChatGPTResponse:
    """Execute one GPT turn through SAGE governance and Full-SAGE render.

    The function fails closed if either canonical state is invalid, if a required
    live capability is absent, if the model violates the SAGE output contract, or
    if the response cannot be reconciled to the supplied runtime state.
    """
    if not immersion_state.validate():
        raise ValueError("Invalid canonical immersion state")

    runtime = SAGERuntime(runtime_state)
    adapter = OpenAIChatGPTAdapter(response_override=response_override)
    response = runtime.invoke(
        adapter,
        task,
        model_role="C2 Mission Control",
        live_capability=live_capability,
    )

    if response.structured_response is None or response.structured_response.violations:
        raise RuntimeError("SAGE response contract was not satisfied")

    rendered = render_chatgpt_c2_response(
        immersion_state,
        body=response.raw_output if response.raw_output is not None else "",
    )

    return SAGEBoundChatGPTResponse(
        raw_output=str(response.raw_output or ""),
        rendered_output=rendered,
        state_digest=runtime_state.digest(),
        evidence_refs=tuple(response.evidence_refs),
    )
