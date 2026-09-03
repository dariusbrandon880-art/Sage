# Queue #09 — Calibration Harness Research Record

**Status:** RESEARCH / SIMULATION SUBSTRATE — NUMERIC THRESHOLDS STILL HOLD
**Base:** `main` @ `db461cb8c9f72e79ffc8de44dc5c2b1660209d7e`
**Branch:** `c2/queue-09-calibration-harness`

## Mission

Provide a deterministic replay surface for Queue #09 without creating a second career store, inventing empirical observations, or promoting any numeric threshold to authoritative policy.

## Repo-truth inputs

The harness reuses the live verified-event scoring and Points -> Career XP economy. The canonical implementation defines event types, base Points, four bounded scoring dimensions (1–5), and deterministic conversion at 10 verified Points per Career XP. Verified event awards require a verified-event reference and evidence references.

The Queue #09 threshold-validation contract requires empirical/simulation evidence before exact promotion thresholds are locked. Rank remains a governed aggregate designation, not an XP-only definition.

## What was added

- `sage/experimental/airspace/career_calibration.py`
  - deterministic `CalibrationEvent` inputs;
  - replay through `PointsXPEconomy.score_verified_event()`;
  - cumulative Points and whole Career XP reconstruction;
  - parameterized increasing-delta, piecewise-band, and hybrid candidate curves;
  - explicit separation of `xp_threshold_reached` from actual promotion eligibility;
  - six deterministic simulation profiles required by Queue #09.
- `tests/experimental/test_career_calibration.py`
  - replay/conversion invariants;
  - curve monotonicity checks;
  - hybrid correction failure detection;
  - qualification/evidence/no-skipping anti-bypass checks;
  - deterministic profile coverage.

## Evidence boundary

The bundled profile mixes are **simulation inputs, not production telemetry**. Their outputs must not be interpreted as observed player/agent progression rates. The harness is intentionally parameterized so later canonical event-history data can be replayed without rewriting the calibration engine.

No exact 30-rank threshold values are selected here. No rank mutation, qualification mutation, automatic promotion, or alternate Points/XP authority is introduced.

## External research synthesis

External game-design and analytics research reinforces the chosen method:

- GameDeveloper's quantitative design guidance compares linear, exponential, and increasing-delta threshold families and emphasizes estimating progression speed rather than choosing values in isolation.
- GameDeveloper telemetry guidance recommends recording and analyzing gameplay events and progression behavior iteratively.
- Unity Analytics documentation describes progression funnels that measure how many users reach ordered progression steps and how long movement between steps takes.
- PlayFab analytics documentation describes event aggregation/querying for measures such as XP gained and time to complete progression activities.
- GameDeveloper systems guidance recommends using the simplest progression that meets the design goal and measuring related progression rates together.

These sources support **calibration against observed progression velocity and telemetry**; they do not provide SAGE thresholds.

## Next evidence frontier

1. Feed canonical historical verified-event observations into the replay format.
2. Record progression-volume/time intervals where canonical timestamps support them.
3. Compare candidate curve families against routine, builder, breakthrough, elite, collaborative, and recovery-heavy profiles.
4. Measure threshold-crossing velocity and sensitivity to exceptional events.
5. Produce negative-case evidence showing that XP/Points/Boss outcomes/badges alone cannot satisfy promotion gates.
6. Only then produce a Director decision record for exact numeric thresholds.

**Authoritative outcome remains HOLD until the required calibration evidence exists.**
