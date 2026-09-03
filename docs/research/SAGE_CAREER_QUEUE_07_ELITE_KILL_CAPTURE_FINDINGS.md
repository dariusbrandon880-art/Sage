# SAGE Career Queue #07 — Elite Kill / Elite Capture Findings

**Status:** RESEARCH-LOCKED FINDINGS / IMPLEMENTATION BOUNDARY
**Date:** 2026-09-03
**Base:** `main`
**Scope:** Career Boss outcome semantics

## 1. Queue Position

Queue #07 advances the already-established Boss model by defining the verified outcome boundary for **Elite Kill** and **Elite Capture**.

This is not a new Boss subsystem. It reconciles the outcome semantics against the existing SAGE mission/sortie, evidence, event, qualification, Points, XP, and immersion substrate.

## 2. Established Career Chain

The governing chain remains:

```text
REAL SAGE WORK
    ↓
MISSION / SORTIE
    ↓
ATTEMPTS / FAILURES / RECOVERY / BREAKTHROUGH
    ↓
EVIDENCE CAPTURE
    ↓
VERIFICATION
    ↓
VERIFIED OUTCOME
    ↓
ELITE KILL / ELITE CAPTURE
    ↓
VERIFIED POINTS
    ↓
CAREER XP
```

Boss classification remains retrospective and Director-governed. SAGE does not manufacture a Boss merely because a task is difficult.

## 3. Elite Kill

**Elite Kill** is a verified outcome whose primary accomplishment is the **elimination or neutralization of a meaningful obstacle**.

Valid semantic targets include:

- blocker
- defect
- regression source
- failure mode
- control/security weakness
- persistent operational obstacle
- frontier obstacle

The word “kill” is SAGE immersion shorthand for verified elimination/neutralization. It does not require literal violence or a literal combat model.

```text
OBSTACLE EXISTS
      ↓
REAL WORK / ATTEMPTS
      ↓
BREAKTHROUGH
      ↓
EVIDENCE
      ↓
VERIFICATION
      ↓
ELITE KILL
      ↓
OBSTACLE NO LONGER BLOCKS THE TARGET
```

A claim that an obstacle was “killed” without verified evidence is not an Elite Kill.

## 4. Elite Capture

**Elite Capture** is a verified outcome whose primary accomplishment is **securing or establishing a meaningful positive asset**.

Valid semantic targets include:

- capability
- qualification
- intelligence finding
- reusable component
- validated asset
- new frontier capability

The word “capture” is SAGE immersion shorthand for verified acquisition/establishment. It does not require a literal capture mechanic.

```text
CAPABILITY / ASSET NOT YET SECURED
             ↓
        REAL WORK
             ↓
        BREAKTHROUGH
             ↓
          EVIDENCE
             ↓
        VERIFICATION
             ↓
       ELITE CAPTURE
             ↓
  CAPABILITY / ASSET IS SECURED
```

A claimed capability without verification is not an Elite Capture.

## 5. Kill and Capture Are Independent Outcome Dimensions

Elite Kill and Elite Capture are **not opposites and are not mutually exclusive**.

One verified encounter can produce both when the evidence supports both outcomes:

```text
ONE VERIFIED ENCOUNTER
        ├── ELITE KILL  → obstacle eliminated
        └── ELITE CAPTURE → capability secured
```

They must remain separately attributable because eliminating an obstacle and securing a capability represent different accomplishments.

Neither outcome is a substitute for the other.

## 6. Outcome vs. Action

The important boundary is that Kill/Capture are **verified outcome classifications**, not arbitrary UI actions or reward buttons.

The system must not treat:

```text
click “KILL” → kill awarded
click “CAPTURE” → capture awarded
```

as authoritative.

Instead:

```text
REAL WORK
  ↓
CANONICAL EVENTS / EVIDENCE
  ↓
VERIFICATION
  ↓
OUTCOME CLASSIFICATION
  ↓
ELITE KILL / ELITE CAPTURE
```

This preserves the existing rule that presentation and game-feel signals remain downstream of canonical evidence/state.

## 7. Outcome Must Be Attached to Verified Lineage

An Elite outcome must be reconstructible from the same durable lineage already used by SAGE.

Minimum lineage concept:

```text
mission_id
sortie_id
attempt / event lineage
 evidence references
verification reference
outcome classification
verified Point consequence
XP consequence
```

The exact implementation schema remains open. The outcome must not become an isolated counter with no evidence lineage.

## 8. Failed Attempts Are Not Erased

An encounter can fail repeatedly before producing a verified Kill/Capture.

Those failures and recovery/adaptation steps remain historical evidence:

```text
ATTEMPT 1 → FAILED
ATTEMPT 2 → BLOCKED
ATTEMPT 3 → RECOVERY
ATTEMPT 4 → BREAKTHROUGH
ATTEMPT 5 → VERIFIED
             ↓
       ELITE KILL / CAPTURE
```

The final outcome does not rewrite the historical path that produced it.

This is especially important when a later Boss classification is made retrospectively.

## 9. Idempotency / Anti-Farming Boundary

The same verified outcome must not generate duplicate career accounting merely because the underlying event is replayed or reprocessed.

The existing verified-event reference principle remains the identity boundary:

```text
SAME VERIFIED EVENT
       ↓
REPLAY
       ↓
NO SECOND CAREER AWARD
```

New progression requires new verified value, such as materially new capability, impact, qualification, or evidence.

This keeps Elite outcomes compatible with the existing Points→XP replay-protection model rather than introducing a second reward ledger.

## 10. Relationship to Boss Classification

The order matters:

```text
REAL WORK
   ↓
REAL HURDLE
   ↓
VERIFIED OUTCOME
   ↓
ELITE KILL / CAPTURE
   ↓
ACCUMULATED PROOF + DIFFICULTY SIGNALS
   ↓
DIRECTOR MAY DECLARE / CONFIRM BOSS FIGHT
   ↓
BIG BOSS ⭐ OR MAJOR BOSS ⭐⭐
```

Therefore:

- Elite Kill/Capture does not automatically create a Boss.
- A Boss does not need to be declared before the work happens.
- A consequential verified outcome can become part of a later Boss classification.
- Big/Major classification must be based on demonstrated challenge characteristics, not arbitrary reward size.

## 11. Relationship to Career Accounting

Elite outcomes are upstream of career accounting but do not replace it.

```text
ELITE OUTCOME
      ↓
VERIFIED PERFORMANCE
      ↓
POINTS
      ↓
CAREER XP
      ↓
RANK / PROMOTION ELIGIBILITY
```

XP remains an accounting consequence. Qualification and promotion remain separately governed evidence gates.

## 12. Relationship to Qualification

An Elite Capture may establish or contribute evidence toward a qualification, but it does not itself bypass the QualificationRegistry gate.

An Elite Kill may eliminate a qualification-blocking defect or failure mode, but it does not itself grant qualification.

The distinction remains:

```text
ELITE OUTCOME = verified accomplishment
QUALIFICATION = formal capability gate
PROMOTION = governed career decision
```

## 13. Relationship to Badges

Badges remain a separate durable accomplishment signal.

```text
BOSS STAR      = challenge class
KILL ⚔️        = verified obstacle elimination
CAPTURE ┃      = verified capability/asset acquisition
BADGE          = verified distinction
POINTS         = verified career accounting
XP             = durable progression accounting
```

These signals must not be collapsed into one another.

## 14. Immersion Boundary

The existing presentation rule remains authoritative:

```text
CANONICAL STATE / EVIDENCE
          ↓
OUTCOME PROJECTION
          ↓
HUD / NAMEPLATE / CHAT
```

HUD elements may display Kill/Capture markers when canonical evidence supports them. They must not invent outcome state, damage, health, verification, Points, or XP.

## 15. Quantitative Game-Design Finding

External game-design research supports the translation of Kill/Capture into **mastery-bearing outcome beats**, rather than treating the final outcome as arbitrary damage depletion. Boss encounters are commonly used as tests of learned skills and meaningful milestone closure; multi-stage encounters can test different capabilities before the final outcome. citeturn0search0turn0search1turn0search3

SAGE should therefore preserve the real-world equivalent: the outcome must demonstrate that the relevant obstacle was actually overcome or that the intended capability was actually secured.

## 16. Locked Findings

The following are locked for Queue #07:

1. **Elite Kill** = verified elimination/neutralization of a meaningful obstacle, blocker, defect, threat, or failure mode.
2. **Elite Capture** = verified acquisition/establishment of a meaningful capability, qualification, intelligence result, or reusable asset.
3. Kill and Capture are independent and may both occur in one verified encounter.
4. Kill/Capture are outcome classifications, not UI commands or independent authority.
5. Both outcomes require canonical evidence and verification.
6. Failed attempts and recovery remain persistent history.
7. Outcome accounting must use the existing verified-event lineage and replay-protection boundary.
8. No duplicate career reward may be produced by replaying the same verified event.
9. Elite Kill/Capture do not automatically create or classify a Boss.
10. Boss classification remains retrospective and Mission Director-governed.
11. Only Big Boss ⭐ and Major Boss ⭐⭐ remain valid Boss classes.
12. Elite outcomes feed verified Points→XP; they do not replace Points, XP, qualification, badges, rank, or promotion gates.
13. Immersion remains read-only and downstream of canonical state/evidence.
14. No Five-Flight structure, assignment, or identity changes are part of Queue #07.

## 17. Still Open

Not locked by Queue #07:

- exact outcome event schema
- exact Kill/Capture point values
- exact evidence minimums beyond existing verification requirements
- team/shared attribution mechanics
- exact Boss-classification scoring
- exact Boss declaration/closure authority implementation
- exact HUD presentation

These require later bounded work and explicit architecture approval if they cross protected architecture boundaries.

## 18. Implementation Boundary

Queue #07 is a **research/contract lock**, not an instruction to create a parallel game engine.

The smallest future implementation seam should reuse existing mission/sortie events, evidence references, verification, Points, XP, qualification, and persistent career history.

No protected Five-Flight architecture is modified by this finding.
