# SAGE Sports Quantitative Build Contract

**Status:** ACTIVE RESEARCH / SHADOW ONLY  
**Boundary:** no wagering, account access, deposits, withdrawals, or real-money execution.

## Purpose

The Sports/RCE lane is a high-volume operational proving ground for SAGE's governed learning loop. The product objective is **verified capability throughput**, not betting profit. FanDuel may be used as a read-only market reference when its public/authorized data is available; the engine never authenticates to or executes against a sportsbook account.

## Canonical loop

`SENSE → BOUND → LOCK → PARALLEL GENERATE → RESOLVE → SCORE → FALSIFY → OOS VALIDATE → COMPOUND → RECONVERGE`

## Five-flight ownership

- **F1 Intelligence:** ingest read-only market snapshots and contextual features; preserve source/time provenance.
- **F2 Continuity:** persist immutable prediction, parlay-leg, outcome, score, and model-version lineage.
- **F3 Execution:** generate large shadow batches concurrently with isolated worker state; singles and parlays are research records only.
- **F4 Guard:** enforce pre-event temporal locks, SHA-256 integrity, OOS separation, and fail-closed boundaries.
- **F5 Warehouse:** resolve outcomes, cluster failures, compare candidate versions against the same locked OOS baseline, and promote only validated learning.

## Evidence rules

1. A prediction is valid only if it is locked strictly before event start (and before market close when that timestamp is known).
2. Every locked record has a deterministic hash covering its decision inputs and model state.
3. Parlay parents retain explicit leg lineage; a failed leg remains a training signal rather than disappearing inside an aggregate result.
4. Brier score and log loss measure probabilistic calibration; CLV is a separate market-timing measure.
5. Candidate model versions are evaluated on common, locked, unseen OOS events. No candidate is promoted from in-sample improvement alone.
6. Failures, missing data, conflicts, rework, and operator intervention are first-class evidence.
7. "20/20" workflow cells or high test counts prove workflow execution/integrity only; they do not prove predictive skill.

## High-volume target

The shadow engine must support at least **500 independently locked prediction records per cycle** in a deterministic test harness, while keeping real-world ingestion read-only and isolated.

## Super Search integration

External research is a sensor, not authority. Before selecting a new research/model target, SAGE may use Super Search to gather current market-structure, data-quality, methodology, and failure evidence. Search findings remain hypotheses until validated against repository code, locked datasets, and OOS evaluation. Search results never overwrite primary observations or create hindsight labels.

## Promotion boundary

`RESEARCH → VERIFIED SHADOW CAPABILITY → PROMOTABLE` requires code tests, evidence integrity, common-window OOS evaluation, and reconvergence against authoritative main. No economic-performance claim is permitted from task count, elapsed time, simulated bankroll, or raw prediction volume alone.
