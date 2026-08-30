# SAGE Immersion Language — Design Lab Expansion

**Status:** DESIGN LAB / FIRST PROJECTION PROTOTYPE IMPLEMENTED / NOT CANONICAL

**Purpose:** Capture and prototype the expanded immersion direction before promotion into canonical governance. Casino and video-game references are inspiration only. The implementation is a read-only projection over existing SAGE state and does not create authority, progression, XP, qualification, or mission state.

## 1. Core Direction

SAGE remains a governed mission-control system. **ChatGPT is the interface.** Military / aerospace / NASA-style operational language is the native visual and tonal frame.

Casino-machine and video-game references supply interaction and feedback patterns only. Borrow mechanics, not identities; feedback patterns, not branding; progression feel, not gambling behavior.

The governing rule is:

> **Real SAGE event → canonical state change → immersion projection. Never immersion → assumed achievement → canonical state.**

The immersion layer must remain read-only with respect to truth-bearing state.

## 2. Reference Mechanics → SAGE Possibilities

The reference class is actual progression behavior from machines such as Wolf Run, Buffalo, and Panda-family games. The implementation translates those patterns into SAGE mission-control semantics.

### Wolf Run — stacking

Borrow: repeated / stacked symbols that make accumulation immediately visible.

SAGE translation:
- verified qualification levels render as compact stacked capability glyphs;
- the stack visibly grows as canonical qualification grows;
- no visual stack can imply an unearned qualification.

### Buffalo — collect → threshold → transformation

Borrow: collected symbols accumulate until a threshold causes a visible transformation.

SAGE translation:
- evidence-backed progress can accumulate in existing canonical progression;
- governed qualification thresholds transform ordinary progression into persistent qualification marks;
- the transformation is an effect of verified state, never its source.

### Panda — completion / trigger / expansion

Borrow: visible collection toward a named trigger and an expanded state after the trigger.

SAGE possibility:
- a capability can expose real gates as a completion sequence;
- completion can trigger a higher-salience mission-control presentation;
- a newly qualified capability can expose additional bounded frontier space.

### Panda-family — sticky / expanding behavior

Borrow: earned symbols persist and the visual field becomes richer.

SAGE translation:
- canonical qualification marks remain visible;
- later sessions can project the same earned marks from durable state;
- no client-side decoration becomes persistent truth.

## 3. Military / Aerospace / NASA Translation

The reference mechanics supply **how progression feels**. Existing SAGE military/aerospace language supplies **what the experience looks and sounds like**.

Operational primitives:
- mission patches / qualification marks
- aircraft / spacecraft / station glyphs
- sortie and flight indicators
- readiness states
- mission phase markers
- telemetry-style status indicators
- objective markers
- rank / qualification presentation
- ribbons / earned distinctions
- squadron / flight identity
- launch / recovery / debrief transitions
- alert / hold / blocked / verified states
- command-center panels
- small persistent operational icons

These remain consistent with existing SAGE terminology and architecture.

## 4. First Implemented Projection Layer

**Implementation:** `sage/experimental/airspace/immersion.py`

The first prototype is deliberately thin and read-only. It consumes `AirspaceState` and projects:

- canonical CQL/SQL progression as stacked capability glyphs;
- qualification labels as persistent capability tags;
- sortie states as live mission-control glyphs;
- an immersion nameplate combining existing identity, XP, qualification, stack, and live sortie state.

No new persistence or authority is introduced.

## 5. Living Nameplates

The nameplate is the primary lightweight immersion surface.

A nameplate can show, from canonical state:

- station / agent identity
- role
- CQL / SQL
- XP
- active mission / frontier when available
- current operational state
- earned capability tags
- qualification marks
- Milestone Strike stars when legitimately earned
- small persistent mission glyphs

The first implementation adds the capability stack and live sortie strip without changing the existing canonical identity API.

## 6. Capability Collection

Create the concept of a visual collection of already-earned SAGE capabilities.

Candidate categories:

- Recon
- Intelligence
- Engineering
- Verification
- Architecture Guard
- C2 Coordination
- Recovery
- Provenance
- Rehydration
- Frontier Exploration
- Warehouse Contribution

The collection can grow visually over time and support persistent identity without becoming a second ledger.

## 7. Capability Completion / Spelling

A later projection can expose a capability's real progression as a sequence of governed gates.

Example:

`R E H Y D R A T I O N`

Each position is filled only by a real evidence-backed condition. Completion reveals the qualified capability.

This remains a candidate until the relevant canonical gate source is wired explicitly.

## 8. Sticky Progression

Candidate sticky elements:

- earned qualification tags
- mission ribbons
- verified capability icons
- completed frontier nodes
- Milestone Strike stars
- persistent station distinctions

Persistence must come from existing canonical state / archive mechanisms.

## 9. Stacked Progression

The first implementation makes stacked progression concrete through `render_capability_stack()`.

Example:

`CQL ⚙️⚙️⚙️⚙️  SQL 🛰️🛰️🛰️`

The stack is derived from current canonical qualification levels. It cannot award XP or qualification.

## 10. Transformation Events

A later projection can render high-salience transformations after verified completion.

Examples:

- `🔧 BUILD` → `⚙️ ENGINEERING QUALIFIED`
- `🛰️ RECON` → `📡 INTELLIGENCE QUALIFIED`
- `🛡️ VERIFY` → `🏅 VALIDATION QUALIFIED`
- `✈️ SORTIE` → `⭐ MILESTONE STRIKE`

The transformation must be triggered only by canonical state.

## 11. Expanding Frontier

Borrow the feeling of a playfield opening as progression occurs.

SAGE possibility:

```text
CORE
 ├─ RECON              🟢
 ├─ PROVENANCE         🟢
 ├─ IMMERSION          🟡 ACTIVE
 ├─ AUTONOMOUS C2      🔒
 └─ NEXT FRONTIER      🔒
```

The visual expansion represents newly visible capability space; it does not authorize work by itself.

## 12. Ribbons / Patches / Distinctions

Borrow military-game recognition systems.

Candidate earned distinctions:

- First Flight
- Evidence Discipline
- Recovery Specialist
- Cross-Station Qualified
- Frontier Explorer
- Architecture Guardian
- Five-Flight Coordinator
- Provenance Guardian
- Rehydration Qualified

These must be derived from real qualification criteria and existing progression mechanisms.

## 13. Live Mission-State Feedback

The first implementation provides sortie-state glyphs:

`CREATED → BRIEFED → CLEARED → ✈️ ACTIVE → 🛡️ EVIDENCE_CAPTURE → ⭐ VERIFIED`

Interrupted states remain explicit:

`⛔ BLOCKED` / `⚠️ FAILED` / `↩ ABORTED`

The interface can acknowledge meaningful transitions quickly while preserving mission-control semantics.

## 14. Failure Can Be Visually Meaningful

Failure should not look like a generic dead end.

Candidate presentation:

`⚠️ GATE FAILED`

`FAILURE CLASS: AUTO-LOCK / REHYDRATION`

`NEGATIVE KNOWLEDGE CAPTURED`

`REPAIR FRONTIER CREATED`

The failure receives no progression award merely because it was displayed.

## 15. Milestone Strike as the Major Reveal

A Milestone Strike can serve as the strongest visual reward because it already represents verified advancement.

Candidate presentation:

`⭐ MILESTONE STRIKE`

`CAPABILITY: CROSS-STATION PROVENANCE`

`EVIDENCE ✓`
`VERIFICATION ✓`
`VALIDATION ✓`
`PROMOTION ✓`

The presentation remains downstream of the verified progression system.

## 16. Live World Feeling

The central immersion property is visible environmental consequence.

A real event can update several already-existing views:

`real event`

→ mission state changes
→ nameplate changes
→ capability marker changes
→ progression changes
→ frontier view changes
→ flight / station status changes
→ next objective becomes visible

The implementation should grow this incrementally rather than introduce a separate game engine.

## 17. Design Boundaries

Do not add:

- gambling mechanics as actual system logic;
- random rewards that imply earned capability;
- fake XP;
- fake qualification;
- visual authority independent of canonical state;
- a second source of truth;
- casino branding as SAGE identity;
- unnecessary game-engine architecture;
- progression that can be manipulated by presentation code.

## 18. Candidate Architecture

```text
CANONICAL SAGE STATE
        ↓
EVENT / PROGRESSION INTERPRETATION
        ↓
IMMERSION PROJECTION
   ├─ nameplate
   ├─ tags
   ├─ stacks
   ├─ capability collection
   ├─ ribbons / patches
   ├─ frontier expansion
   ├─ mission-state feedback
   └─ milestone reveal
        ↓
CHATGPT INTERFACE
```

The immersion layer must not write truth-bearing state.

## 19. Current Prototype Boundary

Implemented now:

- stacked CQL/SQL progression glyphs;
- canonical qualification tags;
- sortie-state glyphs;
- live sortie strip;
- composite immersion nameplate;
- read-only tests proving the projection does not mutate AirspaceState.

Next implementation candidates:

1. capability completion / spelling sequence driven by explicit canonical gates;
2. sticky qualification collection from promotion history;
3. verified transformation events;
4. military-style ribbons / patches derived from governed qualification events;
5. frontier expansion projection from existing frontier state;
6. Milestone Strike reveal integration using the existing validated impact source.

## 20. Promotion Gate

This document remains a design-lab artifact until the candidate mechanics and prototype are reviewed against the existing immersion, progression, persistence, Airspace, mission-control, and governance contracts.

The prototype demonstrates presentation behavior only. It does not make any item canonical merely because it appears here.
