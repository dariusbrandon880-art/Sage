# Queue #03 — XP Economy Contract

**Status:** LOCKED — conversion v0.1
**Queue:** 03 — XP Economy
**Branch:** `c2/xp-economy-step-03`

## Core rule

SAGE career XP is a **deterministic progression currency derived from verified Points**.

**Locked conversion:**

`1 verified Point = 10 career XP`

Therefore:

`XP_awarded = verified_points × 10`

`XP_lifetime = Σ verified_XP_awards`

There is no random roll, casino-style variance, streak multiplier, or hidden modifier in the career-XP conversion.

## Why this model

Game-economy research consistently recommends modeling progression quantitatively, balancing reward velocity against progression pacing, and simulating player/work profiles rather than tuning from intuition alone. citeturn0search2turn0search40

Casino mechanics provide a useful lesson about **reward anticipation and variance**, but that lesson is intentionally bounded here: variable reinforcement can enrich optional presentation or reward loops, while a career ledger must remain deterministic, inspectable, and fair. A verified event must produce the same career XP every time it carries the same verified Point value.

This separation prevents a gambling-like randomizer from contaminating SAGE's professional progression record.

## Accounting contract

Every XP award is represented by an auditable event containing:

- `event_id` — source event / mission / evidence identity;
- `agent_id` — agent receiving individual attribution;
- `verified_points` — authoritative Point amount from the verified event;
- `xp_awarded` — deterministic conversion result.

Lifetime XP is the sum of verified XP awards. XP is not created merely because time elapsed, a message was sent, or a task was claimed.

## Precision and validity

- Point input is an integer.
- Negative Points are rejected.
- Boolean values are rejected as invalid Point inputs.
- Conversion is exact integer arithmetic at the locked 10:1 ratio.
- No rounding policy is needed while the locked ratio is integral.
- Missing event or agent identity is rejected at event construction.

## Worked examples

| Verified Points | Career XP |
|---:|---:|
| 1 | 10 |
| 5 | 50 |
| 10 | 100 |
| 25 | 250 |
| 50 | 500 |
| 100 | 1,000 |
| 250 | 2,500 |
| 500 | 5,000 |

These examples intentionally align with the Point denominations reserved for Queue #04.

## Progression relationship

Queue #02 remains authoritative for rank semantics:

`REAL WORK → VERIFIED EVIDENCE → CAREER SIGNALS → READINESS ASSESSMENT → PROMOTION PROPOSAL → DIRECTOR DECISION → RANK`

XP is one career signal inside that chain. **XP alone never equals rank.**

## Rank-up continuity

When rank changes:

- lifetime XP is retained;
- XP does not reset with the visible Boss kill/capture board cycle;
- Boss kill/capture history remains separately durable;
- badges remain durable.

## Economy boundary

Queue #03 owns the Point→XP conversion and XP accounting primitives.

Queue #04 owns the exact Point-award economy. Queue #09 owns promotion/rank thresholds and eligibility. Queue #11 owns anti-farming/replay protection. Queue #12 owns invalidation/demotion propagation.

Those queues may constrain how XP events are admitted, but they do not alter this conversion rule without an explicit contract change.

## Design guardrails

1. **Deterministic:** identical verified inputs produce identical XP.
2. **Attributable:** every award has event and agent lineage.
3. **No randomness:** career XP is not a variable-ratio reward mechanism.
4. **No time farming:** elapsed time is not an XP source.
5. **No hidden multipliers:** modifiers must not exist outside this contract.
6. **Auditable:** lifetime totals are reconstructible from verified events.
7. **Stable:** historical awards do not change because a later curve is tuned.
8. **Separable:** optional game-like reward presentation cannot corrupt the career ledger.

## Verification

The implementation at `sage/experimental/airspace/xp_economy.py` provides deterministic conversion, event lineage, validation, and lifetime accumulation. Regression coverage is in `tests/experimental/test_xp_economy.py`.

**Queue #03 conversion v0.1 is locked.**

Future progression-curve work belongs to the promotion/rank threshold and pacing queues; this queue does not invent rank thresholds.
