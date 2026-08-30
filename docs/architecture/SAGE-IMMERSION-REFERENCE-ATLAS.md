# SAGE Immersion Reference Atlas

**Status:** DESIGN / IMPLEMENTATION GUIDANCE / NOT A SECOND SOURCE OF TRUTH

## Purpose

Turn external game and mission-control research into small, additive presentation patterns for the existing SAGE workflow.

**ChatGPT is the interface. SAGE remains the governed mission-control system.**

External references are inspiration only. They do not define SAGE identity, authority, progression, or truth.

## Reference split

### Slot-machine references — borrow the progression grammar

- **Wolf Run:** stacked/repeated symbols make accumulation visually obvious.
  - SAGE use: compact stacked qualification/capability glyphs.
- **Buffalo:** collection accumulates toward a threshold and can transform the visible state.
  - SAGE use: verified collection -> governed threshold -> qualification transformation.
- **Panda-family:** visible completion/trigger sequences and expanding states create anticipation and a stronger reveal.
  - SAGE use: real gate completion -> higher-salience mission-control reveal -> bounded next frontier.
- **Sticky/expanding bonus patterns:** earned symbols persist and the visible field becomes richer.
  - SAGE use: durable qualification marks and capability history projected from canonical state.

### Military / aerospace / NASA references — borrow the operational frame

- mission-control language;
- mission phase / objective presentation;
- live status and telemetry-like indicators;
- explicit active / standby / blocked / failed / verified states;
- positive acknowledgement of meaningful actions;
- compact operational symbology;
- flight / sortie / readiness vocabulary;
- debrief and recovery transitions;
- persistent earned patches / ribbons / qualifications.

NASA human-system guidance is especially useful for the boundary that operators should be able to distinguish current, stale, missing, and unknown information and should receive clear acknowledgement for actions. SAGE applies that principle without copying NASA branding.

## SAGE presentation recipe

The normal ChatGPT response remains conversational, but SAGE-directed responses should expose a compact operational frame:

1. **Nameplate** — `[SAGE::C2::CHATGPT] C2 Mission Control`
2. **Mode** — one or two small symbols that match the actual work: `🧠 C2`, `✈️ Flight`, `🔎 Recon`, `🔧 Build`, `🛡️ Verify`, `🧩 Architecture`, `🏭 Warehouse`, `🔬 Research`.
3. **Current mission state** — what is actually happening now.
4. **Real event** — the latest meaningful change.
5. **Progression projection** — a small earned tag/stack/ribbon/frontier movement if canonical state supports it.
6. **Next gate** — the next evidence-bearing condition.
7. **Truth boundary** — only when needed: distinguish candidate, active, verified, blocked, or unverified.

Do not turn every answer into a dashboard. The immersion layer should be **small, persistent, and adaptive**.

## Core visual behaviors

### Stack

`🔧 BUILD  🔧 BUILD  🔧 BUILD`

Means repeated verified progression, not three arbitrary cosmetic points.

### Collect

`🛰️ 2  🔧 3  🛡️ 1`

Means real earned activity/capability accumulation from canonical sources.

### Transform

`🔧 BUILD  ->  ⚙️ ENGINEERING QUALIFIED`

Only after the governed qualification condition is actually satisfied.

### Stick

Once earned, a qualification tag can remain visible in later responses when the current rehydrated state still contains it.

### Expand

`CORE -> FRONTIER -> NEW QUALIFIED NODE`

A newly visible node represents newly exposed capability space. It does not authorize execution by itself.

### Reveal

A Milestone Strike or other verified progression event can receive a stronger visual treatment because the underlying system already has evidence/validation semantics.

## Response pacing

Borrow the satisfying rhythm of game feedback without copying gambling behavior:

**notice -> acknowledge -> reveal -> settle -> next objective**

Example:

`🛡️ VERIFICATION`

`immersion projection tests passed`

`🏷️ IMMERSION PROJECTION QUALIFIED`

`⭐ +1 verified progression`

`NEXT GATE -> frontier integration`

The response should not spam animations, fake counters, or invented rewards.

## Failure pacing

Failure should also have a readable operational rhythm:

`⚠️ GATE FAILED`

`evidence captured`

`no progression awarded`

`repair frontier -> ACTIVE`

The user should immediately understand what happened and what the machine is doing next.

## Design laws

1. **Real event -> canonical state change -> immersion projection.**
2. Never use immersion to manufacture achievement.
3. ChatGPT is the interface; do not create a competing conversational surface.
4. Military/aerospace/NASA language is the native tone; casino references remain invisible as branding.
5. Keep the immersion surface compact enough to coexist with normal conversation.
6. Persistent visual state must come from durable canonical state.
7. A visual mark cannot authorize, qualify, promote, or mutate anything.
8. Do not create a second XP/progression ledger.
9. Candidate mechanics remain Design Lab material until validated.
10. Cross-chat rehydration must restore the immersion contract automatically whenever SAGE repository truth is available.

## Research references

- NASA, *Crew Interfaces* / human-system interface guidance: https://www.nasa.gov/reference/10-0-crew-interfaces-vol-2/
- NASA, *All Systems Go Imagery Toolkit*: https://www.nasa.gov/mission-all-systems-go-imagery-toolkit/
- Slot-mechanics research used for the design study: stacked symbols, collection/thresholds, sticky symbols, expanding reels, and bonus triggers.

These references inform design hypotheses only. SAGE's repository contracts and validated state remain authoritative.
