# SAGE Badge Display Policy — Compact Organism Visibility

**Status:** DESIGN / GOVERNANCE — IMPLEMENTATION PENDING
**Scope:** agent identity tags, immersion HUDs, progression projections

## Decision

SAGE badges are part of organism-wide agent visibility, but badges must **not stack without bound** in identity tags. The canonical badge ledger remains the future authority; the display layer is read-only.

Every agent identity may expose badge status, but the default compact tag should show a **bounded badge summary**, not the complete badge collection.

## Compact display contract

Default identity/tag surfaces should use this order:

`IDENTITY // RANK/QUAL // POINTS // XP // BADGES // STATUS`

The `BADGES` segment should be compact:

- show a small bounded set of **featured/active badges**;
- show a count for the remaining earned badges;
- never print an unbounded badge list into every tag;
- provide a drill-down/detail surface for the complete badge inventory;
- preserve badge provenance and exact definitions outside the presentation string.

Recommended compact form:

`BADGES ★◆◈ +7`

where the symbols represent the featured badges and `+7` means seven additional earned badges not expanded in the compact tag. Exact glyph semantics must come from the canonical badge registry rather than being inferred by the renderer.

## Stacking rules

1. **Bounded visible stack:** identity tags have a fixed maximum number of featured badge glyphs.
2. **Overflow compression:** badges beyond the visible bound collapse into a count; they do not wrap the tag indefinitely.
3. **Priority ordering:** featured badges are selected by governed display priority, not by whichever badge was most recently earned unless policy explicitly says so.
4. **No badge inflation:** duplicate awards do not create duplicate visible glyphs unless the canonical badge definition explicitly supports tiers/stacks.
5. **Tier compression:** tiered badges render as one badge with its current governed tier rather than one glyph per historical tier.
6. **Cross-agent consistency:** every agent uses the same badge display policy and registry.
7. **Read-only projection:** rendering cannot award, remove, reorder canonically, or mutate badges.
8. **Full inventory remains accessible:** compactness must never destroy the ability to inspect the complete earned-badge ledger.
9. **No self-award:** an agent cannot authoritatively grant itself a badge.
10. **Space budget is part of the UI contract:** badge presentation must be evaluated against mobile-first tag width before universal rollout.

## What this does NOT decide

This policy does not yet define:

- the complete badge taxonomy;
- badge earning criteria;
- badge tier mathematics;
- exact maximum featured-badge count;
- canonical badge storage schema;
- automatic badge issuance;
- rank/promotion interaction;
- numeric scoring thresholds.

Those require a dedicated validated badge design frontier and Director decision record. The current repository search shows no authoritative badge registry implementation, so this document intentionally records the **display/governance requirement without inventing a production badge store**.

## Organism-wide relationship

The eventual universal agent projection should expose Points, Career XP, governed rank/qualification, badge summary, and operational status from canonical state. The projection must not create a second source of truth.

The intended architecture is therefore:

`Verified Evidence → Organism Scoring Authority → Points/XP + Qualification/Rank + Badge Authority → Read-Only Agent Projection → Compact Tag / HUD`

This keeps the operational picture legible while preserving full auditability underneath.
