# SAGE Flight Assignment Contract

**Status:** Governing architecture contract
**Scope:** Big Jump Wave execution slots F1-F5

## Core invariant

**F1-F5 are reusable execution slots, not permanent roles, departments, capabilities, or workflow stages.**

A flight ID identifies a temporary execution slot for one wave. C2 assigns the mission at dispatch time. The same slot may perform research, recon, build, repair, verification, governance, warehouse work, or any other authorized mission in a later wave.

## Assignment model

```text
C2 / Mission Control
        |
        +--> mission A -> F1
        +--> mission B -> F2
        +--> mission C -> F3
        +--> mission D -> F4
        +--> mission E -> F5

next wave: assignments may be completely different
```

The slot is stable; the mission is dynamic.

## Prohibited model

Do not encode or document any standing mapping such as:

- F1 = Research / Foundation
- F2 = Continuity / Intelligence
- F3 = Execution
- F4 = Governance / Verification
- F5 = Warehouse

Those labels describe possible mission types only. They are not identities of the flight slots.

## Required dispatch behavior

Every wave must provide an explicit mission assignment for each active flight slot. Mission selection must be based on the current canonical repository state, target frontier, authorization, collision boundaries, and expected capability delta.

The dispatcher must not infer a mission from the flight number.

## Independence

Flights are independent execution slots. They may be assigned any non-overlapping authorized mission in the same wave, subject to collision and governance controls. A wave may contain five different mission types, five similar mission types against separate frontiers, or any other valid composition selected by C2.

## Continuity and evidence

Receipts should bind:

- wave ID;
- flight slot ID;
- assigned mission identity;
- target frontier;
- canonical base SHA;
- execution result;
- verification evidence.

Receipts must never imply that the slot has a permanent domain.

## Anti-drift rule

Historical examples, evidence filenames, UI labels, generated reports, or prior mission assignments do not establish permanent flight roles. Current canonical governance and the explicit mission plan for the current wave are authoritative.
