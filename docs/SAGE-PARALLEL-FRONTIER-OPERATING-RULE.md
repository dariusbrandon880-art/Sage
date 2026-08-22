# SAGE Parallel Frontier Operating Rule

## Purpose

SAGE treats independently bounded capability paths as a parallel production surface.
Parallel execution increases throughput; it never lowers epistemic or governance
requirements.

## Assembly-line law

1. Enumerate every expected cell before launch.
2. Launch independent cells concurrently when isolation permits.
3. Collect evidence for every cell.
4. A partial observation is **not** a campaign result.
5. A shared infrastructure failure is collapsed into one repair frontier and
   repaired once when safe.
6. Re-run every affected cell after the repair.
7. The campaign cannot complete until every expected cell has an explicit,
   evidence-backed terminal status.
8. Combined status is derived from the cell results; no cell may silently be
   omitted or upgraded.
9. PASS remains an empirical claim requiring the existing evaluator and
   independent verification.
10. Failures and indeterminate observations remain durable knowledge.

## Parallelism boundary

Safe parallelism applies to isolated flights, tests, research candidates,
provider adapters, evidence analysis, and independent build paths. Shared
state mutation, canonical promotion, authority changes, or conflicting writes
remain serialized behind their existing governance boundaries.

## Required campaign terminal states

Every expected cell must resolve to one of:

- `PASS`
- `HOLD`
- `NEGATIVE_RESULT`
- `BLOCKED_WITH_EVIDENCE`

Missing or unobserved cells force `HOLD`.

## C2 reporting invariant

C2 must enumerate the complete campaign before reporting campaign completion.
Reporting one observed cell as the result of a multi-cell campaign is a
verification failure.
