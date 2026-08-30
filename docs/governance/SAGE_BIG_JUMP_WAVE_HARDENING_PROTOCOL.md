# SAGE Big Jump Wave Hardening Protocol

**Directive ID:** `SAGE_BIG_JUMP_WAVE_HARDENING_PROTOCOL`
**Status:** Active governed protocol
**Authority:** Subordinate to SAGE Constitution, Master Archive, canonical runtime/state, and validated repository truth.

## Purpose

Turn each Big Jump Wave into a capability-hardening cycle rather than a feature burst. Every wave must reduce a known failure class, expose a reusable enforcement boundary, or materially increase verified capability.

## Wave doctrine

`REPO TRUTH → HISTORICAL RECON → EXTERNAL FALSIFICATION → ATTACK SURFACE MAP → SMALLEST HIGH-LEVERAGE CHANGE → ADVERSARIAL TEST → FULL VERIFY → EXACT-SHA RECONCILIATION → PERMANENT LEARNING → NEXT ATTACK SURFACE`

The wave is not complete because an implementation exists. It is complete only when the new invariant is enforced, tested, evidenced, and reusable.

## Marine-style execution discipline

Use the five-flight structure as a bounded operating pattern, not as theater:

- **F1 — Recon / Architecture Guard:** establish exact repository truth, ownership, dependencies, prior failures, and blast radius.
- **F2 — Intelligence / Falsification:** use Super Search and external sources to challenge assumptions and locate stronger patterns or known failure modes.
- **F3 — Build / Repair:** implement the smallest change in the existing canonical architecture; no parallel authority.
- **F4 — Verification / Red Team:** attack the boundary, including stale, missing, malformed, adversarial, replayed, unauthorized, and bypass paths; then run the full suite.
- **F5 — Evidence / Compound:** bind results to exact SHA, persist receipts and learning, update the repair history, and identify the next frontier.

Flights may run in parallel only when their ownership boundaries do not collide. Shared canonical files and state transitions require explicit sequencing.

## Runtime governance lessons incorporated

External research is used as falsification input, not authority. Recent runtime-governance work reinforces several controls already aligned with SAGE:

1. **Model proposes; trusted runtime decides.** Prompt instructions are not an execution boundary. See current runtime-governance research on action-boundary control and policies-on-paths.
2. **Authorization must be bound to current state.** A previously valid authorization can become stale before an effect occurs; dispatch-time revalidation is therefore a critical control. See current research on stateful governance and state-aware long-horizon agents.
3. **Evidence must prove authority and outcome, not merely log activity.** Authority receipts, provenance, policy context, and observable outcomes make a governance decision reconstructable. See current work on authority receipts and auditable autonomy.
4. **Single enforcement points are risky.** Independent or layered checks are needed because configured controls can silently fail. See current 2026 agent-governance field surveys.
5. **Graduated autonomy is preferable to binary trust.** Expanded authority should be earned through sustained verified reliability and contractually bounded state, with degradation when reliability falls. See current AWS guidance on graduated autonomy.

These findings do not authorize importing another framework. They strengthen the SAGE requirement to make existing governance boundaries enforceable, state-aware, provenance-bound, and observable.

## Mandatory invariants

### 1. State authority

Canonical state has one owner. Projections, model output, receipts, and external research cannot become canonical merely by existing.

### 2. Action authority

No consequential transition executes without an independently valid authorization bound to the current canonical state, actor identity, requested operation, scope, and provenance.

### 3. Freshness

Authorization and state-dependent decisions must be revalidated at the point where the governed effect occurs. Stale approvals fail closed.

### 4. Provenance

Every promoted or consequential state must be traceable to the evidence, validation, authorization, and exact source state that justified it.

### 5. Fail closed

Missing, malformed, ambiguous, stale, conflicting, or unverifiable governance inputs produce HOLD/REJECT—not inferred success.

### 6. Negative evidence

Failed experiments, rejected hypotheses, blocked transitions, and near misses remain durable learning inputs.

### 7. Presentation isolation

Immersion, HUDs, badges, stars, nameplates, and other projections may expose canonical state but cannot create or authorize it.

### 8. Model non-authority

Models and agents can propose, reason, research, or request actions. They cannot self-authorize canonical transitions or promotion.

### 9. Layered enforcement

Critical invariants should have more than one detection/protection point where practical: admission, runtime boundary, post-action reconciliation, and evidence verification.

### 10. Recovery truth

Rehydration must reconstruct from durable canonical state and evidence, not from chat history or model memory. Recovery must preserve provenance and reject contradictory state.

## Required adversarial matrix

Every consequential hardening wave should attempt at least:

- missing state;
- stale state;
- tampered digest;
- wrong identity/station;
- unauthorized transition;
- valid authorization against obsolete state;
- replayed authorization/receipt;
- malformed evidence;
- missing provenance;
- model-generated self-authorization;
- presentation-generated progression;
- swallowed exception / silent failure;
- partial write or interrupted reconciliation;
- duplicate execution / idempotency failure;
- conflicting concurrent state;
- recovery from persisted state;
- bypass through an alternate adapter or integration path.

The matrix is a minimum. A wave must add domain-specific attacks discovered during recon.

## Permanent repair learning

Every consequential repair must leave a durable record containing:

`FAILURE → ROOT CAUSE → AFFECTED BOUNDARY → REPAIR → TESTS → ADVERSARIAL RESULT → EXACT SHA → EVIDENCE → INVARIANT → REUSABLE PATTERN → REMAINING GAP → NEXT ATTACK`

Use `docs/governance/C2_PERMANENT_REPAIR_LOG.md` for repair history and the appropriate evidence-capture surfaces for machine-verifiable receipts.

## Promotion gate

A Big Jump Wave is **HOLD** unless all applicable gates are satisfied:

- repository truth reconciled;
- historical failures consulted;
- external falsification performed when useful;
- implementation landed in the canonical architecture;
- adversarial tests pass;
- full platform verification passes;
- exact head SHA reconciled;
- evidence is durable and traceable;
- remaining limitations are explicit;
- no new authority duplication was introduced.

## Success condition

The system should become harder to break in the same way twice.

> **Every wave must leave SAGE more capable, more governable, more observable, and harder to regress than the wave before it.**
