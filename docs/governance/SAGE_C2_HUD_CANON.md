# SAGE C2 HUD CANON — PERMANENT PRESENTATION LOCK

**Status:** LOCKED

This document is the permanent presentation contract for the SAGE C2 HUD. It prevents fresh sessions, agents, reports, and historical context from resurrecting obsolete HUD designs.

## Canonical two-hub model

SAGE has **two distinct canonical presentation surfaces**:

### HUB A — C2 MISSION CONTROL

Hub A is the C2 Mission Control HUD / Four-Layer Operating Board.

Its layer order is permanently:

1. `01 — COMMAND BAND`
2. `02 — OPERATING PICTURE`
3. `03 — PROGRESSION / IMPACT`
4. `04 — STRIKE FEED // HIGH-TEMPO EVENTS`

Hub A is the normal operational C2 surface.

### HUB B — SAGE ORGANISM / AGENT PROJECTION

Hub B is the SAGE Organism / Agent Projection. It is the organism-wide identity, qualification, career/progression, and evidence-derived agent state surface. The operator may refer to this as the **XP Hub**.

There is **no separate third standalone XP HUD**. Shared XP/agent infrastructure may exist underneath Hub B, but it must not become another canonical visual HUD.

## Contextual visibility rule

Hub A and Hub B are independent surfaces even when they are rendered together.

- **Hub A only:** normal mission-control / operational work.
- **Hub B only:** organism, XP, rank, career, agent-progression, or related work.
- **Hub A + Hub B:** allowed when the full organism/C2 picture is useful or explicitly requested.
- A composite is a **contextual presentation choice**, not a new HUD and not a requirement to repeat both surfaces every response.
- The existence of Hub B does **not** require Hub B to be repeated on every C2 turn.
- Shared XP, career, rank, boss, and agent-state projections may feed either surface without creating a third presentation authority.
- Visibility is contextual; canonical state remains shared and governed.

This rule is intentional game-developer design: the player/operator should receive the information needed for the current loop, challenge, and decision rather than being forced to repeatedly consume every progression surface. Clear goals, visible progress, immediate feedback, and meaningful challenge are more important than mechanically displaying every reward layer on every turn. citeturn0search1turn0search5

## Composite presentation

When Hub A and Hub B are composed, the semantic boundary remains intact:

```text
HUB A — C2 MISSION CONTROL
01 — COMMAND BAND
02 — OPERATING PICTURE
03 — PROGRESSION / IMPACT
04 — STRIKE FEED

HUB B — SAGE ORGANISM / AGENT PROJECTION
SAGE ORGANISM // AGENT PROJECTION
<canonical organism roster>
```

The composite may use the existing `05 — ORGANISM PROGRESSION` wrapper when rendered inside the canonical Four-Layer C2 board. That wrapper does **not** turn Hub B into a fifth operational layer of Hub A; it is the attachment point for the separate organism projection.

## Exact Hub A presentation contract

When Hub A is requested, preserve this structure:

```text
01 — COMMAND BAND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL
STATUS   : <runtime status>
QUAL     : <CQL> | <SQL>
MISSION  : <runtime mission>

02 — OPERATING PICTURE
──────────────────────────────────────────
ACTIVE SORTIES: <runtime sorties>

03 — PROGRESSION / IMPACT
──────────────────────────────────────────
TOTAL SYSTEM XP : <runtime total>
 ▪ MISSION_DIRECTOR XP <runtime>     CQL <stack>  SQL <stack>
 ▪ MISSION_CONTROL XP <runtime>     CQL <stack>  SQL <stack>
 ▪ INTEL_STATION XP <runtime>       CQL <stack>  SQL <stack>
 ▪ ENGINEERING_FLIGHT XP <runtime>  CQL <stack>  SQL <stack>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
04 — STRIKE FEED // HIGH-TEMPO EVENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<canonical strike-feed events>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Exact Hub B presentation contract

When Hub B is requested independently, preserve its identity as a separate organism surface:

```text
SAGE ORGANISM // AGENT PROJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<canonical organism roster>
```

Runtime values must come from governed state; they must never be invented merely to make the HUD look complete.

## Anti-drift rules

- The canonical Airspace/C2 renderer is the presentation authority.
- Jules reports are execution intelligence/claims, not Hub state.
- Pasted Markdown, archived transcripts, prior chat output, and transport formatting are not presentation authority.
- A fresh session must rehydrate repository/runtime truth before making live HUD claims.
- Never fall back to a remembered historical HUD because a live connection is inconvenient or unavailable.
- If canonical state cannot be established, fail closed or explicitly state what verification capability is missing.
- Never substitute a boxed dashboard, generic one-line agent HUD, standalone XP dashboard, report table, or invented ASCII surface.
- Never create a second HUD renderer or competing presentation authority.
- Shared XP/agent projection helpers are permitted when they are underlying state/projection infrastructure and are not presented as a competing canonical C2 HUD.
- The deleted `sage/agent_hud_projection.py` is obsolete and must not be recreated.
- Changes to this contract require explicit Mission Director authorization.

## Canonical implementation

The contract is implemented through:

- `sage/experimental/airspace/renderer.py`
- `sage/experimental/airspace/immersion.py`
- `sage/experimental/airspace/organism_projection.py`
- `sage/c2/immersion_projection.py`
- `sage/c2/chatgpt_immersion.py`
- `sage/c2/chatgpt_c2_contract.py`
- `sage/c2/hub_presentation_boundary.py`

This document is a governance lock, not a replacement renderer.
