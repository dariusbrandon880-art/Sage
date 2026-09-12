# AIET External Harness Launch Readiness

The external harness requires real provider execution and a real out-of-band disruption service.

Required environment:

- `SAGE_AIET_EXTERNAL_HARNESS_KEY`
- `SAGE_AIET_TARGET_GIT_SHA`
- One provider credential/endpoint: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `LOCAL_LLM_URL`, or `CUSTOM_LLM_URL`
- `SAGE_AIET_DISRUPTION_URL`

The deployment example `docker-compose.aiet_external.yml` provisions the disruption sidecar separately from the harness process. The harness records the observed 503/network failure and then performs a real provider recovery request.

Receipts are SHA-256 hash-bound, bind the explicit target Git SHA, reject fixture execution, and require zero human intervention. Hash-bound evidence is not a digital signature.
