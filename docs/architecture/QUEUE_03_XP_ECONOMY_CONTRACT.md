# Queue #03 — XP Economy Contract

**Status:** LOCKED — conversion v0.2
**Queue:** 03 — XP Economy
**Branch:** `c2/xp-economy-step-03-reconciled`

## Core rule

SAGE career XP is a deterministic progression currency derived from verified Points.

**Locked conversion:**

`100 verified Points = 10 career XP`

Therefore:

`1 verified Point = 0.1 career XP`

`XP_awarded = verified_points × 0.1`

`XP_lifetime = Σ verified_XP_awards`

There is no random roll, casino-style variance, streak multiplier, or hidden modifier in the career-XP conversion.

## Precision

Conversion uses exact decimal arithmetic. Fractional XP is preserved and must never be silently rounded.

## Accounting contract

Every conversion receipt is represented by an auditable event containing:

- `event_id` — source event / mission / evidence identity;
- `agent_id` — agent receiving individual attribution;
- `verified_points` — authoritative Point amount from the verified event;
- `xp_awarded` — deterministic conversion result.

Lifetime XP is the sum of verified XP awards. XP is not created merely because time elapsed, a message was sent, or a task was claimed.

## Validity

- Point input is an integer.
- Negative Points are rejected.
- Boolean values are rejected as invalid Point inputs.
- Missing event or agent identity is rejected at event construction.
- Fractional results such as `25 Points = 2.5 XP` are preserved exactly in conversion receipts.
- The existing canonical `GameProgression` ledger currently accepts whole-XP awards; its adapter rejects fractional awards rather than silently rounding them. Extending canonical persistence to fractional XP is an explicit integration concern and is not silently changed by Queue #03.

## Worked examples

| Verified Points | Career XP |
|---:|---:|
| 1 | 0.1 |
| 5 | 0.5 |
| 10 | 1 |
| 25 | 2.5 |
| 50 | 5 |
| 100 | 10 |
| 250 | 25 |
| 500 | 50 |

These examples align with the Point denominations reserved for Queue #04.

## Progression relationship

Queue #02 remains authoritative for rank semantics:

`REAL WORK → VERIFIED EVIDENCE → CAREER SIGNALS → READINESS ASSESSMENT → PROMOTION PROPOSAL → DIRECTOR DECISION → RANK`

XP is one career signal inside that chain. **XP alone never equals rank.**

## Rank-up continuity

When rank changes:

- lifetime XP is retained;
- visible Boss kill/capture board tallies reset as a new rank cycle begins;
- Boss kill/capture history remains durable;
- badges remain durable.

## Economy boundary

Queue #03 owns the Point→XP conversion and XP accounting primitives.

Queue #04 owns the exact Point-award economy. Queue #09 owns promotion/rank thresholds and eligibility. Queue #11 owns anti-farming/replay protection. Queue #12 owns invalidation/demotion propagation.

Those queues may constrain how XP events are admitted, but they do not alter this conversion rule without an explicit contract change.

## Design guardrails

1. **Deterministic:** identical verified inputs produce identical XP.
2. **Attributable:** every award has event and agent lineage.
3. **Exact:** fractional XP is preserved; no silent rounding.
4. **No randomness:** career XP is not a variable-ratio reward mechanism.
5. **No time farming:** elapsed time is not an XP source.
6. **No hidden multipliers:** modifiers must not exist outside this contract.
7. **Auditable:** lifetime totals are reconstructible from verified events.
8. **Stable:** historical awards do not change because a later curve is tuned.
9. **Separable:** optional game-like reward presentation cannot corrupt the career ledger.

## Verification

The implementation at `sage/experimental/airspace/xp_economy.py` provides deterministic decimal conversion, event lineage, validation, lifetime accumulation, and a guarded adapter into canonical progression. Regression coverage is in `tests/experimental/test_xp_economy.py`.

**Queue #03 conversion v0.2 is locked.**
