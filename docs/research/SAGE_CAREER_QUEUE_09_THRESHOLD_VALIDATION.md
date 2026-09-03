# Queue #09 — Promotion Threshold Validation Decision Record

**Status:** RESEARCH / DECISION METHOD LOCK — NUMERIC THRESHOLDS NOT YET AUTHORITATIVE  
**Base:** `main` after PR #418 merge  
**Purpose:** prevent guessed rank thresholds while defining the exact evidence required to lock them.

## 1. Repo-truth baseline

The live `main` state establishes:

- Promotion is a governed decision gate, not an automatic consequence of XP.
- Promotion must be sequential/no-skipping.
- Lifetime Career XP is retained across rank changes.
- Qualification state comes from the canonical `QualificationRegistry`.
- Verified progression is persisted through the existing Airspace event/state substrate.
- The verified Points economy converts **10 verified Points = 1 Career XP**.
- Verified event value is based on an event base value plus four bounded dimensions: difficulty, verification quality, impact, and reuse; each dimension is 1–5.
- The shared rank taxonomy is a 30-rank ladder across six bands.
- Rank is an aggregate career designation and is explicitly **not defined as an XP threshold**.
- The legacy direct-XP rank mutation path is disabled.

Therefore, the old `100 / 500 / 1000 XP` values visible in the unmerged historical career-engine work are **not authoritative** and must not be revived as Queue #09 thresholds.

## 2. What the external design research establishes

Game-development references consistently treat progression thresholds as a pacing control tied to the rate at which progression currency is earned, rather than as universal constants. Progressive curves are common, but the curve must be tuned against expected progression speed and corrected using observed behavior.

- GameDeveloper's quantitative-design guidance compares linear, exponential, and increasing-delta curves and explicitly emphasizes estimating progression speed when selecting thresholds.
- GameDeveloper's progression-curve research recommends simulation before launch to fit XP requirements against expected player behavior.
- Roblox Creator Hub similarly describes XP curves as tunable progression controls and notes that early thresholds should be low enough to make progression immediately legible and rewarding.
- Unity and PlayFab analytics documentation supports collecting event/progression telemetry and using it to measure progression, funnels, and behavioral outcomes.

These references support the **method**, not any particular SAGE number.

## 3. Numeric validation rule

A numeric promotion threshold becomes authoritative only after it can be reproduced from a governed calibration dataset.

For each candidate promotion step `r -> r+1`, the calibration record MUST contain:

1. canonical lifetime Career XP at the observation point;
2. cumulative verified Points and the exact `10:1` conversion;
3. distribution of verified event types contributing those Points;
4. distribution of the four verified-event dimensions;
5. qualification state (CQL/SQL) from the canonical registry;
6. attributable promotion evidence references;
7. elapsed progression interval or an equivalent normalized progression-volume measure;
8. enough observations to distinguish ordinary progression from exceptional/Boss outcomes.

Without those observations, an exact numeric threshold is a design hypothesis, not a validated repo fact.

## 4. Required threshold shape

Queue #09 should use a monotonic, progressively harder threshold schedule, but should not force a specific formula before calibration.

The validation candidate set SHOULD compare at least:

- **Increasing-delta curve:** threshold increments grow gradually by rank/band.
- **Piecewise band curve:** gentle early growth with controlled increases at the six locked rank bands.
- **Hybrid curve:** increasing deltas with manually corrected milestone values where simulated pacing exposes a chokepoint.

A pure exponential curve should not be adopted merely because it is common in games; it must demonstrate acceptable progression velocity against SAGE's verified-event economy.

## 5. Promotion dimensions

The gate must distinguish **necessary conditions** from **sufficient evidence**.

### Necessary conditions already established

- immediate next rank only;
- lifetime Career XP requirement once numerically validated;
- required canonical qualification state;
- attributable canonical promotion evidence;
- valid/non-replayed/non-stale evidence;
- authorized governance decision.

### Signals that remain assessment inputs, not automatic rank setters

- Points;
- Boss kills/captures;
- badges;
- accomplishments;
- workflow evolution;
- capability evolution;
- career history.

No one of these signals may directly mutate rank.

## 6. Calibration simulation

Before implementation, the validation harness should replay representative verified-event mixes against candidate curves:

- **Routine operator:** mostly RECON / ANALYSIS / VERIFICATION work;
- **Builder:** BUILD / REPAIR-heavy work;
- **Breakthrough operator:** periodic BREAKTHROUGH / CAPABILITY_CAPTURE events;
- **Elite operator:** rare Boss outcomes plus ordinary verified work;
- **Collaborative operator:** mixed attributable contributions;
- **Recovery-heavy operator:** repeated failure/recovery cycles.

For each profile, record:

`verified events -> Points -> Career XP -> candidate promotion readiness -> qualification gate -> time/volume to next rank`

The harness must prove that high-value events accelerate progression without allowing a small number of exceptional events to bypass the career-evidence and qualification gates.

## 7. Anti-bypass invariants

The eventual implementation MUST reject/hold when:

- XP alone reaches a candidate threshold;
- Points alone reach a candidate threshold;
- Boss outcomes alone reach a candidate threshold;
- badges alone reach a candidate threshold;
- qualification is missing or stale;
- promotion evidence is missing, replayed, stale, or non-canonical;
- a rank is skipped;
- an untrusted/legacy XP mutation path attempts to change rank.

## 8. Decision

**Decision:** lock the calibration method now; do **not** lock numeric thresholds yet.

This is the only conclusion currently supportable by the live repository because `main` contains the verified event/Points/XP mechanics and qualification substrate, but no authoritative empirical progression-rate dataset from which exact rank thresholds can be calibrated.

The previous quadratic proposal (`5 × (level − 1)^2`) is explicitly rejected as an authoritative SAGE rule. It may be used only as a simulation candidate if useful for comparative analysis.

Likewise, the historical `100 / 500 / 1000 XP` values are rejected as promotion thresholds because they belong to unmerged/deferred career-engine work and conflict with the Queue #09 boundary.

## 9. Queue #09 implementation gate

Queue #09 may move from research to implementation after the calibration record contains:

- a reproducible observation/simulation dataset;
- selected curve family and rationale;
- exact cumulative XP thresholds for all 30 promotion steps (or an explicitly justified banded equivalent);
- exact qualification dimensions, where numeric qualification requirements are actually supported by canonical state;
- negative-case evidence for all anti-bypass invariants;
- a Director-authorized decision record;
- exact-head CI verification of the resulting promotion gate.

Until then, **HOLD** remains the correct authoritative outcome for an otherwise threshold-ready candidate whose numeric policy has not been validated.
