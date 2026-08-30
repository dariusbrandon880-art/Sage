"""SAGE-governed OpenAI model adapter.

The adapter is deliberately downstream of ``SAGERuntime``.  It receives a
canonical runtime envelope, calls the OpenAI Responses API, parses the model
proposal through ``SAGEProtocolGovernor``, and returns a ``ModelResponse``.
The model never becomes canonical authority and cannot bypass the runtime
reconciliation boundary.
"""
from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from sage.runtime.model_gateway import (
    ModelResponse,
    SAGEProtocolGovernor,
    SAGERuntimeEnvelope,
)


class OpenAIModelAdapter:
    """OpenAI transport implementing the SAGE ``ModelAdapter`` protocol."""

    model_id: str
    station: str = "[SAGE::C2::CHATGPT]"

    def __init__(
        self,
        *,
        client: Any | None = None,
        model_id: str | None = None,
    ) -> None:
        self.model_id = model_id or os.getenv("SAGE_OPENAI_MODEL", "gpt-5.6-luna")
        self._client = client or OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    @staticmethod
    def _instructions(envelope: SAGERuntimeEnvelope) -> str:
        return (
            "You are operating as a SAGE model worker. SAGE is the authority; "
            "your output is proposal/evidence only. Return ONLY a JSON object "
            "with keys: station, reasoning_chain, proposed_actions, "
            "epistemic_state, evidence_refs. Do not claim canonical state mutation, "
            "authorization, completion, or verification without evidence.\n\n"
            f"SAGE ENVELOPE:\n{envelope.to_payload()}"
        )

    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse:
        """Call OpenAI only with the SAGE envelope and parse through the governor."""
        response = self._client.responses.create(
            model=self.model_id,
            instructions=self._instructions(envelope),
            input=task,
        )
        raw_output = response.output_text
        structured = SAGEProtocolGovernor.validate_and_parse(raw_output)
        if structured.violations:
            raise ValueError(
                "SAGE model-output governance rejection: "
                + " | ".join(structured.violations)
            )

        evidence_refs = tuple(structured.evidence_refs)
        proposed_actions = tuple(
            {
                "action_type": action.action_type,
                "target": action.target,
                "parameters": action.parameters,
                "justification": action.justification,
            }
            for action in structured.proposed_actions
        )
        return ModelResponse(
            model_id=self.model_id,
            instance_id=envelope.state.instance_id,
            mission_id=envelope.state.mission_id,
            session_id=envelope.state.session_id,
            input_state_digest=envelope.state_digest,
            proposed_actions=proposed_actions,
            evidence_refs=evidence_refs,
            raw_output=raw_output,
            structured_response=structured,
        )
