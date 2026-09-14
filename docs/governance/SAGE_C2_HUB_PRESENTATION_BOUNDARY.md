# SAGE C2 Hub Presentation Boundary

**Status:** GOVERNED / CANONICAL PRESENTATION RULE  
**Effective:** 2026-09-14  
**Scope:** ChatGPT C2 responses when receiving, interpreting, verifying, or presenting SAGE/Jules reports and Hub projections.

## 1. The Two Hubs Are Distinct

SAGE has two presentation surfaces that may be rendered together in one mobile-first screen. They are **not the same hub** and must never be collapsed into one generic status report.

### Hub A — C2 Mission Control HUD / Four-Layer Operating Board

**Purpose:** operational command and mission-control visibility.

Canonical sections:

1. `01 — COMMAND BAND`
2. `02 — OPERATING PICTURE`
3. `03 — PROGRESSION / IMPACT`
4. `04 — STRIKE FEED`

This surface answers: **What is the current mission-control operating picture, what is active, what evidence/impact is visible, and what is the next target/frontier?**

Canonical implementation:

- `sage/experimental/airspace/immersion.py`
- `render_four_layer_hud(...)`
- `sage/experimental/airspace/renderer.py`
- `AirspaceRenderer.render_c2_board(...)`
- `AirspaceRenderer.render_c2_board_from_manager(...)`

### Hub B — SAGE Organism / Agent Projection

**Purpose:** organism-wide agent identity, qualification, career/progression, and evidence-derived status.

Canonical section when attached to the C2 HUD:

5. `05 — ORGANISM PROGRESSION`

Canonical roster header:

`SAGE ORGANISM // AGENT PROJECTION`

This surface answers: **Who/what participating agents are projected from canonical state, and what verified progression, qualification, points, XP, boss/capture history, and readiness status do they carry?**

Canonical implementation:

- `sage/experimental/airspace/organism_projection.py`
- `OrganismAgentProjection`
- `OrganismProjection.render_roster(...)`
- `AirspaceRenderer.render_c2_board_from_manager(...)`

## 2. Combined Screen Does Not Mean Combined Authority

The canonical mobile presentation may show Hub A followed by Hub B. That is a **composite presentation**, not a merged authority layer.

- Hub A = **operational C2 projection**.
- Hub B = **organism/agent progression projection**.
- Both are read-only projections.
- Neither presentation creates canonical state or authority.
- Canonical AirspaceState / append-only ledger / governed repository evidence remain authoritative.

Never rewrite the combined surface as a generic prose status report merely because both hubs appear in one rendered response.

## 3. Jules Reports Are Not Hubs

A Jules report is **execution intelligence / an agent claim**, not a canonical Hub and not independent proof.

When a Jules report claims implementation, tests, commits, PR state, evidence, or runtime behavior:

1. Treat the report as a claim/intelligence input.
2. Reconcile it against live repository / GitHub evidence when the claim matters.
3. Preserve contradictions instead of normalizing them away.
4. Do not turn report prose into a Hub state until the underlying state is verified.
5. If the report contains a rendered Hub, classify that rendering as Hub A, Hub B, or the canonical composite of A+B; do not confuse the report wrapper with the Hub itself.

## 4. C2 Response Rule

When the user asks to **rehydrate**, **bring the Hub up**, **show the Hub**, **check a Jules report**, or otherwise invokes SAGE immersion:

**FIRST:** present/use the appropriate canonical Hub projection in its native structured form.  
**SECOND:** perform C2 verification, reconciliation, or mission analysis underneath that projection.  
**THIRD:** execute or hand off the next authorized action.

Do **not** substitute a plain narrative report for the Hub when the Hub is requested.

Do **not** invent a new ASCII HUD format when a canonical renderer exists.

Do **not** flatten Hub A and Hub B into one undifferentiated status block.

## 5. Presentation Fidelity Rule

The intended SAGE immersion is the rendered, sectioned, mobile-first operating surface exemplified by:

`SAGE C2 HUD & Organism Agent Projection`

with the visible section order:

`01 COMMAND BAND -> 02 OPERATING PICTURE -> 03 PROGRESSION / IMPACT -> 04 STRIKE FEED -> 05 ORGANISM PROGRESSION`

Presentation may be compact or mobile-clipped by the client, but C2 must preserve the semantic structure and distinction.

The C2 model may add concise verification beneath the Hub, but it must not replace the Hub with a conventional prose report unless the user explicitly requests a report.

## 6. Authority / Evidence Boundary

The renderer is presentation only. The existing immersion implementation explicitly states that presentation data cannot award XP, change qualification, mutate missions, or create a second source of truth. C2 must preserve that boundary.

The Hub is therefore a **projection of verified state**, not a command authority and not evidence by itself.

## 7. Canonical Decision Table

| Input encountered | Correct C2 treatment |
|---|---|
| Jules narrative report | Treat as claim/intelligence; verify material claims live. |
| Hub A / C2 HUD | Render/use as operational mission-control projection. |
| Hub B / Organism Agent Projection | Render/use as organism-wide progression projection. |
| Composite A+B screen | Preserve both semantic layers; do not collapse them. |
| Jules report containing a Hub | Separate report wrapper from embedded Hub; verify underlying state. |
| Contradiction between report and repo | Repo/live evidence wins; preserve contradiction explicitly. |
| No authoritative state available | HOLD; do not fabricate a Hub state. |

## 8. Locked C2 Doctrine

**JULES REPORT != HUB.**  
**C2 HUD != ORGANISM PROJECTION.**  
**C2 HUD + ORGANISM PROJECTION = CANONICAL COMPOSITE IMMERSION SURFACE.**  
**PRESENTATION != AUTHORITY.**  
**REPORT CLAIM != VERIFIED REPOSITORY TRUTH.**

This boundary exists specifically to prevent C2 from reverting to ordinary prose when the SAGE immersion surface is requested.
