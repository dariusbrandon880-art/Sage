# BIG JUMP WAVE C2 5x4 OPERATING FRAME

**Status:** Governing workflow extension
**Authority:** SAGE C2 Persistent Operating Contract + Git/main truth + validated Master Archive + `docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md`

## Purpose

This document defines the Big Jump Wave execution frame as the primary acceleration workflow layered on top of SAGE governance.

The frame does not replace existing architecture, sessions, or authority boundaries. It coordinates them.

## Core Model (Independent Vehicles)

```
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼

     FLIGHT 1  FLIGHT 2  FLIGHT 3  FLIGHT 4  FLIGHT 5

     Own       Own       Own       Own       Own
     Frontier  Frontier  Frontier  Frontier  Frontier

        \        |        |        |        /
                 ▼
          C2 RECONVERGENCE
          Evidence + Receipts
          Promotion Gate
```

A flight is **NOT** a staged pipeline step.
A flight **IS** an independent capability attack vector operating as a bounded build mission with its own recon, tests, evidence, and milestone output.

5 PATHS x 4 LIFECYCLE STAGES = 20 ADVANCEMENT CELLS

### Big Strike Wave Definition
A **Big Strike Wave** is defined as one coordinated wave where multiple independent flights hit separate frontiers and reconverge (e.g., F1 Fleet intelligence, F2 HUD/immersion, F3 Engineering capability, F4 Governance/security, F5 Evidence/archive). It is NOT five flights building one single item.

## C2 Role

C2 Mission Control must:

- maintain the complete board;
- map every work item to a path and course position;
- select highest-leverage moves;
- prevent duplicate work;
- protect validated architecture;
- require evidence before promotion.

C2 must not:

- invent repository state;
- claim unperformed actions;
- reopen validated work without evidence;
- confuse activity with capability.

## Operational 20-Cell Advancement Matrix

The 5x4 Operating Frame operates across **20 explicit advancement cells** (5 Parallel Paths x 4 Lifecycle Stages):

```
                        STAGE 1           STAGE 2           STAGE 3           STAGE 4
                     Intake & Recon    Bounded Build    Verify & Proof    Warehouse Promote
                   +-----------------+-----------------+-----------------+-----------------+
PATH 1: Research   | Cell P1-S1      | Cell P1-S2      | Cell P1-S3      | Cell P1-S4      |
PATH 2: Continuity | Cell P2-S1      | Cell P2-S2      | Cell P2-S3      | Cell P2-S4      |
PATH 3: Execution  | Cell P3-S1      | Cell P3-S2      | Cell P3-S3      | Cell P3-S4      |
PATH 4: Guard      | Cell P4-S1      | Cell P4-S2      | Cell P4-S3      | Cell P4-S4      |
PATH 5: Warehouse  | Cell P5-S1      | Cell P5-S2      | Cell P5-S3      | Cell P5-S4      |
                   +-----------------+-----------------+-----------------+-----------------+
```

### Stage Transitions & Authorization Gate
- **Stage 1 (Intake & Recon):** SAGI Discovery generates candidates (`DiscoveryCandidate` -> `FlightSelectionProposal`).
- **Authorization Gate:** `FrontierIntelligenceBridge` (`sage/c2/frontier_intelligence_bridge.py`) inspects candidates for explicit C2 candidate authorization before allowing transition to Stage 2. Unapproved items fail closed (`REJECTED_UNAUTHORIZED`).
- **Stage 2 (Bounded Build):** `MultiFrontierDispatcher` executes isolated flight builds across non-overlapping target paths.
- **Stage 3 (Verify & Proof):** Reconvergence engine (`reconverge_five_flight_wave`) and full platform test suite execute fail-closed verification.
- **Stage 4 (Warehouse Promote):** Cryptographic receipts (`FrontierBridgeDispatchReceipt`) and knowledge graph records are committed to the capability warehouse.

## Work Item Tracking Contract

Every active item maps through:

```
PATH (1-5)
    -> LIFECYCLE STAGE (1-4)
    -> FLIGHT (F1-F5)
    -> AUTHORIZATION GATE (FrontierIntelligenceBridge)
    -> BOUNDED BUILD (MultiFrontierDispatcher)
    -> TEST & RECONVERGE (reconverge_five_flight_wave)
    -> RECEIPT & PROMOTION (Capability Warehouse)
```

Required record:

```
Path:
Lifecycle Stage:
Advancement Cell:
Flight:
Mission:
Authorization Status:
Current State:
Blocker:
Evidence Digest:
Capability Gained:
Next Move:
```

## Flight Layer

F1 Foundation
- repository truth
- architecture state
- capability inventory

F2 Intelligence
- reconnaissance
- failure mining
- opportunity discovery

F3 Execution
- governed build
- implementation
- workflow activation

F4 Verification
- tests
- artifacts
- receipts
- proof

F5 Capability Warehouse
- reusable patterns
- lessons
- validated knowledge

## Jules Integration

Every Jules report must be translated by C2 into:

1. Which path advanced?
2. Which course part advanced?
3. Which flight advanced?
4. What capability increased?
5. What evidence exists?
6. What is the next highest-value move?

## Jules Flight Start Board

Jules operates as the engineering execution station inside the same Big Jump Wave framework.

Jules does not create a separate workflow. Jules follows the same governed execution protocol used by C2.

Before every flight:

```
MISSION LOCK
- What capability are we creating?

REALITY LOCK
- What is verified?
- What requires checking?

STATE LOCK
- What already exists?
- What must not be rebuilt?

FLIGHT LOCK
- Path (1-5)
- Course Part (1-4)
- Flight (F1-F5)
```

Shared execution loop:

```
SENSE
-> RECON
-> SUPER SEARCH (when useful)
-> BOUND
-> DECIDE
-> BUILD
-> OBSERVE
-> VERIFY
-> COMPOUND
```

Jules execution reports must return:

```
Path:
Course Part:
Flight:
Mission:
Changes:
Tests:
Evidence:
Capability Gained:
Next Move:
```

C2 and Jules are different stations operating under one shared workflow frame.

C2 coordinates alignment, verification, and architecture protection.

Jules executes engineering work, implementation, testing, and evidence capture.

No duplicate authority.
No separate workflow.
One Big Jump Wave protocol.

## Completion Standard

A capability is real only when:

BUILD
+
TEST
+
VERIFY
+
EVIDENCE
+
REUSE

exist.

## Operating Principle

Big Jump Wave leads execution.

C2 protects alignment.

SAGI discovers.

Builders execute.

Evidence promotes.

The goal is not more activity.

The goal is faster verified capability and compounding execution speed.
