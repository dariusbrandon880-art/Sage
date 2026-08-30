# SAGE C2 SEP/1 Provider-Neutral Protocol Foundation

**Status:** Candidate specification / implementation boundary
**Authority:** SAGE C2 governance; Git/main is implementation truth
**Issue:** #333

## Purpose

SEP/1 defines the minimum evidence contract between SAGE C2 and an external execution substrate. The substrate may be Jules, GitHub Actions, GitLab CI, a local runner, or another implementation. The substrate executes; C2 verifies and governs promotion.

This document is deliberately a protocol foundation, not a claim of provider neutrality. Provider neutrality is proven only when at least two independent execution substrates produce equivalent, independently verifiable SEP/1 semantics.

## Authority boundary

`execution substrate != verification authority != promotion authority`

Provider status, workflow success, agent assertions, and transport metadata are evidence inputs. None can independently authorize SAGE promotion.

## State machine

The canonical transition chain is:

`DECLARED -> CONFIGURED -> EXECUTING -> EXECUTED -> EVIDENCE_CAPTURED -> VERIFIED -> VALIDATED -> ACCEPTED -> PROMOTED`

Terminal/non-promoting states:

- `FAILED` — execution or verification failed.
- `REJECTED` — evidence/provenance violates a required invariant.
- `HOLD` — required evidence or authorization is absent/indeterminate.
- `SUPERSEDED` — evidence is stale because a newer valid execution exists.
- `INVALIDATED` — artifact identity, commit binding, or provenance changed.

Illegal shortcuts include `CONFIGURED -> PROMOTED`, `EXECUTED -> PROMOTED`, and `PASS -> PROMOTED`.

## SEP/1 evidence packet

Every packet MUST carry:

- `protocol`: `SAGE-SEP/1`
- `protocol_version`
- `mission_id`
- `execution_id`
- `session_id` when applicable
- `provider_id` and `provider_version` when known
- `execution_started_at`
- `execution_finished_at`
- `repository`
- `base_ref`
- `target_sha` — exact intended repository SHA
- `observed_sha` — exact SHA actually executed
- `artifact_manifest` with stable paths and content digests
- `test_manifest` with commands, results, and timestamps
- `provenance` identifying actor, substrate, and lineage
- `result` — execution result only; not promotion authority
- `evidence_digest`
- `schema_digest`

The packet MUST be rejected if `target_sha != observed_sha`, required provenance is absent, a referenced artifact digest does not match, or the evidence is otherwise unverifiable.

## Verification rules

C2 verification MUST independently establish:

1. exact-head identity;
2. artifact integrity;
3. provenance continuity;
4. test/evidence completeness for the declared mission;
5. freshness relative to the target SHA;
6. required human/operator authorization;
7. absence of contradictory or superseding evidence.

A provider-reported green state may satisfy one evidence input but cannot satisfy the full verification boundary by itself.

## Provider handshake

A provider adapter exposes only transport/execution facts:

`DECLARE -> ACCEPT -> EXECUTE -> EMIT_EVIDENCE -> ACK`

The adapter MUST NOT expose a provider-specific promotion primitive as authoritative C2 state. Provider-specific statuses are mapped into SEP/1 evidence fields and reconciled by C2.

## Promotion receipt

Promotion requires a C2-generated receipt containing:

- exact verified target SHA;
- verification result and verifier identity;
- evidence digest(s);
- validation decision;
- explicit acceptance authorization when required;
- promotion timestamp;
- resulting repository reference;
- supersession/invalidation relationships where applicable.

A provider cannot generate a valid SAGE promotion receipt merely by reporting success.

## Master Archive event model

The durable event sequence is append-only:

`DECLARATION | EXECUTION | EVIDENCE | VERIFICATION | VALIDATION | ACCEPTANCE | PROMOTION | FAILURE | REJECTION | HOLD | SUPERSESSION | INVALIDATION`

Events MUST be immutable once recorded. Rehydration derives current state by deterministic reduction of valid events; chat history and provider dashboards are not canonical state.

## Fail-closed rules

- Missing evidence => `HOLD`.
- Invalid provenance => `REJECTED`.
- Artifact identity change => `INVALIDATED`.
- Failed verification => `FAILED`.
- Stale evidence => `SUPERSEDED`.
- Missing required acceptance => `HOLD`.
- Unknown/indeterminate status never upgrades state.

## Implementation boundary

This foundation intentionally does not implement provider adapters or claim multi-provider equivalence. The next implementation slices are:

1. typed SEP/1 packet model + validation;
2. C2 verification reducer;
3. immutable promotion receipt;
4. append-only archive event/reduction tests;
5. GitHub reference adapter;
6. second independent execution adapter;
7. cross-provider equivalence evaluation.

Each slice must remain independently testable and must reuse existing SAGE provenance, evidence, persistence, and governance primitives rather than introducing a parallel authority system.
