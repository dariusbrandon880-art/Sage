# SAGE Live HUD Presence Contract

## Purpose

The Hub A and Hub B SVGs are **locked visual presence references**. They define the persistent interface identity and layout. They are not runtime state and must never be treated as a source of XP, rank, sortie, mission, qualification, Boss, evidence, or readiness values.

## Canonical references

- `docs/design/hud/HUB_A_C2_MISSION_CONTROL_VISUAL.svg`
- `docs/design/hud/HUB_B_ORGANISM_PROGRESSION_VISUAL.svg`

These artifacts establish the visual surface only.

## Runtime rule

Every live HUD render follows:

```text
LOCKED VISUAL PRESENCE
        ↓
CURRENT GOVERNED ORGANISM / AIRSPACE STATE
        ↓
CURRENT HUD RENDER
```

The visual surface remains stable while runtime values are refreshed from canonical state.

## Required invariants

1. **Presence is persistent.** Hub A and Hub B retain their locked visual identity and section ordering.
2. **State is live.** XP, rank, qualifications, sorties, mission state, evidence, Boss state, and readiness are populated from current governed state at render time.
3. **Reference values are not state.** Any values visible in the SVGs are illustrative visual-reference values only.
4. **No duplicate authority.** The SVGs do not become a second state store, ledger, or progression source.
5. **No stale snapshot.** A prior rendered HUD must never be reused as the source for a subsequent live HUD render.
6. **No redesign through runtime data.** Current state may change displayed values and live event content, but must not mutate the locked visual contract.
7. **HUD != authority.** Canonical state and evidence remain authoritative; the HUD is a read-only projection.

## Canonical implementation seam

The live projection belongs in the existing canonical Airspace immersion/rendering path:

- `sage/experimental/airspace/immersion.py` — live read-only HUD projection
- `sage/c2/hub_presentation_boundary.py` — Hub A / Hub B / composite surface selection
- `sage/c2/chatgpt_immersion.py` — ChatGPT-facing presentation boundary
- `sage/experimental/airspace/manager.py` — canonical reconstructed Airspace state
- `sage/live_agent_hud.py` — live HUD consumer, where applicable

Do not create a parallel HUD implementation to consume the SVGs.

## Rehydration invariant

A fresh chat must be able to recover the same visual presence and then render it against the current organism state:

```text
NEW CHAT
  → REHYDRATE
  → RETRIEVE LOCKED HUD VISUAL REFERENCES
  → SELECT HUB SURFACE
  → RECONSTRUCT CURRENT CANONICAL STATE
  → RENDER CURRENT VALUES INTO THE SAME VISUAL PRESENCE
```

The objective is continuity of **presence + current state**, not continuity of a stale screenshot or serialized HUD snapshot.
