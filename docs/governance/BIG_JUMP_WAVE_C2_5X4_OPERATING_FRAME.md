# BIG JUMP WAVE C2 5x4 OPERATING FRAME

**Status:** Governing workflow extension  
**Authority:** SAGE C2 Persistent Operating Contract + Git/main truth + validated Master Archive + `docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md`

## Purpose

This document defines the Big Jump Wave execution frame as the primary acceleration workflow layered on top of SAGE governance.

The frame does not replace existing architecture, sessions, or authority boundaries. It coordinates them.

## Core Model — Five Reusable Open Slots

```
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼

     FLIGHT 1  FLIGHT 2  FLIGHT 3  FLIGHT 4  FLIGHT 5

       OPEN      OPEN      OPEN      OPEN      OPEN
       SLOT      SLOT      SLOT      SLOT      SLOT

        \        |        |        |        /
                 ▼
          C2 RECONVERGENCE
          Evidence + Receipts
          Promotion Gate
```

A flight is **NOT** a permanent capability, department, stage, or ownership lane.

A flight **IS** a reusable execution slot that receives an explicitly assigned mission for the current wave. Any slot may perform research, recon, implementation, repair, testing, governance, security, evidence, integration, sports work, or any other authorized mission.

The five slots may simultaneously perform different missions. They may also be reassigned in a later wave. Slot identity and mission identity must remain separate in evidence and provenance.

5 OPEN SLOTS x 4 LIFECYCLE STAGES = 20 ADVANCEMENT CELLS

### Big Strike Wave Definition
A **Big Strike Wave** is one coordinated wave where up to five reusable flight slots attack separate authorized missions/frontiers and reconverge. The missions are selected per wave; they are not permanently attached to F1–F5.

## C2 Role

C2 Mission Control must:

- maintain the complete board;
- select the highest-leverage uncovered missions;
- assign each mission to an available slot for the current wave;
- prevent duplicate work and active collision;
- protect validated architecture;
- require evidence before promotion.

C2 must not:

- invent repository state;
- claim unperformed actions;
- reopen validated work without evidence;
- confuse activity with capability;
- treat a flight slot as a permanent capability owner.

## Operational 20-Cell Advancement Matrix

The 5x4 Operating Frame operates across **20 explicit advancement cells** (5 reusable slots x 4 lifecycle stages):

```
                        STAGE 1           STAGE 2           STAGE 3           STAGE 4
                     Intake & Recon    Bounded Build    Verify & Proof    Warehouse Promote
                   +-----------------+-----------------+-----------------+-----------------+
SLOT 1 / F1         | Cell F1-S1      | Cell F1-S2      | Cell F1-S3      | Cell F1-S4      |
SLOT 2 / F2         | Cell F2-S1      | Cell F2-S2      | Cell F2-S3      | Cell F2-S4      |
SLOT 3 / F3         | Cell F3-S1      | Cell F3-S2      | Cell F3-S3      | Cell F3-S4      |
SLOT 4 / F4         | Cell F4-S1      | Cell F4-S2      | Cell F4-S3      | Cell F4-S4      |
SLOT 5 / F5         | Cell F5-S1      | Cell F5-S2      | Cell F5-S3      | Cell F5-S4      |
                   +-----------------+-----------------+-----------------+-----------------+
```

### Stage Transitions & Authorization Gate
- **Stage 1 (Intake & Recon):** SAGI Discovery generates candidates (`DiscoveryCandidate` -> `FlightSelectionProposal`).
- **Authorization Gate:** `FrontierIntelligenceBridge` inspects candidates for explicit C2 candidate authorization before allowing transition to Stage 2. Unapproved items fail closed (`REJECTED_UNAUTHORIZED`).
- **Stage 2 (Bounded Build):** `MultiFrontierDispatcher` executes isolated missions across non-overlapping target paths. The target is bounded; the flight slot itself is not permanently bounded to a capability.
- **Stage 3 (Verify & Proof):** Reconvergence and the full platform test suite execute fail-closed verification.
- **Stage 4 (Warehouse Promote):** Cryptographic receipts and knowledge graph records are committed to the capability warehouse.

## Work Item Tracking Contract

Every active item maps through:

```
MISSION
    -> OPEN FLIGHT SLOT (F1-F5)
    -> LIFECYCLE STAGE (1-4)
    -> AUTHORIZATION GATE
    -> BOUNDED MISSION EXECUTION
    -> TEST & RECONVERGE
    -> RECEIPT & PROMOTION
```

Required record:

```
Slot:
Lifecycle Stage:
Advancement Cell:
Mission:
Target / Collision Zone:
Authorization Status:
Current State:
Blocker:
Evidence Digest:
Capability Gained:
Next Move:
```

## Flight Layer

F1–F5 have **no permanent capability labels**. Their only persistent meaning in the Big Jump Wave is reusable execution capacity and identity for provenance.

The mission specification determines what a slot does in a particular wave. A fresh wave may assign completely different missions to the same slot IDs.

## Jules Integration

Every Jules report must be translated by C2 into:

1. Which reusable slot advanced?
2. Which lifecycle stage advanced?
3. What mission was assigned for this wave?
4. What capability increased?
5. What evidence exists?
6. What is the next highest-value move?

Jules operates as the engineering execution station inside the same Big Jump Wave framework. Jules does not create a separate workflow.

Before every flight:

```
MISSION LOCK
- What capability are we creating or repairing?

REALITY LOCK
- What is verified?
- What requires checking?

STATE LOCK
- What already exists?
- What must not be rebuilt?

SLOT LOCK
- Slot identity: F1-F5
- Current mission assignment
- Target / collision zone
```

Shared execution loop:

```
SENSE
-> RECON
-> SUPER SEARCH (when useful)
-> BOUND THE MISSION
-> DECIDE
-> BUILD / REPAIR / TEST / RECON
-> OBSERVE
-> VERIFY
-> COMPOUND
```

## Completion Standard

A capability is real only when:

BUILD / REPAIR
+
TEST
+
VERIFY
+
EVIDENCE
+
REUSE

exist.

## Capability Advancement Gate — Non-Negotiable

A Big Jump Wave is **not complete merely because its 20-cell matrix is green, receipts exist, or the test suite passes**.

For every mission, C2/Jules must establish a **NET CAPABILITY DELTA** against the authoritative pre-wave baseline:

```
BASELINE CAPABILITY
    -> TARGET FRONTIER
    -> CONCRETE CODE / BEHAVIOR CHANGE
    -> DEDICATED VERIFICATION
    -> EVIDENCE BOUND TO RESULT
    -> REUSABLE OUTPUT
    -> RECONVERGENCE
    -> PROMOTION
```

### Evidence-only prohibition

Evidence, receipts, reports, hashes, matrices, documentation, or test-only changes **do not count as capability advancement by themselves**. They may prove an advancement, but cannot substitute for one.

If a mission produces no concrete capability delta, its advancement status MUST be recorded as `NO_NET_CAPABILITY_DELTA` and the target must be returned to target selection rather than inflated into velocity.

### Baseline and duplicate gate

Before BUILD, every mission must record:

- authoritative baseline SHA;
- exact target files / collision zone;
- existing capability already present;
- reason the target is uncovered and higher leverage than the next candidate;
- assigned reusable flight slot for this wave.

A target already present on the baseline MUST NOT be reopened or relabeled as new advancement. It must be replaced by the next-highest-leverage uncovered target.

### Verification gate

A green test establishes that the tested behavior passes. It does not establish that the behavior is newly capable. C2 must separately verify the before/after capability delta and persistent/reusable output.

### Wave promotion gate

A wave may be promoted only when every claimed capability cell has:

`BUILD + TEST + VERIFY + EVIDENCE + REUSE`

and the wave-level report distinguishes:

- execution/evidence throughput;
- net verified capability added;
- rework/conflicts;
- human intervention;
- blocked or no-delta missions.

## Deep Recon / Super Search Gate

Super Search is a reconnaissance sensor, not repository authority.

For substantive engineering work, C2 MUST:

1. establish repository-first reality lock;
2. determine whether external intelligence can materially change target selection, implementation, security, validation, or verification;
3. use targeted primary/current external intelligence when it can change the decision;
4. synthesize external findings with repository truth before mutation;
5. reuse verified findings instead of repeating identical searches;
6. avoid turning research into a serial approval gate when sufficient evidence already exists.

Super Search may be omitted only when external information cannot materially change the implementation or verification decision. Its omission must not be used to justify speculative work.

## Velocity Measurement Contract

SAGE measures velocity as **verified reusable capability added per scarce execution capacity**, not as task count, receipt count, elapsed time, or green-cell count alone.

Every Big Jump Wave should therefore record, where available:

```
External Sessions Consumed:
Active Slots Actually Executed:
Distinct Missions Executed:
Net Capability Deltas:
Capability Deltas Verified:
Reusable Outputs Promoted:
Rework / Conflicts:
Human Intervention:
No-Net-Delta Missions:
Targeted External Recon Used:
Execution Duration:
Verification Duration:
```

Do not claim a multiplier from one wave. Velocity claims require repeated observations over comparable waves with the same completion boundary.

## C2 Stop/Continue Rule

C2 must continue authorized work through the complete bounded workflow. It must not stop at:

- target identification;
- a plan;
- a green evidence matrix;
- a local test result;
- a pasted agent report;
- or a successful workflow configuration.

C2 may stop only when:

1. the authorized completion boundary is satisfied;
2. a real external blocker prevents continuation;
3. a governance/authorization boundary requires human action; or
4. repository evidence proves that no safe implementation is justified, in which case the mission must record the decision and select the next highest-value path.

## Operating Principle

Big Jump Wave leads execution.

C2 protects alignment.

SAGI discovers.

Builders execute.

Evidence promotes.

The five flights are reusable open slots—not permanent departments.

The goal is not more activity.

The goal is faster verified capability and compounding execution speed.
