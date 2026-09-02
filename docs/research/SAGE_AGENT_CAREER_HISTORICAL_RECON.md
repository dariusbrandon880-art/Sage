# SAGE Agent Career — Historical Recon & Design Findings Lock

**Status:** RESEARCH LOCKED / IMPLEMENTATION HOLD  
**Date:** 2026-09-02  
**Scope:** SAGE Agent Career / Rank / Progression side-project research and historical synthesis  
**Authority:** Repository evidence + external design research; this document records findings and hypotheses only. It does **not** authorize architecture changes.

## 1. Purpose

Preserve the recovered historical findings for the SAGE Agent Career / Rank Engine work so the research survives chat loss. This is a research lock, not a Career Engine implementation.

The immediate design question is how to turn SAGE's existing governed execution, evidence, qualification, progression, fleet, and immersion infrastructure into a persistent agent career system without creating a parallel game universe or weakening canonical authority.

## 2. Repository Historical Lineage Recovered

### 2.1 Governed mission progression predates the career concept

SAGE already had a deterministic, governed Mission Progression Controller before the Airspace career layer. The recovered August 2026 progression work included:

- deterministic mission state transitions
- predecessor/transition validation
- PFC preflight integration
- HDG v2 causality auditing
- MEC/ACH/PEF/causality adapters
- deterministic serialization
- zero-spawning boundary checks
- evidence generation and validation
- regression-contract hardening
- integration into the developer execution workflow

**Finding:** progression began as a governed execution concept, not as a game mechanic.

### 2.2 Airspace C2 introduced persistent capability progression

Commit `0998edf42f58fde99ee84d7fdc02a18edf9bf513` (2026-08-16) introduced the SAGE Airspace C2 and Capability Progression subsystem. The commit describes:

- persistent evidence-backed Airspace C2
- Station roles
- Mission/Sortie state machines
- Intel telemetry
- CQL/SQL qualification registries
- XP progression
- append-only event-ledger persistence
- mobile-first C2 rendering
- read-only adapters

**Finding:** this is the major convergence point where governed execution became persistent capability/progression state.

### 2.3 Verified progression separated proof from raw progression

August 21 work introduced verified progression projection and adversarial coverage. The progression projection work was explicitly merged only after governed CI verification.

**Finding:** SAGE's trajectory is toward evidence-backed progression rather than raw activity-backed XP.

### 2.4 Fleet intelligence expanded progression beyond simple counts

Fleet readiness/evolution work introduced quality-oriented signals and failure-memory controls, including evidence completeness, regression resistance, protected-path enforcement, concurrency controls, and fail-closed behavior.

**Finding:** fleet evolution already distinguishes useful capability growth from mere quantity of activity.

### 2.5 Persistent agent identity and immersion followed

Commit `2b316ff8dd26d64fa44feb89b8eb8fca95fc031f` added persistent agent progression nameplates for immersive SAGE chat, with bounded shared agent awareness, canonical progression, truthful coordination state, and explicit coordination events.

Commit `c98142ad13d726f2e9db8bef0730f2b37b1c79b5` expanded the immersion progression language design lab and established read-only progression projection primitives, canonical visual progression projections, an immersion boot surface, a reference atlas, and anti-drift continuity requirements.

Commit `155c6c10246625850318bd308c9f6934a3e98719` (2026-09-02) implemented a four-layer HUD and strike-feed projection across SAGE interface surfaces. Its stated boundary is deterministic presentation derived strictly from canonical state without inventing state or granting authority.

**Finding:** career/rank presentation belongs downstream of canonical state and evidence; immersion is presentation, not authority.

## 3. Current Main Implementation That Must Not Be Mistaken for the Final Career Engine

The live `main` file `sage/experimental/airspace/fleet_qualification_ledger.py` is a real historical implementation, but it is simplistic.

Current `FleetRankState` contains:

- `agent_id`
- `rank_title` (default `Cadet`)
- `total_xp`
- `cql_qualified`
- `sql_qualified`
- `verification_badges`
- `last_updated`

Current `record_xp_event()` directly increments XP and changes rank by hard-coded thresholds:

- 100+ XP → Flight Captain
- 500+ XP → Squadron Leader + CQL
- 1000+ XP → Fleet Commander + CQL + SQL

The same method therefore allows XP thresholds to drive qualification flags.

**Finding:** this implementation is historical substrate, not the target Career Engine. It demonstrates the original progression primitive but conflicts with the later evidence/qualification separation if extended naively.

## 4. Core Architectural Finding

The recovered SAGE evolution is best represented as:

```text
GOVERNED MISSION PROGRESSION
        ↓
EXECUTION + CAUSALITY
        ↓
EVIDENCE VALIDATION
        ↓
AIRSPACE / SORTIES
        ↓
CQL + SQL
        ↓
XP / PROGRESSION
        ↓
VERIFIED PROGRESSION
        ↓
FLEET READINESS
        ↓
FLEET EVOLUTION
        ↓
PERSISTENT NAMEPLATES
        ↓
IMMERSION PROJECTION
        ↓
CAREER / RANK QUESTION
```

The proposed Career layer should therefore extend this existing chain rather than create a parallel progression universe.

## 5. Locked Career Model Hypothesis — NOT IMPLEMENTATION

```text
REAL WORK
   ↓
CANONICAL EVENT
   ↓
EVIDENCE
   ↓
VERIFICATION
   ↓
QUALIFIED CAPABILITY
   ↓
CAREER ACCOUNTING
   ├── POINTS
   └── XP
   ↓
PROMOTION ELIGIBILITY
   ↓
PROMOTION GATE
   ├── PROMOTE
   └── HOLD
   ↓
SHARED AGENT ROSTER
   ↓
IMMERSION / NAMEPLATE
```

### Separation of meanings

- **Points:** immediate performance/accounting score for a verified event or work product.
- **XP:** accumulated verified career progression.
- **Qualification:** evidence-backed demonstration that a specific capability standard has been met.
- **Rank:** persistent compression of demonstrated overall capability/maturity.
- **Promotion eligibility:** rule evaluation indicating whether the agent may advance.
- **Promotion gate:** authoritative decision boundary that produces PROMOTE or HOLD.
- **Roster/nameplate:** read-only projection of canonical career state.

**Locked principle:** XP must not be the sole authority for qualification or promotion.

## 6. Proposed Evidence Flow

```text
WORK
  ↓
POINTS
  ↓
VERIFICATION
  ↓
XP CONVERSION
  ↓
CAREER XP
  ↓
RANK PROGRESS
```

This preserves the useful game mechanic of accumulating progression while ensuring that SAGE rewards verified capability rather than raw activity.

Candidate research values previously explored (not approved implementation):

- baseline concept: 100 verified Points → 10 XP
- example immediate points: mission completion, code/build, tests, evidence capture, independent verification, reusable capability, frontier advancement
- candidate quality model: `BASE POINTS × VERIFICATION QUALITY × DIFFICULTY × IMPACT/REUSE`

These numbers remain **design candidates**, not canonical thresholds.

## 7. Promotion Principle

The preferred model is:

```text
XP makes an agent eligible.
Qualification + evidence + capability dimensions determine whether promotion is warranted.
The promotion gate decides PROMOTE or HOLD.
```

Promotion should not be reducible to:

```text
XP >= threshold → rank
```

The current FleetQualificationLedger does exactly that at its historical prototype level; the future design should not simply harden those hard-coded thresholds into a larger version of the same mechanism.

## 8. Career Dimensions

External research and SAGE history both support separating broad career rank from narrower mastery/qualification.

Potential conceptual separation:

```text
CAREER RANK      = broad demonstrated maturity
MASTERY          = domain-specific capability
CQL / SQL        = formal qualification
BADGES           = verified distinctions
XP               = accumulated career progression
SORTIES          = execution history
EVIDENCE         = proof
```

These are design concepts only until explicitly approved and mapped to canonical repo structures.

## 9. External Design Findings

### 9.1 Riot career-leveling research

Riot's engineering career/title experiments found problems with simplistic game-like rank labels, including ambiguity, inconsistent measurement, checkbox behavior, and difficulty representing multiple dimensions of capability. Their later direction used multiple mastery attributes rather than treating a single level/title as the complete representation of capability.

**Transferable finding:** do not make SAGE rank a single undifferentiated activity score.

### 9.2 Persistent progression systems

Modern game progression systems commonly separate career/account progression, mastery, badges/accolades, and unlocks rather than forcing every form of progress into one number.

**Transferable finding:** SAGE can use XP as an accounting/progression layer while retaining separate qualification and mastery state.

### 9.3 Server-authoritative persistence

Current progression-system engineering guidance consistently treats authoritative server-side state as the source of truth for lifetime XP/progression and exposes that state to presentation clients.

**Transferable finding:** SAGE career state must remain canonical and persistent; ChatGPT/Jules/Gemini/conversation presentation cannot manufacture rank or XP.

### 9.4 Progression must resist farming

Game-economy research repeatedly identifies repetitive, guaranteed XP farming as a progression failure mode.

**Transferable finding:** SAGE must reward verified capability and impact, not merely event volume or repetitive low-value work.

### 9.5 Career/rank should not erase specialization

Career research and real-world qualification frameworks show that broad advancement and specialist qualification are related but distinct. Specialized competence can matter differently at different career stages.

**Transferable finding:** rank and domain mastery/qualification should remain separate axes.

### 9.6 Qualification gates are stronger than raw scores

Real qualification systems commonly define explicit standards/gates rather than treating a cumulative score as sufficient proof of readiness.

**Transferable finding:** SAGE's CQL/SQL and future promotion gate should remain evidence/standard based.

## 10. Five-Flight Rule — LOCKED

The Five Flights are reusable execution vehicles, not permanent career classes.

```text
F1 ≠ Recon rank
F2 ≠ Intelligence rank
F3 ≠ Builder rank
F4 ≠ Verification rank
F5 ≠ Warehouse rank
```

Flight identity and mission are assigned by authorized C2/state. Career rank describes persistent demonstrated capability across work; flight assignment describes current execution context.

No Career Engine design may pin permanent career identity to F1–F5 without explicit architecture approval.

## 11. Authority / Governance Boundary

This research lock does not authorize architectural change.

The Career Engine, if later implemented, must preserve the repository's existing authority boundaries, including the principle that agents may execute within the architecture but may not redefine protected architecture, governance, flight structure, or authority boundaries without explicit Mission Director approval.

The career layer must not grant ChatGPT, Jules, Gemini, a renderer, a HUD, a nameplate, or conversational state authority to mutate rank/qualification.

## 12. Canonical Presentation Boundary

The intended direction is:

```text
CANONICAL CAREER STATE
        ↓
READ-ONLY PROJECTION
        ↓
ROSTER / NAMEPLATE / HUD / CHAT
```

Not:

```text
CHAT / HUD / GAME LAYER
        ↓
INVENT RANK OR XP
```

Immersion is operational projection over real SAGE state/evidence, not fake HUD theater.

## 13. Research Status

### LOCKED FINDINGS

- SAGE progression predates the career concept and began as governed mission/execution progression.
- Airspace introduced persistent sorties, qualifications, XP, and event-ledger progression.
- Verified progression subsequently strengthened the evidence boundary.
- Fleet readiness/evolution adds quality and failure-memory dimensions.
- Persistent nameplates and immersion are downstream projections.
- The current FleetQualificationLedger is real but simplistic historical substrate.
- XP, qualification, mastery, rank, promotion eligibility, and presentation should be separate concepts.
- Career progression should be evidence-backed and persistent.
- Career state should be authoritative/canonical, not conversational.
- Five Flights remain reusable execution vehicles, not career classes.
- Promotion should use a gate and support HOLD as well as PROMOTE.
- Anti-farming/quality-over-quantity constraints are required.
- No Career Engine implementation is authorized by this research document.

### DESIGN CANDIDATES — NOT LOCKED

- exact point values
- exact XP conversion ratio
- rank count
- rank names
- rank thresholds
- quality/difficulty/impact multipliers
- mastery dimensions
- badge taxonomy
- promotion prerequisites
- prestige/reset mechanics
- seasonal mechanics
- reward mechanics
- roster UI details

## 14. Implementation Hold

**DO NOT IMPLEMENT THE CAREER ENGINE FROM THIS DOCUMENT ALONE.**

Next required step is a repo-first architecture reconciliation against current `main`, including current canonical event/evidence schemas, qualification registries, progression receipts, fleet state, roster/nameplate projections, and authority gates. Any architecture change requires the existing SAGE architecture-approval rule to be honored.

## 15. Research Chain

```text
SAGE HISTORY
  ↓
CONTINUITY
  ↓
PERSISTENCE
  ↓
VALIDATION
  ↓
AUTHORITY
  ↓
EVIDENCE
  ↓
QUALIFICATION
  ↓
CAPABILITY
  ↓
FLEET
  ↓
IMMERSION
  ↓
CAREER
```

**Research lock intent:** preserve this chain and prevent future chat loss from collapsing the Career Engine back into a generic XP/rank feature.
