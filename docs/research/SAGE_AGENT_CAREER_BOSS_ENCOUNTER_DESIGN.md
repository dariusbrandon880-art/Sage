# SAGE Agent Career — Boss Encounter Design

**Status:** DESIGN CANDIDATE / RESEARCH-LOCKED / IMPLEMENTATION HOLD  
**Date:** 2026-09-02  
**Scope:** Agent Career / Rank / Progression — Boss Encounter, Elite Capture, and Elite Kill model  
**Authority:** Mission Director-approved design exploration; repository architecture remains authoritative. This document does not by itself authorize protected architecture changes.

## 1. Core Idea

SAGE career progression should model exceptional milestones as **Boss Encounters**, not merely as XP thresholds.

A Boss is a meaningful challenge that tests demonstrated capability and creates a recognizable closure point in an agent's career progression.

```text
REAL VERIFIED WORK
        ↓
MISSIONS / SORTIES
        ↓
   BOSS ENCOUNTER
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
SMALL  BIG   MAJOR
BOSS   BOSS   BOSS
        ↓
 VERIFIED OUTCOME
        ↓
 ┌──────┴──────┐
 ▼             ▼
KILL          CAPTURE
│             │
obstacle      capability
eliminated    secured
        ↓
 VERIFIED CAREER EVENT
        ↓
 POINTS / XP / QUALIFICATION / BADGE
```

## 2. Boss Is an Encounter, Not a Currency

A Boss must not simply mean “worth X XP.”

The Boss represents a **difficulty-bearing challenge**. Its value is established through the verified characteristics of the encounter and its outcome.

```text
Boss = meaningful challenge
XP   = career accounting consequence
Rank = persistent career state
CQL/SQL = formal capability qualification
Badge = verified distinction
```

This preserves the separation established in the historical career recon.

## 3. Why Bosses Fit SAGE

Game-design research commonly treats bosses as milestone tests: they close a progression segment, test mastery, and create a meaningful transition point. Boss encounters can also be structured as multi-phase tests rather than a single undifferentiated difficulty value. citeturn0search0turn0search8

The SAGE translation is not literal combat. The boss is a **governed challenge representation** over real work.

```text
GAME:       learn → engage → defeat boss → unlock progress
SAGE:       discover → bound → execute → verify → overcome → capture capability
```

## 4. Boss Classes

### Small Boss

A bounded but non-trivial challenge that requires demonstrated competence beyond routine work.

Examples:

- difficult defect elimination
- contained integration obstacle
- meaningful recon target
- first successful demonstration of a capability
- bounded verification challenge

### Big Boss

A substantial challenge requiring multiple capabilities, sorties, evidence artifacts, or coordinated work.

Examples:

- subsystem-level capability delivery
- multi-stage integration problem
- difficult qualification challenge
- significant frontier advancement
- reusable capability brought into the fleet

### Major Boss

A frontier-level or system-significant challenge whose verified outcome materially expands SAGE capability or removes a major structural obstacle.

Examples:

- major runtime/control-plane breakthrough
- high-impact reusable capability
- difficult multi-agent coordination challenge
- major frontier breakthrough
- elimination of a persistent high-impact failure mode

**Important:** Small/Big/Major are difficulty classes, not automatic XP amounts.

## 5. Boss Outcomes

### Elite Kill

A verified Boss outcome where the primary accomplishment is **eliminating an obstacle, threat, blocker, defect, or failure mode**.

```text
BOSS → ENGAGE → VERIFY → KILL
```

Examples:

- blocker eliminated
- defect eliminated
- regression source eliminated
- security/control failure mode eliminated
- frontier obstacle overcome

### Elite Capture

A verified Boss outcome where the primary accomplishment is **securing a capability, qualification, intelligence finding, or reusable asset**.

```text
BOSS → ENGAGE → VERIFY → CAPTURE
```

Examples:

- capability captured
- qualification achieved
- reusable component secured
- validated intelligence captured
- new frontier capability established

A Boss may produce both a Kill and a Capture when the verified outcome supports both.

## 6. Boss Phases

A Boss can contain phases. Phases are progression semantics, not a new authority system.

Candidate phase model:

```text
BOSS ENCOUNTER
      ↓
DISCOVER
      ↓
BOUND
      ↓
ENGAGE
      ↓
BREAKTHROUGH
      ↓
VERIFY
      ↓
CAPTURE / KILL
```

This intentionally echoes SAGE's existing governed continuous-intelligence loop rather than inventing a disconnected game lifecycle.

Multi-phase boss design is useful because individual phases can test different capabilities and provide meaningful progression beats. citeturn0search8turn0search9

## 7. No Fake Health Bars

A Boss must **not** receive arbitrary “health,” “damage,” or progress values solely for presentation.

Any boss progress projection must be derived from canonical evidence/state.

```text
CANONICAL STATE / EVIDENCE
          ↓
BOSS PROJECTION
          ↓
HUD / NAMEPLATE / CHAT
```

Never:

```text
HUD / CHAT
   ↓
invent boss damage
   ↓
claim kill
```

This preserves the existing SAGE immersion rule: presentation is downstream of canonical state.

## 8. Boss Difficulty Profile

The Boss class should eventually be derived from a structured difficulty profile rather than a subjective label.

Candidate dimensions:

- capability breadth
- capability depth
- dependency complexity
- uncertainty
- verification burden
- failure severity
- reuse/impact
- coordination requirement
- frontier distance

These are design candidates, not locked scoring rules.

## 9. Career Economy

The Boss is not the XP economy itself.

```text
BOSS ENCOUNTER
      ↓
VERIFIED OUTCOME
      ↓
QUALIFIED PERFORMANCE
      ↓
POINTS
      ↓
XP CONVERSION
      ↓
CAREER XP
      ↓
RANK PROGRESS / ELIGIBILITY
```

Qualification and promotion remain separate gates.

```text
XP → eligibility
QUALIFICATION + EVIDENCE + CAPABILITY → promotion decision
PROMOTION GATE → PROMOTE / HOLD
```

This prevents Boss farming from becoming a shortcut to rank.

## 10. Bosses Should Be Persistent Career Objects

A Boss should be capable of existing across multiple sorties when the challenge is genuinely multi-stage.

```text
BOSS CREATED
    ↓
ENGAGED
    ↓
PARTIALLY ADVANCED
    ↓
BLOCKED / RECOVERED / RE-ENGAGED
    ↓
VERIFIED
    ↓
DEFEATED / CAPTURED
    ↓
CLOSED
```

Failed attempts should remain evidence/history rather than disappearing when the Boss is eventually defeated.

This aligns with SAGE's existing persistence, append-only evidence/event, and failure-memory direction.

## 11. Bosses Are Not Five Flights

Boss encounters must not redefine the Five-Flight operating model.

```text
F1–F5 = reusable execution vehicles
BOSS   = challenge object
RANK   = persistent career state
```

A Boss can require one flight or several flights. A flight can participate in many different Boss encounters. No permanent mapping exists between flight identity and Boss category.

## 12. Boss Rewards / Consequences

Candidate post-Boss consequences include:

- verified Points
- career XP
- CQL/SQL qualification evidence
- mastery evidence
- verification badges
- reusable capability registration
- roster/nameplate progression
- promotion eligibility
- chapter/frontier progression

These are consequences of verified outcomes, not automatic rewards for merely reaching a Boss.

## 13. Boss Farming Constraint

A Boss should not be repeatable for unlimited career gain simply because the event can be replayed.

Repeated work must produce additional progression only when it creates additional verified capability, impact, qualification, or materially new evidence.

```text
REPEAT EVENT ≠ AUTOMATIC XP

NEW VERIFIED VALUE → progression consequence
NO NEW VERIFIED VALUE → no artificial career inflation
```

This directly addresses known progression-system failure modes where repetitive activity can be farmed for guaranteed XP.

## 14. Proposed Career World

```text
                    SAGE CAREER WORLD
                           │
                    REAL VERIFIED WORK
                           │
                     SORTIES / MISSIONS
                           │
                           ▼
                    BOSS ENCOUNTERS
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           SMALL          BIG         MAJOR
           BOSS           BOSS          BOSS
              │            │            │
              └────────────┼────────────┘
                           ▼
                    VERIFIED OUTCOME
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  ELITE         ELITE
                   KILL         CAPTURE
                    │             │
                    └──────┬──────┘
                           ▼
                    CAREER ACCOUNTING
                    ├── POINTS
                    ├── XP
                    ├── QUALIFICATION
                    ├── MASTERY
                    └── BADGES
                           ↓
                    PROMOTION GATE
                    ├── PROMOTE
                    └── HOLD
                           ↓
                    SHARED AGENT ROSTER
                           ↓
                    IMMERSION / HUD / CHAT
```

## 15. Design Lock

The following are now design findings for the Career Boss concept:

- Milestones can be represented as Boss Encounters.
- Small, Big, and Major represent challenge tiers, not fixed XP payouts.
- A Boss is a test of demonstrated capability and a progression closure point.
- Elite Kill means verified elimination of a meaningful obstacle.
- Elite Capture means verified acquisition/establishment of a meaningful capability, qualification, intelligence result, or reusable asset.
- Boss outcomes must be evidence-backed.
- Boss progress must be projected from canonical state/evidence; no fake health bars or invented damage.
- Bosses may span multiple sorties and retain failure/attempt history.
- Bosses are not Five-Flight identities or career classes.
- Bosses feed career accounting; they do not replace XP, qualification, mastery, rank, or promotion gates.
- Repeated Boss work must not create automatic career inflation without new verified value.

## 16. Still Open

Not locked:

- exact Boss schema
- exact difficulty calculation
- exact phase schema
- exact Small/Big/Major thresholds
- exact Points/XP consequences
- Boss creation authority
- Boss closure authority
- repeat/retry policy
- team/shared Boss ownership rules
- Boss rewards
- chapter/frontier relationships
- UI/HUD presentation

## 17. Implementation Boundary

**Do not create a parallel game engine.**

Before implementation, reconcile this model against current `main` canonical structures for:

- mission/sortie lifecycle
- event ledger
- evidence schemas
- qualification registries
- progression receipts
- fleet state
- promotion/authority gates
- roster/nameplate projections
- current C2 transition and rendering boundaries

The first implementation should be the smallest governed primitive that can represent a real Boss Encounter using existing SAGE authority and evidence paths.
