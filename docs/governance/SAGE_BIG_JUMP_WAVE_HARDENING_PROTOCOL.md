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

Use the five-flight structure as a governed operating pattern, not as theater. “Marine-style” means decisive execution against the actual failure surface, disciplined sequencing, explicit objectives, independent verification, and no premature victory declaration.

**F1, F2, F3, F4, and F5 are open reusable execution slots.** No flight has a permanent function.

For the current wave, C2 assigns each slot a distinct mission and boundary. Any slot may perform recon, research, build, repair, testing, governance/security work, architecture work, evidence work, integration, or another authorized mission. The assignments can be completely different on the next wave.

Flights may run in parallel only when their current mission boundaries do not collide. Shared canonical files and state transitions require explicit sequencing or governed collision admission.

## Repair-as-learning doctrine

A consequential repair is itself a reusable capability. SAGE must learn the **repair method**, not only retain the repaired code.

For every consequential failure, C2 must extract and persist:

`FAILURE → SIGNAL → ROOT CAUSE → ATTACK VECTOR → DECISIVE REPAIR → PROOF QUALITY → REGRESSION → EVIDENCE → INVARIANT → REUSABLE REPAIR PATTERN → NEXT ATTACK`

The reusable pattern must describe **how the system should reason and act the next time the failure class appears**. Examples include:

- inspect live repository truth before trusting a completion report;
- consult prior repair history before designing a new fix;
- attack the proof itself for vacuous or non-binding assertions;
- repair the canonical enforcement boundary instead of patching a downstream symptom;
- verify precondition → attempted violation → rejection → unchanged postcondition;
- reconcile implementation, evidence, and exact SHA before promotion;
- preserve the failure as negative evidence when the attack is rejected;
- convert every newly discovered seam into the next bounded attack surface.

A future C2 session should be able to reuse these patterns without reconstructing them from chat history.

### Autonomous repair-learning loop

When a consequential repair completes, the runtime/process should treat the resulting record as candidate repair intelligence and route it through the existing validation/archive pathway. It must not silently rewrite canonical state or authorize itself. Learning is durable only after evidence and validation requirements are satisfied.

`OBSERVE → RETRIEVE PRIOR REPAIRS → FORM REPAIR HYPOTHESIS → ATTACK → REPAIR → VERIFY → EXTRACT PATTERN → VALIDATE LEARNING → ARCHIVE → REUSE`

This is a pathway guide: existing canonical ledgers, evidence stores, validators, and archives remain authoritative.

## Runtime governance lessons incorporated

External research is used as falsification input, not authority. Recent runtime-governance work reinforces several controls already aligned with SAGE:

1. **Model proposes; trusted runtime decides.** Prompt instructions are not an execution boundary.
2. **Authorization must be bound to current state.** A previously valid authorization can become stale before an effect occurs; dispatch-time revalidation is therefore a critical control.
3. **Evidence must prove authority and outcome, not merely log activity.** Authority receipts, provenance, policy context, and observable outcomes make a governance decision reconstructable.
4. **Single enforcement points are risky.** Independent or layered checks are needed because configured controls can silently fail.
5. **Graduated autonomy is preferable to binary trust.** Expanded authority should be earned through sustained verified reliability and bounded state, with degradation when reliability falls.

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

### 11. Repair-learning integrity

Repair intelligence is derived from verified failures and repairs. It cannot be promoted from narrative claims, a green test without proof-quality review, or model-generated self-attestation.

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
- bypass through an alternate adapter or integration path;
- vacuous security assertions that can pass without establishing the protected precondition or postcondition;
- repair-learning records that claim a lesson without linking failure, repair, regression, and evidence.

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
- repair learning is recorded with proof-quality evidence;
- remaining limitations are explicit;
- no new authority duplication was introduced.

## Success condition

The system should become harder to break in the same way twice.

> **Every wave must leave SAGE more capable, more governable, more observable, and harder to regress than the wave before it—and every consequential repair must improve the system's future ability to perform the next repair.**
