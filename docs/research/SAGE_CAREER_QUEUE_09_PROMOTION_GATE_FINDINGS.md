# Queue #09 — Career Promotion Gate Findings

**Status:** RESEARCH / CONTRACT LOCK — IMPLEMENTATION HOLD
**Base:** `main` after PR #417 merge

## Mission

Define the governed promotion decision boundary without creating a second career-state authority or allowing XP alone to mutate rank.

## Locked promotion model

Promotion is a **decision gate**, not an automatic consequence of XP accumulation.

```text
Verified work
  -> canonical evidence
  -> verified Points
  -> Career XP
  -> qualification + promotion evidence
  -> promotion gate
  -> PROMOTE or HOLD
  -> persistent rank state only after authorized promotion
```

## Gate requirements

A candidate promotion MUST satisfy all currently established prerequisites:

1. **Sequential progression** — only the immediate next rank may be considered; rank skipping is rejected.
2. **Lifetime Career XP** — XP is durable and is retained across rank changes.
3. **Qualification evidence** — required qualification state must come from the canonical qualification authority.
4. **Promotion evidence** — the gate must have attributable, canonical evidence supporting demonstrated capability/work evolution.
5. **Governance decision** — the gate returns an explicit `PROMOTE` or `HOLD` result; eligibility is not itself a rank mutation.
6. **Canonical persistence** — an approved promotion may update the existing canonical rank state only through the governed persistence boundary.
7. **Fail closed** — missing, invalid, stale, replayed, or non-canonical evidence cannot produce promotion.

## Explicit non-requirements

- XP alone never promotes an agent.
- Points do not directly set rank.
- Boss kills/captures do not directly set rank.
- Badges do not directly set rank.
- Career identity/specialization is not replaced by rank.
- C2 remains a control function, not a career rank.
- Five Flights remain adaptive reusable execution slots; no permanent flight assignment is introduced.
- Immersion/HUD remains downstream of canonical career state.
- No second career store or parallel rank authority is introduced.

## Threshold boundary

**Exact XP thresholds and any additional numeric promotion dimensions are NOT invented or locked by this contract.** They require the dedicated threshold/economy decision and validation evidence before implementation can make them authoritative.

The existing `10 verified Points = 1 Career XP` economy remains separate from promotion thresholds.

## Legacy-path boundary

The historical `FleetQualificationLedger` is not a promotion authority. Its direct raw-XP mutation path is disabled. Historical snapshot recovery must not infer new rank or qualification from raw XP.

## Implementation hold

Do not add automatic promotion, hard-coded guessed thresholds, a second rank store, or a parallel promotion engine until the numeric threshold contract is explicitly validated.

## Queue exit criteria

Queue #09 becomes implementation-ready only when:

- promotion inputs and decision states are represented against canonical state;
- exact threshold values are explicitly locked by the governing research/decision record;
- negative cases prove XP-only, missing-evidence, non-qualified, skipped-rank, and replay/stale evidence attempts resolve to `HOLD`/rejection;
- persistent rank mutation remains behind the authorized promotion boundary;
- exact-head CI verifies the implementation.
