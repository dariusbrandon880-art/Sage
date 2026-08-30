# SAGE Unified Agent Control Plane

**Status:** Architecture guide for the governed agent/runtime boundary
**Authority:** Canonical SAGE implementation, tests, and validated evidence
**External research:** threat-model input only; never canonical authority

## Purpose

SAGE governs every model/agent station through one runtime control plane. Agent role is not authority. A station may propose work or supply evidence, but only the governed SAGE runtime can reconcile identity, canonical state, policy context, provenance, authorization, and effect.

## Canonical path

```text
AGENT
  ↓
IDENTITY / STATION
  ↓
CANONICAL STATE SNAPSHOT
  ↓
PINNED POLICY CONTEXT
  ↓
PROVENANCE CONTEXT
  ↓
MODEL / AGENT ADAPTER
  ↓
PROTOCOL GOVERNOR
  ↓
PROPOSAL / EVIDENCE
  ↓
RUNTIME RECONCILIATION
  ↓
ACTION-BOUND AUTHORIZATION
  ↓
STATE-MUTATING BOUNDARY
  ↓
EVIDENCE / VALIDATION
  ↓
PROMOTION
  ↓
IMMERSION PROJECTION
```

No station receives a side door because it is C2, ChatGPT, Jules, Gemini, or a future agent.

## Runtime binding invariant

A governed model response is acceptable only when it reconciles to the same:

- station identity
- canonical state digest
- policy version
- policy-context digest
- provenance digest
- mission/session/instance identity

The model does not author any of these values.

## Policy pinning

The runtime envelope is immutable for the lifetime of an invocation. Policy context is represented by a deterministic digest bound to station, model role, and policy version. Reconciliation rejects a response carrying a different policy version or digest.

This follows the general security lesson that an in-flight session must enforce the policy snapshot it was created under rather than rereading mutable ambient policy state.

## Provenance binding

Provenance is derived from the complete canonical reference sets supplied by SAGE: evidence, known state, candidate state, and negative-memory references. A response carrying a different provenance digest is rejected before authority use.

## Cross-agent rule

> **No safe agent is exempt from the governance protocol because of role, model, trust level, or origin.**

C2 can command. Jules can implement. Gemini can research. ChatGPT can operate the governed interface. None can self-authorize a canonical transition.

## Evidence discipline

Green tests, PASS receipts, or model claims do not become authority by themselves. Promotion remains a separate canonical transition protected by the state-mutating boundary and action-bound authorization.

## External threat-model inputs

NIST's 2026 agent identity/authorization work highlights explicit identification, authorization, auditing, non-repudiation, and prompt-injection controls for agent systems. Current Microsoft agent-governance work independently emphasizes pinned session policy, fail-closed evaluation, complete snapshots, and action-bound execution-time revalidation.

These sources are useful falsification targets, not SAGE authority. Live repository truth and validated evidence remain canonical.

## Next attack surfaces

1. Audit every direct CLI/tool/runtime entry point for a path around `SAGERuntime`.
2. Remove or gate legacy ChatGPT paths that can invoke a provider without `render_governed_chatgpt_turn`.
3. Extend provenance and identity binding into every state-mutating authorization artifact.
4. Stress concurrent authorization consumption and alternate promotion/evolution routes.
5. Attack the tests themselves for vacuous assertions and unproved preconditions.

## Repair pattern

```text
RECON
→ ROOT CAUSE
→ ATTACK
→ REPAIR
→ REGRESSION
→ FULL VERIFY
→ EXACT-SHA RECONCILIATION
→ PERMANENT LOG
→ COMPOUND
```

Every discovered seam becomes a regression and a reusable repair lesson.