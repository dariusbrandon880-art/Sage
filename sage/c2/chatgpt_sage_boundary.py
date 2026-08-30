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
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
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
    """Execute one GPT turn through SAGE governance and Full-SAGE render."""
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


def execute_sage_bound_chatgpt_from_legacy_runtime(
    *,
    runtime: Any,
    session_id: str,
    task: str,
    c2_context: dict[str, Any],
    response_override: str | None = None,
    live_capability: Any = None,
) -> SAGEBoundChatGPTResponse:
    """Adapt the existing ``sage.runtime.engine.SageRuntime`` into the boundary.

    Required frontier/gate/next-move values must be supplied by C2 context. The
    adapter refuses to invent them, so an incomplete context fails closed.
    """
    required = ("frontier", "gate", "next_move")
    missing = [key for key in required if not str(c2_context.get(key, "")).strip()]
    if missing:
        raise ValueError(
            "SAGE C2 immersion context incomplete; missing: " + ", ".join(missing)
        )

    mission = str(
        c2_context.get("mission")
        or c2_context.get("mission_id")
        or runtime.current_state.current_objective
        or "SAGE C2 Mission"
    )
    evidence_refs = tuple(str(ref) for ref in c2_context.get("evidence_refs", ()))
    provenance_head = str(c2_context.get("provenance_head", ""))
    runtime_state = SAGEStateSnapshot(
        state_version=str(c2_context.get("state_version", "sage-runtime-v1")),
        instance_id=str(c2_context.get("instance_id", "sage-runtime")),
        mission_id=str(c2_context.get("mission_id", mission)),
        session_id=session_id,
        authority_scope=str(c2_context.get("authority_scope", "human-operator")),
        active_frontier=str(c2_context["frontier"]),
        stop_boundary=str(c2_context.get("stop_boundary", "SAGE C2 fail-closed boundary")),
        evidence_refs=evidence_refs,
        known_state_refs=tuple(str(x) for x in c2_context.get("known_state_refs", ())),
        candidate_state_refs=tuple(str(x) for x in c2_context.get("candidate_state_refs", ())),
        negative_memory_refs=tuple(str(x) for x in c2_context.get("negative_memory_refs", ())),
    )
    immersion_state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission=mission,
        phase=ExecutionPhase.EXECUTE,
        flight_id=str(c2_context.get("flight_id", session_id)),
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.UNVERIFIED,
        frontier=str(c2_context["frontier"]),
        gate=str(c2_context["gate"]),
        next_move=str(c2_context["next_move"]),
        evidence_refs=evidence_refs,
        provenance_head=provenance_head or runtime_state.digest(),
    )
    return execute_sage_bound_chatgpt(
        runtime_state=runtime_state,
        immersion_state=immersion_state,
        task=task,
        response_override=response_override,
        live_capability=live_capability,
    )
