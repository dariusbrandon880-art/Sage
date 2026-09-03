# SAGE Boss Badge Display Policy — Organism Visibility

**Status:** IMPLEMENTED PROJECTION / GOVERNED BY QUEUE #08
**Scope:** agent identity tags, immersion HUDs, progression projections

## Canonical rule

Queue #08 is the authority for the Boss badge cadence:

- **Major Boss ⭐⭐:** every 20 verified Major Boss kills earns 1 badge and every 20 verified Major Boss captures earns 1 badge.
- **Big Boss ⭐:** every 30 verified Big Boss kills earns 1 badge and every 30 verified Big Boss captures earns 1 badge.
- Kill and capture are independent tallies; both may be recorded by one verified encounter.
- Badges persist across rank-ups.
- Badges remain separate from Points, Career XP, qualifications, rank, and promotion gates.

The renderer does not decide whether work is a Boss. Boss classification remains upstream, evidence-backed, and Mission-Director governed.

## Canonical persistence boundary

Verified Boss outcomes are recorded as `BOSS_OUTCOME_VERIFIED` events in the existing append-only AirspaceManager ledger. The badge projection reconstructs the outcome history from that ledger and applies the locked cadence. No separate badge database or presentation-side badge state is created.

This preserves the organism boundary:

`Verified Evidence → Governed Boss Classification → Airspace Event Ledger → Boss/Badge Projection → Agent Tag / HUD`

Points and Career XP remain on their existing canonical path:

`Verified Evidence → PointsXPEconomy → POINTS_AWARDED → Career XP`

The two paths share the same verified-event/evidence boundary without collapsing badges into Points or XP.

## Compact organism tag

The preferred compact projection is:

`IDENTITY // CQL/SQL // POINTS // XP // BOSS badges // ⚔️ kills // ┃ captures // STATUS`

Example:

`GPT // CQL-4 // SQL-3 // POINTS 250 // XP 25 // BOSS ⭐×1 ⭐⭐×2 // ⚔️ 34 // ┃ 21 // READY`

The Boss stars identify class-earned badges; crossed swords are verified Boss kills; regular Stripes are verified Boss captures. These markers are not interchangeable.

## Read-only rule

The identity/HUD layer:

- reads canonical AirspaceState for qualification and Career XP;
- reconstructs Points from the canonical `POINTS_AWARDED` ledger;
- reconstructs Boss kills, captures, and earned badges from verified Boss outcome events;
- never awards Points, XP, badges, rank, or qualifications;
- never classifies an arbitrary task as a Boss;
- never deletes historical outcomes;
- exposes the same projection vocabulary to every participating SAGE agent.

## Rank-up semantics

Queue #02 requires XP and underlying verified Boss history to persist across rank-up. The visible kill/capture board cycle resets at rank-up, while badges persist. Until a canonical rank-transition event is available to the projection, the organism projection intentionally exposes the reconstructed verified totals rather than inventing a reset boundary.

## Boundary

This policy does not define rank thresholds, automatic promotion, Boss detection, or new Boss classes. Queue #09 calibration remains research-only for exact numeric rank thresholds. The implementation here only closes the already-locked Queue #08 badge accounting/display gap using the existing event ledger.
