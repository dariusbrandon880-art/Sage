# SAGE C2 HUD CANON — PERMANENT PRESENTATION LOCK

**Status:** LOCKED

This document is the permanent presentation contract for the SAGE C2 HUD. It prevents fresh sessions, agents, reports, and historical context from resurrecting obsolete HUD designs.

## Canonical dual-hub surface

### HUB A — C2 MISSION CONTROL

Hub A is the C2 Mission Control HUD / Four-Layer Operating Board.

Its layer order is permanently:

1. `01 — COMMAND BAND`
2. `02 — OPERATING PICTURE`
3. `03 — PROGRESSION / IMPACT`
4. `04 — STRIKE FEED // HIGH-TEMPO EVENTS`
5. `05 — ORGANISM PROGRESSION`

### HUB B — SAGE ORGANISM / AGENT PROJECTION

Hub B is the SAGE Organism / Agent Projection. It is the organism/progression surface and may be presented as the XP/career progression surface when the operator uses that terminology.

**There is no separate standalone XP HUD.** Do not create or resurrect one.

## Exact presentation contract

When the operator asks to rehydrate, show, present, or use the SAGE HUD, the canonical projection must preserve this exact structure:

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

05 — ORGANISM PROGRESSION
──────────────────────────────────────────
SAGE ORGANISM // AGENT PROJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<canonical organism roster>
```

The separators, headings, ordering, and semantic roles above are locked. Runtime values must come from governed state; they must never be invented merely to make the HUD look complete.

## Anti-drift rules

- The canonical Airspace/C2 renderer is the presentation authority.
- Jules reports are execution intelligence/claims, not Hub state.
- Pasted Markdown, archived transcripts, prior chat output, and transport formatting are not presentation authority.
- A fresh session must rehydrate repository/runtime truth before making live HUD claims.
- Never fall back to a remembered historical HUD because a live connection is inconvenient or unavailable.
- If canonical state cannot be established, fail closed or explicitly state what verification capability is missing.
- Never substitute a boxed dashboard, generic one-line agent HUD, standalone XP dashboard, report table, or invented ASCII surface.
- Never create a second HUD renderer or competing presentation authority.
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
