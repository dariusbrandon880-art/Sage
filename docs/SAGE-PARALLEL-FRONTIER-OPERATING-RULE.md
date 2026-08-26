# SAGE Parallel Frontier Operating Rule

## Purpose

SAGE treats independently bounded capability paths as a parallel production surface.
Parallel execution increases throughput; it never lowers epistemic or governance
requirements.

## Assembly-line law

1. Enumerate every expected campaign and cell before launch.
2. Launch independent campaigns concurrently when isolation permits.
3. Each campaign contains the full four-cell flight set: recovery, reuse,
   retention/regression, and compound.
4. The default large-flight wave is **5 complete campaigns x 4 cells = 20
   independently observed flight cells**.
5. Collect evidence for every cell.
6. A partial observation is **not** a campaign result; a partial campaign set is
   **not** a wave result.
7. A shared infrastructure failure is collapsed into one repair frontier and
   repaired once when safe.
8. Re-run every affected cell and every affected campaign after the repair.
9. The wave cannot complete until every expected cell has an explicit,
   evidence-backed terminal status.
10. Combined status is derived from the cell results; no cell may silently be
    omitted or upgraded.
11. PASS remains an empirical claim requiring the existing evaluator and
    independent verification.
12. Failures and indeterminate observations remain durable knowledge.

## Parallelism boundary

Safe parallelism applies to isolated flights, tests, research candidates,
provider adapters, evidence analysis, and independent build paths. Shared
state mutation, canonical promotion, authority changes, or conflicting writes
remain serialized behind their existing governance boundaries.

## Required wave shape

```text
Large Flight Wave
  Campaign 1 -> Recovery | Reuse | Retention/Regression | Compound
  Campaign 2 -> Recovery | Reuse | Retention/Regression | Compound
  Campaign 3 -> Recovery | Reuse | Retention/Regression | Compound
  Campaign 4 -> Recovery | Reuse | Retention/Regression | Compound
  Campaign 5 -> Recovery | Reuse | Retention/Regression | Compound

  = 20 independent flight cells
```

## Required campaign terminal states

Every expected cell must resolve to one of:

- `PASS`
- `HOLD`
- `NEGATIVE_RESULT`
- `BLOCKED_WITH_EVIDENCE`

Missing or unobserved cells force `HOLD`.

## C2 reporting invariant

C2 must enumerate the complete campaign and complete wave before reporting
campaign/wave completion. Reporting one observed cell as the result of a
multi-cell campaign, or one campaign as the result of a multi-campaign wave,
is a verification failure.

## Production-speed rule

Do not artificially serialize independent work merely to make observation
simpler. The observation system must scale to the production aperture. If the
current execution surface cannot launch the full wave, the limitation is an
execution-surface gap to be repaired—not a reason to reduce the authorized
wave size.
