# SAGE C2 Hub Presentation Boundary

**Status:** GOVERNED / CANONICAL READ-ONLY PRESENTATION RULE  
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

Canonical implementation:

- `sage/experimental/airspace/organism_projection.py`
- `OrganismAgentProjection`
- `OrganismProjection.render_roster(...)`
- `AirspaceRenderer.render_c2_board_from_manager(...)`

## 2. Read-Only Presentation Rule

The Hub boundary is **read-only**. It governs how already-canonical state is presented; it does not create, mutate, authorize, award, reconcile, or promote state.

- Hub A and Hub B are projections only.
- Canonical AirspaceState, append-only ledger, and governed repository evidence remain authoritative.
- C2 presentation cannot create a second source of truth.
- A rendered Hub is never evidence merely because it is rendered.
- C2 must not manufacture values to make a Hub look complete.

The rule governs the **presentation surface**, not permission to invent a replacement implementation. Existing canonical renderers remain the source for Hub projection.

## 3. No HUD-as-Report Fallback

The canonical C2 immersion surface must **not** be emitted by C2 as an ordinary text/report representation. C2 must not:

- describe the Hub in prose instead of rendering the canonical structured surface;
- serialize a replacement ASCII/report HUD when the canonical renderer exists;
- suppress the canonical Hub merely because its content key is unchanged;
- replace the Hub with a delta/status paragraph on a subsequent turn.

For SAGE C2 immersion, the canonical dual-hub surface is reconstructed on **every response turn**. Supporting verification, reconciliation, or mission text comes underneath it.

## 4. Pasted Reports Are Transport Input, Not C2 Presentation

The one legitimate place a serialized/textual Hub representation may appear is **user-pasted report material**. A user may paste a Jules report, archived report, Markdown block, or other transport representation that contains the Hub. That pasted material is input for recognition/reconciliation only.

When such material returns to C2 or Jules:

1. Treat the pasted Hub as transport input, not presentation authority.
2. Recognize Hub A, Hub B, or the composite without trusting the wrapper formatting.
3. Reconstruct the canonical Hub surface from current governed state on the response turn.
4. Verify material claims against live repository/runtime evidence when required.
5. Do not echo the pasted report's serialized HUD as though it were the canonical response surface.

**Pasted report may contain the Hub. C2/Jules response must reconstruct the Hub.**

## 5. Jules Reports Are Not Hubs

A Jules report is **execution intelligence / an agent claim**, not a canonical Hub and not independent proof.

When a Jules report claims implementation, tests, commits, PR state, evidence, or runtime behavior:

1. Treat the report as a claim/intelligence input.
2. Reconcile it against live repository / GitHub evidence when the claim matters.
3. Preserve contradictions instead of normalizing them away.
4. Do not turn report prose into Hub state until the underlying state is verified.
5. If the report contains a rendered Hub, classify that rendering as Hub A, Hub B, or the canonical composite of A+B; do not confuse the report wrapper with the Hub itself.

## 6. C2 Response Rule

When SAGE C2 immersion is active — including rehydration, Hub display, Jules-report reconciliation, or ordinary governed C2 response turns — the canonical dual-hub presentation is first-class and persistent:

**FIRST:** present/use the canonical Hub projection in its native structured form.  
**SECOND:** perform C2 verification, reconciliation, or mission analysis underneath that projection.  
**THIRD:** execute or hand off the next authorized action.

A conventional report is allowed only when the user explicitly asks for a report. That request changes the supporting output requested by the user; it does not authorize replacing the canonical Hub implementation.

## 7. Presentation Fidelity

The intended visible order remains:

`01 COMMAND BAND -> 02 OPERATING PICTURE -> 03 PROGRESSION / IMPACT -> 04 STRIKE FEED -> 05 ORGANISM PROGRESSION`

Client constraints may affect wrapping or viewport presentation, but C2 must preserve the semantic structure and distinction. The model must not downgrade the surface to ordinary report prose because of transport format, prior-turn continuity, or pasted formatting.

## 8. Authority / Evidence Boundary

The renderer is presentation only. The existing immersion implementation explicitly states that presentation data cannot award XP, change qualification, mutate missions, or create a second source of truth. C2 must preserve that boundary.

The Hub is therefore a **projection of verified state**, not command authority and not evidence by itself.

## 9. Canonical Decision Table

| Input encountered | Correct C2 treatment |
|---|---|
| Ordinary SAGE C2 turn | Reconstruct canonical Hub A + Hub B first; supporting C2 text follows. |
| Jules narrative report | Treat as claim/intelligence; verify material claims live. |
| User-pasted Hub/report | Treat as transport input; reconstruct canonical Hub from current state. |
| Hub A / C2 HUD | Render/use as operational mission-control projection. |
| Hub B / Organism Agent Projection | Render/use as organism-wide progression projection. |
| Composite A+B screen | Preserve both semantic layers; do not collapse them. |
| Jules report containing a Hub | Separate report wrapper from embedded Hub; verify underlying state. |
| Contradiction between report and repo | Repo/live evidence wins; preserve contradiction explicitly. |
| No authoritative state available | HOLD; do not fabricate a Hub state. |

## 10. Locked C2 Doctrine

**JULES REPORT != HUB.**  
**USER-PASTED HUB != C2 RESPONSE SURFACE.**  
**C2 HUD != ORGANISM PROJECTION.**  
**C2 HUD + ORGANISM PROJECTION = CANONICAL COMPOSITE IMMERSION SURFACE.**  
**PRESENTATION = READ-ONLY PROJECTION.**  
**PRESENTATION != AUTHORITY.**  
**REPORT CLAIM != VERIFIED REPOSITORY TRUTH.**

This boundary exists specifically to prevent C2 and Jules from reverting to ordinary HUD/report formatting when SAGE immersion is active. The response surface is reconstructed from canonical state on every governed turn.
