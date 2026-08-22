# SAGE Model Adapters v0.1

## Purpose

Provide real provider transports behind the model-agnostic SAGE runtime gateway without moving state, authority, persistence, or qualification into a model provider.

## Current adapters

- `OpenAIResponsesAdapter` — OpenAI Responses API transport.
- `GeminiInteractionsAdapter` — Google Gemini Interactions API transport.

Both receive a `SAGERuntimeEnvelope` and return `ModelResponse`. `SAGERuntime.invoke()` reconciles the response against the current canonical instance, mission, session, and state digest before returning it to the caller.

## Evidence boundary

Gemini citation URLs returned by provider grounding are captured as `evidence_refs`. They remain external evidence references and are not promoted to canonical truth by the adapter.

## Tool boundary

Provider tools are configuration supplied by the caller. For Gemini, this permits controlled use of tools such as Google Search or remote MCP while leaving execution and authority outside the model adapter. Tool output must still cross SAGE reconciliation and evidence boundaries.

## Security / governance invariants

- API credentials are supplied by the host application/client; they are never stored in SAGE state.
- Provider responses are proposals/evidence, never authorization.
- Adapters do not persist memory or mutate capability state.
- State identity, mission identity, session identity, and input state digest are bound to every response.
- A stale or cross-context response is rejected before authority use.
- Provider citations remain candidate evidence until SAGE validation.
- No automatic promotion, XP/rank mutation, retry control plane, or execution authority is added.

## Platform evidence

OpenAI's current Agents SDK documents the Responses API as its recommended OpenAI model path and supports custom/non-OpenAI model providers. Google documents the Gemini Interactions API with structured output, Google Search grounding, function calling, and remote MCP support. SAGE deliberately keeps those provider capabilities behind its own model envelope and reconciliation boundary.

## STOP boundary

This layer establishes provider transport only. Do not add automatic cross-provider orchestration, persistent provider memory, capability qualification, autonomous promotion, or external authority mutation until a separate governed frontier is authorized and verified.
