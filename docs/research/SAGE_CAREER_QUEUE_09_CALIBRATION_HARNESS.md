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
- `sage/experimental/airspace/boss_progression.py`
  - verified Boss outcome recording through the existing Airspace event ledger;
  - locked Big Boss / Major Boss classification vocabulary;
  - independent kill/capture reconstruction;
  - Queue #08 badge cadence reconstruction without a second store.
- `sage/experimental/airspace/organism_projection.py`
  - one read-only organism-wide projection joining identity, CQL/SQL, Points, Career XP, Boss outcomes, badges, and status;
  - one shared tag vocabulary for every participating agent.
- `sage/experimental/airspace/nameplate.py`
  - manager-backed full organism nameplate and roster projection while preserving the existing state-only API.
- `tests/experimental/test_career_calibration.py`
  - replay/conversion invariants;
  - curve monotonicity checks;
  - hybrid correction failure detection;
  - qualification/evidence/no-skipping anti-bypass checks;
  - deterministic profile coverage.
- `tests/experimental/test_organism_projection.py`
  - Boss cadence and independent kill/capture tests;
  - duplicate/replay protection;
  - unified Points/XP/Boss projection coverage.

## Evidence boundary

The bundled profile mixes are **simulation inputs, not production telemetry**. Their outputs must not be interpreted as observed player/agent progression rates. The harness is intentionally parameterized so later canonical event-history data can be replayed without rewriting the calibration engine.

No exact 30-rank threshold values are selected here. No rank mutation, qualification mutation, automatic promotion, or alternate Points/XP authority is introduced.

## Organism-wide scoring direction

The organism, not an individual agent, is the scoring authority. Agents never self-award, self-certify, or directly mutate their own SAGE Points, Career XP, rank, badges, or promotion state. Every participating agent is evaluated through the same canonical evidence pipeline, using attributable verified events and the existing scoring dimensions, while keeping scoring authority outside the scored agent.

Queue #09 does not lock exact rank thresholds, telemetry targets, evaluator topology, or promotion policy. Those remain subject to calibration evidence and a Director decision record. The organism projection implemented in this branch is a read-only reconciliation layer; it does not turn provisional thresholds into policy.

## Universal identity projection

Every SAGE identity/agent tag can now use one shared manager-backed projection:

`IDENTITY // CQL/SQL // POINTS // XP // BOSS badges // ⚔️ kills // ┃ captures // STATUS`

Points and Career XP are reconstructed from the canonical Airspace ledger/economy. Verified Boss outcomes and badge state are reconstructed from `BOSS_OUTCOME_VERIFIED` events in that same append-only ledger. The presentation layer never infers, awards, removes, or otherwise mutates progression.

Queue #08 semantics are explicit: Major Boss ⭐⭐ awards one badge per 20 verified Major Boss kills and per 20 verified Major Boss captures; Big Boss ⭐ awards one badge per 30 verified Big Boss kills and per 30 verified Big Boss captures. Kill and capture tallies remain independent, and both can occur in one verified encounter. Badges persist across rank-ups.

The dedicated display policy is recorded in `docs/research/SAGE_BADGE_DISPLAY_POLICY.md`.

## Scoring/progression invariants

1. **Universal attribution:** every scored agent has an unambiguous agent identity and attributable evidence.
2. **Evidence-first scoring:** Points originate only from verified events with required evidence references.
3. **No self-scoring:** the scored agent cannot authoritatively assign its own Points or promotion state.
4. **One canonical economy:** all agents use the same Points/XP authority rather than agent-specific scoring stores.
5. **Comparable evaluation:** equivalent verified work is evaluated through the same bounded scoring dimensions and governance rules.
6. **Append-only provenance:** scoring decisions remain reconstructable from the underlying verified events and evidence.
7. **Governed progression:** Points/XP contribute to progression but do not bypass qualification, evidence, no-skipping, or other promotion gates.
8. **Calibration before lock:** exact scoring weights, threshold values, and velocity targets remain provisional until supported by observed/replay evidence.
9. **Independent Boss accounting:** Boss kills, captures, and badges remain separate signals from Points, XP, qualification, and rank.
10. **Single projection boundary:** Points, XP, qualification/rank, Boss outcomes, badges, and status are displayed from canonical state/ledger rather than separate presentation stores.

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
6. Validate the universal agent-attribution/scoring substrate against all organism participants without creating a second scoring authority.
7. Add canonical rank-transition events when rank becomes operationally authoritative, then derive the Queue #02 visible kill/capture board-cycle reset without deleting lifetime history.
8. Validate the compact organism tag against real mobile HUD space.
9. Only then produce a Director decision record for exact numeric thresholds and any remaining progression policy.

**Authoritative numeric rank outcome remains HOLD until the required calibration evidence exists.**
