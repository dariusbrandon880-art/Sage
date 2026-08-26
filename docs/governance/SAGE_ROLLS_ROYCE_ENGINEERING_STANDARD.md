# SAGE Rolls-Royce Engineering Standard

**Status:** Canonical engineering quality standard  
**Scope:** C2, engineering, governance, research-to-build transitions, verification, and repository integration

## Purpose

SAGE adopts a **Rolls-Royce engineering standard** as an internal quality metaphor: every component is accounted for, every tolerance is intentional, every transition is controlled, and every completion claim is proven.

This is an engineering and governance standard, not a branding or vendor dependency.

## Core Standard

SAGE work must be:

1. **Complete** — the requested capability is actually carried through execution, verification, and integration rather than stopping at planning or review readiness.
2. **Precise** — changes are surgical, bounded, and causally related to the mission; unnecessary churn is avoided.
3. **Traceable** — implementation, evidence, commits, tests, workflow runs, and integration state can be traced to exact repository state.
4. **Durable** — validated lessons become architecture or governance where appropriate so the same failure mode is not repeatedly rediscovered.
5. **Cleanly integrated** — stale work is reconstructed against current `main` when necessary; historical work is never discarded merely because its PR was closed.
6. **Fail-closed** — missing authorization, unavailable verification, contradictory evidence, or unexecuted work must never be represented as success.
7. **Adversarially verified** — C2 actively searches for missed failures, stale evidence, duplicate capability, regressions, and incomplete integration.
8. **Velocity-preserving** — independent work is executed concurrently through bounded Big Jump Waves when safe, without weakening verification.

## Historical Capability Preservation

A closed, superseded, or stale PR is **not** evidence that its implementation was preserved.

Before retiring a historical frontier, classify its capability payload as exactly one of:

- **Integrated** — capability is present in current `main`.
- **Superseded** — equivalent or stronger implementation is present in current `main`, with evidence of equivalence.
- **Research-only** — intentionally not promoted to implementation, with rationale recorded.
- **Recovered** — missing capability was reconstructed into a current-main-compatible frontier.
- **Duplicate** — capability is demonstrably redundant and may be retired.

Historical capability that cannot be classified must remain an active reconciliation item.

## Execution Quality Gate

For consequential work, C2 should drive the following loop:

```text
DIRECTIVE
  -> PREFLIGHT / REALITY LOCK
  -> SUPER SEARCH / RECONNAISSANCE
  -> BOUNDED BIG JUMP WAVE
  -> EXECUTE
  -> TEST
  -> EVIDENCE
  -> VERIFY
  -> RECONCILE
  -> INTEGRATE
  -> POST-INTEGRATION VERIFY
```

Super Search is a reconnaissance sensor, not canonical authority. Git/repository truth, live execution results, and validated Master Archive state remain authoritative.

## Evidence Discipline

The following distinctions are mandatory:

- configured != executed
- queued != successful
- green historical run != green current HEAD
- PR closed != capability preserved
- ready for review != merged
- merged != post-merge verified
- documented requirement != enforced control

C2 must report the strongest claim actually supported by live evidence and no stronger.

## Rolls-Royce Completion Criterion

A mission is complete only when the requested capability is:

- implemented or explicitly dispositioned;
- tested at the relevant scope;
- independently verified against the resulting exact repository state;
- integrated at the requested boundary;
- checked for regressions and historical capability loss;
- and left in a clean, reproducible state.

If any of these gates is unresolved, the mission remains open.

## Relationship to Other Governance

This standard complements, and does not replace:

- `CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md`
- `PR_QUEUE_FRONTIER_POLICY.md`
- `SAGE_C2_FRONTIER_ADMISSION_AND_RECONCILIATION_RULE.md`
- `SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md`

The anti-drift contract defines behavioral authority; the PR Queue policy defines bounded frontier management; the Frontier Admission rule defines reconciliation; the Big Jump Wave doctrine defines concurrent execution; this standard defines the required **quality and completion bar** across those mechanisms.
