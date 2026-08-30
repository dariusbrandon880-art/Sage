# SAGE Sports Signal Intelligence Contract

**Status:** ACTIVE RESEARCH / SHADOW ONLY
**Boundary:** External signals may inform simulated predictions; no sportsbook authentication, wagering, deposits, withdrawals, or real-money execution.

## Purpose

SAGE treats heterogeneous sports information as a time-bounded Research/Intelligence pipeline. The objective is to determine, with locked out-of-sample evidence, whether a signal improves probabilistic forecasting. A signal is not considered useful merely because it appears correlated with a past outcome.

## Canonical Signal Lifecycle

`DISCOVER → NORMALIZE → TIMESTAMP → BOUND → LOCK → PREDICT → RESOLVE → ATTRIBUTE → OOS VALIDATE → COMPOUND`

## Signal Classes

- Availability: injuries, scratches, suspensions, confirmed starters, minutes restrictions, lineup/rotation changes.
- Context: rest, travel, schedule density, altitude, coaching changes, role changes, roster transitions.
- Environment: weather, wind, precipitation, temperature, venue, surface, and other event conditions where applicable.
- Performance: player/team efficiency, usage, possession, shot quality, matchup, fatigue, and other measurable pre-event features.
- Market: FanDuel-shaped reference snapshots, consensus prices, line movement, and other authorized read-only market observations.

## Temporal Hygiene

1. Every signal carries an authoritative `observed_at_utc` timestamp and source provenance.
2. A signal may influence a prediction only when its observation timestamp is strictly before the prediction lock.
3. Information observed after lock is retained only as a diagnostic variant and must never be used to retroactively alter the locked prediction.
4. Outcome-derived fields are unavailable to generation and OOS candidate construction.
5. When a market-close timestamp exists, predictions must also preserve whether the lock preceded that boundary.

## Signal Provenance

Each signal-to-prediction relationship must remain auditable:

`Signal ID → Source → Observed Timestamp → Normalized Feature → Prediction ID → Lock Hash → Outcome → Diagnostic`

Signal payloads and normalized feature state must be deterministically hashable. Missing, conflicting, stale, or unverifiable signals are explicit states, not silently substituted facts.

## Baseline / Candidate Evaluation

For a common locked OOS event set, retain separate baseline and signal-adjusted predictions. Evaluate:

- Brier score for probabilistic calibration.
- Log loss for confidence-sensitive error.
- CLV/market movement as a separate market-timing observation.
- Signal attribution as the difference in evaluation between otherwise comparable baseline and signal-adjusted predictions.

No signal is promoted because of a single win, a short streak, raw ROI, or hindsight agreement. Promotion requires repeatable OOS evidence over a declared evaluation window and must preserve the underlying event and signal lineage.

## Failure Learning

Material misses become structured training evidence. Diagnostics should distinguish, where supported by evidence:

- high-confidence miss;
- low-confidence miss;
- stale or late signal;
- conflicting sources;
- missing-data condition;
- overreaction to signal;
- underreaction to signal;
- market movement unexplained by the current feature set.

Clusters generate hypotheses for candidate model versions. Hypotheses remain unpromoted until common-window OOS validation.

## Five-Flight Ownership

- **F1 Intelligence:** discover, normalize, timestamp, and provenance external signals.
- **F2 Continuity:** persist signal, prediction, parlay-leg, model-version, and diagnostic lineage.
- **F3 Execution:** consume only eligible pre-lock signals in isolated concurrent shadow generation.
- **F4 Guard:** enforce temporal lock, leakage prevention, source validity, and fail-closed boundaries.
- **F5 Warehouse:** resolve outcomes, attribute signal contribution, cluster failures, and promote validated learning.

## Super Search Boundary

Super Search is an external intelligence sensor. It may surface current injuries, lineups, schedules, weather, market-structure observations, research, or methodology. Search findings are hypotheses until captured with source provenance and validated inside SAGE's temporal/OOS evidence boundary. Search results never overwrite repository truth, locked predictions, or outcomes.

## Velocity Measurement

Signal ingestion contributes to verified velocity only when it produces reusable capability that survives verification and reconvergence. Record volume alone is not velocity. The minimum completion boundary is:

`BUILD + VERIFY + EVIDENCE + REUSABLE CAPABILITY`

Track execution duration, eligible signal count, prediction throughput, verification status, rework/conflicts, intervention, OOS sample size, and validated capability delta.

## Promotion Rule

`RESEARCH → VERIFIED SHADOW CAPABILITY → PROMOTABLE`

requires code-level verification, deterministic evidence, temporal integrity, common-event OOS evaluation, and reconvergence against authoritative main. No economic-performance claim may be inferred from simulated bankrolls, prediction count, elapsed time, or a single successful event.
