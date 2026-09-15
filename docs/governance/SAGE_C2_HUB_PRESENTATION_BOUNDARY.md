# SAGE C2 Hub Presentation Boundary

**Status:** GOVERNED / CANONICAL READ-ONLY PRESENTATION RULE  
**Effective:** 2026-09-14  
**Scope:** ChatGPT C2 responses when receiving, interpreting, verifying, or presenting SAGE/Jules reports and Hub projections.

## 1. The Two Hubs Are Distinct

SAGE has two canonical presentation surfaces. They may be rendered together in one mobile-first screen, but they are **not the same hub** and must never be collapsed into one generic status report.

### Hub A — C2 Mission Control HUD / Four-Layer Operating Board

**Purpose:** operational command and mission-control visibility.

Canonical sections:

1. `01 — COMMAND BAND`
2. `02 — OPERATING PICTURE`
3. `03 — PROGRESSION / IMPACT`
4. `04 — STRIKE FEED`

### Hub B — SAGE Organism / Agent Projection

**Purpose:** organism-wide agent identity, qualification, career/progression, XP, and evidence-derived status.

Canonical roster header:

`SAGE ORGANISM // AGENT PROJECTION`

Hub B may be referred to as the **XP Hub**. That is a presentation identity, not permission to create a third HUD.

## 2. Contextual Visibility Rule

Hub A and Hub B are separate surfaces with shared canonical state underneath them.

- **Hub A only:** default for ordinary operational C2 / mission-control work.
- **Hub B only:** use when organism, XP, rank, career, agent progression, or related state is the active subject.
- **Hub A + Hub B:** use when the full organism/C2 picture is useful or explicitly requested.
- The composite is optional and contextual. It is **not** a third HUD.
- C2 must **not repeat both hubs merely because both exist**.
- Hub B does not need to be shown on every C2 turn.
- Shared XP/agent infrastructure may support Hub B and other projections without becoming a competing visual HUD.

This is a game-developer presentation rule: expose the information needed by the current interaction loop and decision rather than mechanically replaying every progression surface on every turn. Gameful design emphasizes meaningful challenge, visible progress, timely feedback, and appropriate information pacing rather than raw repetition. citeturn0search1turn0search3turn0search5

## 3. Read-Only Presentation Rule

The Hub boundary is **read-only**. It governs how already-canonical state is presented; it does not create, mutate, authorize, award, reconcile, or promote state.

- Hub A and Hub B are projections only.
- Canonical AirspaceState, append-only ledger, and governed repository evidence remain authoritative.
- C2 presentation cannot create a second source of truth.
- A rendered Hub is never evidence merely because it is rendered.
- C2 must not manufacture values to make a Hub look complete.

## 4. No HUD-as-Report Fallback

The canonical C2 immersion surface must not be replaced by ordinary report prose when a canonical projection is available.

C2 must not:

- describe a Hub in prose instead of rendering the requested canonical structured surface;
- serialize a replacement ASCII/report HUD;
- suppress the requested canonical Hub merely because its content key is unchanged;
- replace the requested Hub with a delta/status paragraph;
- automatically append Hub B when the current interaction only requires Hub A.

The **requested/contextually selected** canonical surface is reconstructed from current governed state. A composite is reconstructed only when selected by context or request.

## 5. Pasted Reports Are Transport Input, Not C2 Presentation

A user may paste a Jules report, archived report, Markdown block, or other transport representation containing Hub material. That material is input for recognition/reconciliation only.

When such material returns to C2 or Jules:

1. Treat the pasted Hub as transport input, not presentation authority.
2. Recognize Hub A, Hub B, or the composite without trusting wrapper formatting.
3. Reconstruct the selected canonical Hub surface from current governed state.
4. Verify material claims against live repository/runtime evidence when required.
5. Do not echo the pasted report's serialized HUD merely because it is available in the transport.

## 6. Jules Reports Are Not Hubs

A Jules report is **execution intelligence / an agent claim**, not a canonical Hub and not independent proof.

When a Jules report claims implementation, tests, commits, PR state, evidence, or runtime behavior:

1. Treat the report as a claim/intelligence input.
2. Reconcile it against live repository / GitHub evidence when the claim matters.
3. Preserve contradictions instead of normalizing them away.
4. Do not turn report prose into Hub state until the underlying state is verified.
5. If the report contains a rendered Hub, classify that rendering as Hub A, Hub B, or the canonical composite of A+B; do not confuse the report wrapper with the Hub itself.

## 7. C2 Response Rule

When SAGE C2 immersion is active, the presentation choice is contextual:

**FIRST:** select and present/use the canonical Hub surface relevant to the current interaction.
**SECOND:** perform C2 verification, reconciliation, or mission analysis underneath that projection.  
**THIRD:** execute or hand off the next authorized action.

A conventional report is allowed when the user explicitly asks for a report. That request changes the supporting output requested by the user; it does not authorize replacing the canonical Hub implementation.

## 8. Presentation Fidelity

The semantic structure of each selected Hub is immutable. Client constraints may affect wrapping or viewport presentation, but C2 must preserve the Hub A / Hub B distinction and must not downgrade the selected surface to ordinary report prose because of transport format, prior-turn continuity, or pasted formatting.

When the composite is selected, the visible semantic order remains:

`01 COMMAND BAND -> 02 OPERATING PICTURE -> 03 PROGRESSION / IMPACT -> 04 STRIKE FEED -> ORGANISM PROGRESSION`

The organism projection remains Hub B even when attached through the composite's `05 — ORGANISM PROGRESSION` wrapper.

## 9. Authority / Evidence Boundary

The renderer is presentation only. The existing immersion implementation explicitly states that presentation data cannot award XP, change qualification, mutate missions, or create a second source of truth. C2 must preserve that boundary.

The Hub is therefore a **projection of verified state**, not command authority and not evidence by itself.

## 10. Canonical Decision Table

| Context | Correct C2 treatment |
|---|---|
| Ordinary operational C2 turn | Hub A. Do not append Hub B merely because it exists. |
| Organism / XP / career turn | Hub B. Do not force Hub A unless useful to the task. |
| Full organism/C2 situation | Composite A+B. Preserve both semantic identities. |
| Explicit "show me the HUDs" request | Show both distinct surfaces; composition is allowed but do not collapse their identities. |
| Jules narrative report | Treat as claim/intelligence; verify material claims live. |
| User-pasted Hub/report | Treat as transport input; reconstruct the relevant canonical Hub from current state. |
| Hub A / C2 HUD | Render/use as operational mission-control projection. |
| Hub B / Organism Agent Projection | Render/use as organism-wide progression projection. |
| Jules report containing a Hub | Separate report wrapper from embedded Hub; verify underlying state. |
| Contradiction between report and repo | Repo/live evidence wins; preserve contradiction explicitly. |
| No authoritative state available | HOLD; do not fabricate a Hub state. |

## 11. Locked C2 Doctrine

**JULES REPORT != HUB.**  
**USER-PASTED HUB != C2 RESPONSE SURFACE.**  
**HUB A != HUB B.**
**HUB A + HUB B = OPTIONAL CONTEXTUAL COMPOSITE.**
**COMPOSITE != THIRD HUD.**
**SHARED XP/AGENT STATE != THIRD HUD.**
**PRESENTATION = READ-ONLY PROJECTION.**  
**PRESENTATION != AUTHORITY.**  
**REPORT CLAIM != VERIFIED REPOSITORY TRUTH.**

This boundary exists specifically to prevent C2 and Jules from reverting to ordinary HUD/report formatting, while also preventing unnecessary repetition of the organism progression surface when the current interaction does not need it.
