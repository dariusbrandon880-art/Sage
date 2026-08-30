"""Provider adapters for the SAGE model gateway.

Adapters perform transport only. They do not receive SAGE authority, mutate
canonical state, persist memory, or qualify capabilities.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from sage.c2.chatgpt_c2_contract import render_system_contract
from sage.runtime.model_gateway import ModelResponse, SAGERuntimeEnvelope


class OpenAIResponsesAdapter:
    """OpenAI Responses API adapter behind the SAGE model contract."""

    station = "[SAGE::C2::CHATGPT]"

    def __init__(self, client: Any, *, model_id: str):
        self.client = client
        self.model_id = model_id

    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse:
        from sage.runtime.model_gateway import SAGEProtocolGovernor

        response = self.client.responses.create(
            model=self.model_id,
            instructions=_system_instructions(envelope),
            input=task,
        )
        text = getattr(response, "output_text", None)
        if text is None:
            raise ValueError("OpenAI response did not contain output_text")

        structured = SAGEProtocolGovernor.validate_and_parse(text, required_station=self.station)
        if structured.violations:
            raise ValueError(f"SAGE Protocol Governance Violation: {'; '.join(structured.violations)}")

        return ModelResponse(
            model_id=self.model_id,
            instance_id=envelope.state.instance_id,
            mission_id=envelope.state.mission_id,
            session_id=envelope.state.session_id,
            input_state_digest=envelope.state_digest,
            station=envelope.station,
            policy_version=envelope.policy_version,
            policy_digest=envelope.policy_digest,
            provenance_digest=envelope.provenance_digest,
            raw_output=text,
            structured_response=structured,
            evidence_refs=structured.evidence_refs,
        )


class GeminiInteractionsAdapter:
    """Google Gemini Interactions API adapter behind the SAGE model contract."""

    station = "[SAGE::INTEL::GEMINI]"

    def __init__(
        self,
        client: Any,
        *,
        model_id: str,
        tools: Sequence[Mapping[str, Any]] = (),
    ):
        self.client = client
        self.model_id = model_id
        self.tools = tuple(tools)

    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse:
        from sage.runtime.model_gateway import SAGEProtocolGovernor

        request: dict[str, Any] = {
            "model": self.model_id,
            "input": _gemini_input(envelope, task),
        }
        if self.tools:
            request["tools"] = [dict(tool) for tool in self.tools]
        interaction = self.client.interactions.create(**request)
        text = getattr(interaction, "output_text", None)
        if text is None:
            raise ValueError("Gemini interaction did not contain output_text")

        structured = SAGEProtocolGovernor.validate_and_parse(text, required_station=self.station)
        if structured.violations:
            raise ValueError(f"SAGE Protocol Governance Violation: {'; '.join(structured.violations)}")

        evidence_refs = _extract_url_citations(interaction)
        evidence_refs = tuple(dict.fromkeys((*structured.evidence_refs, *evidence_refs)))
        return ModelResponse(
            model_id=self.model_id,
            instance_id=envelope.state.instance_id,
            mission_id=envelope.state.mission_id,
            session_id=envelope.state.session_id,
            input_state_digest=envelope.state_digest,
            station=envelope.station,
            policy_version=envelope.policy_version,
            policy_digest=envelope.policy_digest,
            provenance_digest=envelope.provenance_digest,
            evidence_refs=evidence_refs,
            raw_output=text,
            structured_response=structured,
        )


def _system_instructions(envelope: SAGERuntimeEnvelope) -> str:
    payload = json.dumps(envelope.to_payload(), sort_keys=True, separators=(",", ":"))
    return (
        "You are operating under the SAGE Autonomous Continuity Runtime Protocol.\n"
        f"{render_system_contract()}\n"
        "STRICT GOVERNANCE RULES:\n"
        "1. NO ROLEPLAY: You are operating in real reality, not roleplay or simulation mode. Do not use roleplay markers, persona fluff, or conversational narrative.\n"
        "2. NO MUTATION AUTHORITY: Model output does NOT constitute authorization, autonomous execution, or canonical state mutation. Human operators hold authority.\n"
        "3. STRUCTURED PROPOSALS ONLY: Provide clear reasoning chains, proposed actions, evidence references, and epistemic states.\n"
        "4. DEEP RECON WITHOUT DRAG: For substantive tasks, lock repository reality first, then use only relevant primary external research. Run independent research and inspection concurrently when possible; never turn research into a serial waiting gate.\n"
        "5. EVIDENCE CLASSIFICATION: Label repository facts, external intelligence, inference, and unverified claims distinctly. Never let external research override live repository truth.\n"
        "6. IDENTITY IS BOUND: Treat the envelope station, agent identity, policy version, state digest, and provenance digest as immutable governance context. Do not invent, replace, or reinterpret them.\n"
        f"The envelope is authoritative context. Return structured output according to {envelope.required_output_contract}.\n"
        f"SAGE_ENVELOPE={payload}"
    )


def _gemini_input(envelope: SAGERuntimeEnvelope, task: str) -> str:
    return f"{_system_instructions(envelope)}\n\nTASK:\n{task}"


def _extract_url_citations(interaction: Any) -> list[str]:
    """Extract provider citations without treating them as canonical truth."""
    refs: list[str] = []
    for step in getattr(interaction, "steps", ()) or ():
        for block in getattr(step, "content", ()) or ():
            for annotation in getattr(block, "annotations", ()) or ():
                url = getattr(annotation, "url", None)
                if url:
                    refs.append(str(url))
    return refs
