# SAGE Sports Quantitative Build Contract

**Status:** ACTIVE RESEARCH / SHADOW ONLY  
**Boundary:** no wagering, account access, deposits, withdrawals, or real-money execution.

## Purpose

The Sports/RCE lane is a high-volume operational proving ground for SAGE's governed learning loop. The product objective is **verified capability throughput**, not betting profit. FanDuel may be used as a read-only market reference when its public/authorized data is available; the engine never authenticates to or executes against a sportsbook account.

## Canonical loop

`SENSE → BOUND → LOCK → PARALLEL GENERATE → RESOLVE → SCORE → FALSIFY → OOS VALIDATE → COMPOUND → RECONVERGE`

## Five-flight execution model

F1–F5 are **five reusable, open execution slots**. They have no permanent capability ownership and no fixed research, continuity, execution, governance, or warehouse identity. C2 may assign any authorized sports mission to any available slot for a particular wave.

A wave may therefore assign different sports capabilities to all five slots, including ingestion/recon, modeling, repair, testing, governance, evidence, settlement, or other authorized work. The assignment is per-wave and must be recorded in the flight mission specification and evidence.

The capabilities below are responsibilities of the system, not permanent flight identities:

- read-only market snapshots and contextual features with source/time provenance;
- immutable prediction, parlay-leg, outcome, score, and model-version lineage;
- concurrent shadow generation with isolated worker state;
- pre-event temporal locks, SHA-256 integrity, OOS separation, and fail-closed boundaries;
- outcome resolution, failure clustering, common-OOS comparison, and validated learning promotion.

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
