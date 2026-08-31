# SAGE Governed ChatGPT Activation

## Purpose

This integration provides a **real, explicit activation boundary** for a supported ChatGPT client. It does not claim that the native ChatGPT website is automatically intercepted or governed.

## Truth states

### CONNECTED_AND_GOVERNED

A client is in this state only when all of the following are true:

1. The client is configured to call the deployed SAGE runtime endpoint.
2. The request reaches `POST /ai/query/chatgpt`.
3. SAGE authentication succeeds when authentication is enabled.
4. `ChatGPTClient` constructs the governed runtime and invokes `SAGEChatGPTBoundary`.
5. `SAGEProtocolGovernor` validates the model result and station identity.
6. The governed response is rendered and returned by SAGE.

### UNBRIDGED_HOST_SESSION

A native/browser ChatGPT conversation is in this state unless it is explicitly routed through the deployed SAGE boundary. A model response in this state must not be treated as proof of SAGE authority, authorization, repository mutation, or live SAGE execution.

## Activation mechanism

The repository already exposes the governed ChatGPT API path. The companion OpenAPI document, `chatgpt-governed-action.openapi.yaml`, is the client configuration contract for a supported ChatGPT Action/custom-client integration.

Deployment steps:

1. Deploy the SAGE API on a reachable HTTPS origin.
2. Set authentication according to the deployment policy; for exposed deployments, enable `SAGE_REQUIRE_AUTH=true` and configure the API key through the deployment secret mechanism.
3. Replace the placeholder server URL in the OpenAPI document with the deployed SAGE origin.
4. Configure the supported ChatGPT Action/custom client to import that OpenAPI document.
5. Exercise `executeGovernedChatGPTQuery` and inspect the returned governed response and runtime evidence.
6. Treat any conversation that does not use this route as `UNBRIDGED_HOST_SESSION`.

## Non-goals

This integration does **not**:

- inject system instructions into arbitrary ChatGPT web sessions;
- intercept OpenAI browser traffic;
- claim that this repository can force the ChatGPT consumer website to use SAGE;
- manufacture a governance receipt from an unbridged conversation.

The boundary is intentionally explicit: **routing creates governance; conversation text does not.**
