# SAGE Google + Gemini Bridge v0.1

## Purpose

SAGE is entering an inventor-stage operating mode: learn from external systems, standards, and competing agent architectures, then convert useful discoveries into bounded executable capability without surrendering canonical authority.

This bridge makes Google/Gemini a governed intelligence participant in the SAGE loop rather than a second source of truth.

## External evidence incorporated

- Gemini Apps currently supports custom Connected Apps through MCP server URLs for eligible Gemini Spark users. Google documents that the custom MCP server is third-party infrastructure and that write actions receive manual confirmation in Gemini. This is the consumer-facing path for connecting a deployed SAGE MCP surface to Gemini Apps.
- Gemini API supports function calling, structured outputs, Google Search, URL Context, File Search, Code Execution, and MCP-based external tool access. These capabilities make Gemini useful as a research/recon and tool-using participant while leaving application-side tool execution under the integrating system.
- MCP's 2026-07-28 revision is stateless over Streamable HTTP and requires per-request authentication/authorization because the protocol no longer relies on protocol sessions.
- A2A is the complementary agent-to-agent interoperability layer. SAGE should evaluate A2A after the MCP bridge proves the smaller Google/Gemini connection; MCP connects an AI host to tools/context, while A2A connects independent agents.

## SAGE boundary

```text
Google AI / Gemini
        |
        | MCP / structured intelligence
        v
SAGE Google-Gemini Bridge
        |
        +--> bounded context read
        +--> governed knowledge search
        +--> research candidate intake
        |
        v
SAGE candidate knowledge
        |
        v
Validation / Evidence Binding / DecisionRecord
        |
        v
Master Archive / canonical state
```

Google/Gemini MUST NOT directly:

- promote knowledge to canonical state;
- grant authority;
- mutate XP, qualification, mission, or progression;
- execute arbitrary runtime operations;
- create a second persistence authority;
- submit private chain-of-thought as evidence.

## MCP surface v0.1

### `sage_context`

Read bounded SAGE context: identity, objective, active task, blockers, health counts, and governance posture.

### `sage_search`

Read SAGE memory by exact tag or object type. Search is bounded and does not authorize action.

### `sage_submit_research_candidate`

Write boundary for external intelligence. Every submission is explicitly:

- `confidence = hypothesis`
- `promotion_status = CANDIDATE`
- `authority_granted = false`
- provenance-bearing (`source`, submitter, timestamp, context ID)
- digest-bound for replay/traceability

The submission cannot validate or promote itself.

### `sage_capability_surface`

Read the currently exposed SAGE capability surface without changing capability state.

## Authentication

Production Render already has `SAGE_REQUIRE_AUTH=true` and a generated `SAGE_API_KEYS` value. The bridge deliberately reuses the canonical SAGE API authentication boundary rather than introducing a second independent authority secret.

A dedicated `SAGE_GOOGLE_MCP_API_KEY` may be configured later if deployment topology requires it. It is not required by this v0.1 implementation when the canonical SAGE middleware is active.

## Gemini Apps connection

When the deployed SAGE runtime is available at `https://<sage-host>`, the MCP endpoint is:

`https://<sage-host>/mcp`

Gemini Spark's Custom Connected Apps flow accepts an MCP server URL. The connected app should be granted only the minimum access needed and should be supervised. SAGE's own authorization boundary remains authoritative even if Gemini presents a tool call as user-approved.

## Inventor-stage learning loop

The Google/Gemini bridge is not the endpoint. It creates a reusable external-learning channel:

1. **SENSE** — Gemini/Search/Deep Research observes external reality.
2. **RECON** — Google/Gemini submits sources, comparisons, standards, and candidate findings.
3. **BOUND** — SAGE records provenance and keeps findings in candidate state.
4. **FALSIFY** — SAGE adversarially checks claims against repository truth and independent evidence.
5. **DECIDE** — DecisionRecord/evidence evaluation determines whether a capability candidate is supportable.
6. **AUTHORIZE** — Director remains the consequential authority.
7. **BUILD** — validated capability is implemented through the engineering lane.
8. **VERIFY** — receipts, witness binding, and regression evidence verify the result.
9. **COMPOUND** — validated knowledge becomes reusable SAGE state and improves the next research cycle.

## Next expansion targets

1. Add a real Gemini API client using the stable Google API boundary rather than the legacy placeholder `GeminiJulesClient` behavior.
2. Add structured research-task envelopes so Gemini can request a SAGE research objective and receive a deterministic response contract.
3. Add citation/provenance capture for Google Search/Deep Research outputs.
4. Evaluate A2A Agent Card + task lifecycle as a second interoperability surface after MCP proves stable.
5. Add independent cross-model challenge flows: Gemini challenges SAGE, SAGE challenges Gemini-derived claims, and neither becomes canonical merely by agreement.

## Stop boundary

v0.1 stops at the governed MCP bridge. Do not add automatic promotion, arbitrary execution tools, transport proliferation, A2A, or new persistence until the MCP flight is deployed and independently verified.
