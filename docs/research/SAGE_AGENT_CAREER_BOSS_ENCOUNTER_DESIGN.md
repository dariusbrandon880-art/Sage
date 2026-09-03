# SAGE Agent Career — Boss Encounter Design

**Status:** DESIGN CANDIDATE / RESEARCH-LOCKED / IMPLEMENTATION HOLD  
**Date:** 2026-09-02  
**Scope:** Agent Career / Rank / Progression — Boss Encounter, Elite Capture, and Elite Kill model  
**Authority:** Mission Director-approved design exploration; repository architecture remains authoritative. This document does not by itself authorize protected architecture changes.

## 1. Core Idea

SAGE career progression should model exceptional milestones as **Boss Encounters**, not merely as XP thresholds.

A Boss is a meaningful challenge that tests demonstrated capability and creates a recognizable closure point in an agent's career progression.

```text
REAL VERIFIED WORK → MISSIONS / SORTIES → BOSS ENCOUNTER
                                      ↓
                              BIG / MAJOR BOSS
                                      ↓
                              VERIFIED OUTCOME
                               ↙             ↘
                            KILL          CAPTURE
                               ↘             ↙
                         POINTS / XP / QUALIFICATION / BADGE
```

## 2. Boss Is an Encounter, Not a Currency

A Boss must not simply mean “worth X XP.” The Boss represents a **difficulty-bearing challenge**. Its value is established through verified characteristics of the encounter and its outcome.

```text
Boss = meaningful challenge
XP   = career accounting consequence
Rank = persistent career state
CQL/SQL = formal capability qualification
Badge = verified distinction
```

## 3. Why Bosses Fit SAGE

Bosses are milestone tests: they close progression segments, test mastery, and can contain multiple phases. SAGE translates that pattern into a governed challenge representation over real work.

```text
GAME: learn → engage → defeat boss → unlock progress
SAGE: discover → bound → execute → verify → overcome → capture capability
```

## 4. Boss Classes

### Big Boss

A substantial challenge requiring multiple capabilities, sorties, evidence artifacts, or coordinated work.

Examples include subsystem capability delivery, multi-stage integration, difficult qualification, significant frontier advancement, and reusable capability brought into the fleet.

### Major Boss

A frontier-level or system-significant challenge whose verified outcome materially expands SAGE capability or removes a major structural obstacle.

Examples include major runtime/control-plane breakthroughs, high-impact reusable capabilities, difficult multi-agent coordination, major frontier breakthroughs, and elimination of persistent high-impact failure modes.

**Big/Major are difficulty classes, not automatic XP amounts. No additional Boss tier is defined by this contract.**

## 5. Boss Outcomes

### Elite Kill

A verified Boss outcome where the primary accomplishment is **eliminating an obstacle, threat, blocker, defect, or failure mode**.

### Elite Capture

A verified Boss outcome where the primary accomplishment is **securing a capability, qualification, intelligence finding, or reusable asset**.

A Boss may produce both a Kill and a Capture when the verified outcome supports both.

## 6. Boss Phases

Candidate phase model:

```text
BOSS ENCOUNTER → DISCOVER → BOUND → ENGAGE → BREAKTHROUGH → VERIFY → CAPTURE / KILL
```

Phases are progression semantics, not a new authority system. A Boss may span multiple sorties.

## 7. No Fake Health Bars

A Boss must **not** receive arbitrary “health,” “damage,” or progress values solely for presentation. Any Boss progress projection must be derived from canonical evidence/state.

```text
CANONICAL STATE / EVIDENCE → BOSS PROJECTION → HUD / NAMEPLATE / CHAT
```

Presentation cannot invent damage or claim a kill.

## 8. Boss Difficulty Profile

Candidate dimensions for eventual structured classification:

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

## 8A. Emergent Boss Classification Model

The Boss classification model is **emergent and retrospective**. SAGE should classify a Boss from the verified shape of real organism execution rather than declaring a tier solely from a task title, planned ticket size, expected XP, diff size, runtime, or other activity proxy.

```text
REAL ORGANISM EXECUTION
        ↓
VERIFIED EVENT / EVIDENCE HISTORY
        ↓
ENCOUNTER FEATURE PROFILE
        ├─ capability breadth
        ├─ capability depth
        ├─ dependency / integration complexity
        ├─ uncertainty / discovery load
        ├─ verification burden
        ├─ failure severity / recovery burden
        ├─ reuse / system impact
        ├─ coordination requirement
        └─ frontier distance
        ↓
EMERGENT CLASSIFICATION
        ├─ BIG BOSS
        └─ MAJOR BOSS
        ↓
GOVERNED VERIFICATION
        ↓
CANONICAL BOSS OUTCOME
```

### 8A.1 Classification Principle

The Boss class is an **evidence-backed conclusion about the encounter**, not an input that can manufacture its own evidence.

```text
PLAN / INTENT       → candidate
EXECUTION           → observations
VERIFIED EVIDENCE   → classification basis
GOVERNED REVIEW     → Boss class
CANONICAL OUTCOME   → career accounting
```

A planned task may be a provisional candidate, but final classification remains provisional until sufficient verified evidence exists.

### 8A.2 Emergence From Multiple Signals

No single dimension automatically creates a Major Boss. Classification emerges from the **joint profile** of the verified encounter plus its material verified consequence.

A **Big Boss** is indicated when an encounter demonstrates substantial difficulty across material dimensions and produces a meaningful verified outcome.

A **Major Boss** is indicated when the verified encounter demonstrates system-significant or frontier-level difficulty, impact, uncertainty, coordination, or structural consequence, with evidence showing that the outcome materially expands capability or removes a major obstacle.

```text
ONE LARGE NUMBER ≠ AUTOMATIC MAJOR

MULTI-DIMENSIONAL VERIFIED PROFILE
              +
       MATERIAL OUTCOME
              ↓
      EMERGENT BOSS CLASS
```

Exact weighting, normalization, and thresholds remain HOLD until sufficient real execution history exists for calibration.

### 8A.3 Retrospective Evidence Requirement

Classification must be reconstructable from the evidence trail. A reviewer should be able to determine:

1. what work actually occurred;
2. what dependencies, uncertainty, and coordination were encountered;
3. what failure/recovery burden was present;
4. what capability or obstacle changed;
5. what evidence verifies the outcome; and
6. why the observed profile supports Big versus Major.

If the record cannot support the classification, the encounter remains **unclassified / provisional** rather than being promoted by presentation pressure.

### 8A.4 Anti-Gaming Rules

The emergent model must not reward artificial complexity:

- unnecessary subtasks do not increase Boss class;
- evidence volume alone does not increase Boss class;
- repeated work does not increase Boss class without new verified value;
- large diffs, high token counts, and long runtimes are not Boss signals by themselves;
- Points or XP awarded cannot prove that an encounter was a Boss;
- UI presentation cannot promote an encounter to Boss status;
- a declared Boss label cannot substitute for canonical evidence.

The model measures **observed difficulty and verified consequence**, not activity theater.

### 8A.5 Classification Confidence and Hold State

Until evidence is sufficient, preserve a governed hold state instead of forcing a classification.

```text
PROVISIONAL
    ↓
EVIDENCE SUFFICIENT?
  ┌───┴───┐
  NO     YES
  ↓       ↓
HOLD   CLASSIFY
          ├─ BIG
          └─ MAJOR
```

A future confidence/evidence-completeness measure must derive from canonical evidence and must not become a hidden third Boss tier.

### 8A.6 Learning Loop

Emergent classification improves through observed history:

```text
CLASSIFY → VERIFY → ARCHIVE → OBSERVE MORE ENCOUNTERS
                         ↓
                 COMPARE OUTCOMES
                         ↓
                 RECALIBRATE MODEL
```

Historical classifications remain auditable. Recalibration must never rewrite the underlying append-only event ledger.

**Current lock:** the emergent classification principle is adopted as the research direction. Exact feature weights, thresholds, normalization, confidence math, and automatic classification authority remain **HOLD** pending sufficient real organism execution history.

## 9. Career Economy

The Boss is not the XP economy itself.

```text
BOSS ENCOUNTER → VERIFIED OUTCOME → QUALIFIED PERFORMANCE → POINTS → XP CONVERSION → CAREER XP → RANK PROGRESS / ELIGIBILITY
```

Qualification and promotion remain separate gates:

```text
XP → eligibility
QUALIFICATION + EVIDENCE + CAPABILITY → promotion decision
PROMOTION GATE → PROMOTE / HOLD
```

Boss farming must not become a shortcut to rank.

## 10. Bosses Should Be Persistent Career Objects

A Boss may exist across multiple sorties when genuinely multi-stage:

```text
BOSS CREATED → ENGAGED → PARTIALLY ADVANCED → BLOCKED / RECOVERED / RE-ENGAGED → VERIFIED → DEFEATED / CAPTURED → CLOSED
```

Failed attempts remain evidence/history rather than disappearing when the Boss is defeated.

## 11. Bosses Are Not Five Flights

```text
F1–F5 = reusable execution vehicles
BOSS   = challenge object
RANK   = persistent career state
```

A Boss can require one flight or several. A flight can participate in many Boss encounters. There is no permanent mapping between flight identity and Boss category.

## 12. Boss Rewards / Consequences

Candidate consequences include:

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

Repeated work must produce additional progression only when it creates additional verified capability, impact, qualification, or materially new evidence.

```text
REPEAT EVENT ≠ AUTOMATIC XP
NEW VERIFIED VALUE → progression consequence
NO NEW VERIFIED VALUE → no artificial career inflation
```

## 14. Proposed Career World

```text
SAGE CAREER WORLD
      ↓
REAL VERIFIED WORK
      ↓
SORTIES / MISSIONS
      ↓
BOSS ENCOUNTERS
      ↓
EMERGENT CLASSIFICATION
   ↙             ↘
 BIG           MAJOR
 BOSS           BOSS
   ↘             ↙
   VERIFIED OUTCOME
       ↙     ↘
     KILL   CAPTURE
        ↓
 CAREER ACCOUNTING
 ├─ POINTS
 ├─ XP
 ├─ QUALIFICATION
 ├─ MASTERY
 └─ BADGES
        ↓
 PROMOTION GATE
        ↓
 SHARED AGENT ROSTER
        ↓
 IMMERSION / HUD / CHAT
```

## 15. Design Lock

The following are design findings for the Career Boss concept:

- Milestones can be represented as Boss Encounters.
- Big and Major are the only defined challenge tiers and are not fixed XP payouts.
- A Boss tests demonstrated capability and provides a progression closure point.
- Elite Kill means verified elimination of a meaningful obstacle.
- Elite Capture means verified acquisition/establishment of a meaningful capability, qualification, intelligence result, or reusable asset.
- Boss outcomes must be evidence-backed.
- Boss progress must be projected from canonical state/evidence; no fake health bars or invented damage.
- Bosses may span multiple sorties and retain failure/attempt history.
- Bosses are not Five-Flight identities or career classes.
- Bosses feed career accounting; they do not replace XP, qualification, mastery, rank, or promotion gates.
- Repeated Boss work must not create automatic career inflation without new verified value.
- Boss classification should emerge retrospectively from the verified multi-dimensional encounter profile rather than task labels or reward size.
- Classification remains provisional when evidence is insufficient.
- Exact feature weights, thresholds, normalization, confidence math, and automatic classification authority remain HOLD pending real execution history.
- No additional Boss tier is defined by this contract.

## 16. Still Open

Not locked:

- exact Boss schema
- exact difficulty calculation
- exact phase schema
- exact Big/Major thresholds
- exact Points/XP consequences
- Boss creation authority
- Boss closure authority
- repeat/retry policy
- team/shared Boss ownership rules
- Boss rewards
- chapter/frontier relationships
- UI/HUD presentation
- exact emergent-classification feature weights
- normalization and threshold calibration
- confidence/evidence-completeness math
- automatic versus governed classification authority

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
