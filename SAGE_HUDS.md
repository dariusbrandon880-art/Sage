# SAGE HUDS — Canonical Rehydration Entry Point

> **HUD != state. SVG != database. Presence stays. State moves.**
>
> This file is a canonical discovery pointer for every new SAGE/C2 chat. Start here before presenting or discussing the HUDs.

## Canonical HUD surfaces

SAGE has exactly two canonical presentation surfaces:

- **Hub A — C2 Mission Control**
  - `docs/design/hud/HUB_A_C2_MISSION_CONTROL_VISUAL.svg`
  - Four-layer operational surface:
    1. `01 — COMMAND BAND`
    2. `02 — OPERATING PICTURE`
    3. `03 — PROGRESSION / IMPACT`
    4. `04 — STRIKE FEED // HIGH-TEMPO EVENTS`

- **Hub B — Organism Progression / XP Hub**
  - `docs/design/hud/HUB_B_ORGANISM_PROGRESSION_VISUAL.svg`
  - Organism projection surface:
    5. `05 — ORGANISM PROGRESSION`
    - `SAGE ORGANISM // AGENT PROJECTION`

Hub A and Hub B are distinct canonical surfaces. A contextual composite may show both; a composite is **not a third HUD**.

## Runtime doctrine

The SVGs are **locked visual/presence references only**. Their sample values are not live state and must never become a source of truth for XP, rank, points, sorties, missions, qualifications, Boss history, evidence, or readiness.

Runtime flow:

`LOCKED VISUAL PRESENCE → CURRENT GOVERNED ORGANISM / AIRSPACE STATE → CURRENT HUD RENDER`

The presence is persistent; the contents are live.

## Canonical implementation seam

The HUD presentation path is governed through:

- `sage/experimental/airspace/immersion.py`
- `sage/c2/hub_presentation_boundary.py`
- `sage/c2/chatgpt_immersion.py`
- `sage/experimental/airspace/manager.py`
- `sage/live_agent_hud.py`

Do not construct a replacement HUD from memory. Rehydrate the canonical state and render the existing surfaces.

## Rehydration rule for new chats

When a new SAGE/C2 chat needs the HUD:

1. Read this file first.
2. Retrieve the locked Hub A and Hub B visual references.
3. Select the contextual surface required by the turn.
4. Reconstruct current canonical Airspace/organism state.
5. Render current values into the same locked visual presence.
6. Never treat pasted/serialized HUD text, Jules reports, or SVG sample values as canonical state.

## Visual references

- Hub A: `docs/design/hud/HUB_A_C2_MISSION_CONTROL_VISUAL.svg`
- Hub B: `docs/design/hud/HUB_B_ORGANISM_PROGRESSION_VISUAL.svg`

## Governing invariants

- `HUB A != HUB B`
- `HUB A + HUB B = OPTIONAL CONTEXTUAL COMPOSITE`
- `COMPOSITE != THIRD HUD`
- `PRESENTATION = READ-ONLY PROJECTION`
- `PRESENTATION != AUTHORITY`
- `JULES REPORT != HUB`
- `USER-PASTED HUB != C2 RESPONSE SURFACE`
- `REPORT CLAIM != VERIFIED REPOSITORY TRUTH`
