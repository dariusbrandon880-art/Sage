# SAGE Session Rehydration Contract

## Purpose

A fresh ChatGPT/Jules/Gemini session must not depend on conversational memory to recover active SAGE state. The repository and persisted evidence are authoritative.

## Deterministic bootstrap order

1. Resolve repository `HEAD` and require a valid 40-character SHA.
2. Load the active SAGE session manifest.
3. Verify the manifest is bound to the resolved SHA.
4. Load active mission/PR/flight state from the manifest and live repository state.
5. Load persisted acceptance/evidence references.
6. Load identity/nameplate/immersion contract state.
7. Fail closed when any required state is missing, malformed, or SHA-drifted.

## Authority boundary

- Repository state is authoritative for implementation and governance.
- Evidence artifacts are authoritative for observed runtime behavior.
- Conversational memory is contextual only; it cannot promote or repair repository state.
- Identity and immersion are projections of canonical state, not independent sources of truth.

## Acceptance boundary

A capability is `ACCEPTED` only when the deterministic gate passes and every required interface has a persisted PASS observation with evidence. Partial observation remains `PENDING`.

## Fresh-session guarantee

The bootstrap must make the following facts mechanically recoverable in a new chat window or on a new PR:

- canonical SHA
- active mission/goals
- active flights and PRs
- required interfaces and per-interface verdicts/evidence
- open operational defects
- SAGE identity/nameplate contract status
- current acceptance status

This contract is intentionally independent of model personality or prompt wording.
