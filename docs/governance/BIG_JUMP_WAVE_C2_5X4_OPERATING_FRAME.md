# BIG JUMP WAVE C2 5x4 OPERATING FRAME

**Status:** Governing workflow extension
**Authority:** SAGE C2 Persistent Operating Contract + Git/main truth + validated Master Archive + `docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md`

## Purpose

This document defines the Big Jump Wave execution frame as the acceleration workflow layered on top of SAGE governance. It coordinates independent reusable flight slots without assigning permanent missions to any slot.

## Core Model — Reusable Independent Vehicles

```text
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼

     FLIGHT 1  FLIGHT 2  FLIGHT 3  FLIGHT 4  FLIGHT 5

     dynamic   dynamic   dynamic   dynamic   dynamic
     mission   mission   mission   mission   mission

        \        |        |        |        /
                 ▼
          C2 RECONVERGENCE
          Evidence + Receipts
          Promotion Gate
```

A flight is **NOT** a staged pipeline step and is **NOT** a permanent department, capability, or role.

A flight **IS** a reusable execution slot. C2 assigns its mission for each wave from the current canonical state, target frontier, authorization, collision boundaries, and expected capability delta.

The same F1-F5 slot may perform research, recon, build, repair, verification, governance, warehouse work, or another authorized mission in a later wave.

The governing contract is `docs/governance/FLIGHT_ASSIGNMENT_CONTRACT.md`.

## Big Strike Wave Definition

A **Big Strike Wave** is one coordinated wave in which multiple independent reusable flights attack separately authorized frontiers and reconverge. The composition is selected per wave. It may contain different mission types or similar mission types against separate frontiers. It is never derived from the flight number.

## C2 Role

C2 Mission Control must:

- maintain the complete board;
- map every work item to a current path/course position and assigned flight;
- select highest-leverage moves;
- prevent duplicate work;
- protect validated architecture;
- require evidence before promotion.

C2 must not:

- invent repository state;
- claim unperformed actions;
- reopen validated work without evidence;
- confuse activity with capability;
- infer a mission from F1-F5.

## Operational 20-Cell Advancement Matrix

The 5x4 frame represents **20 advancement cells**: five parallel work paths crossed with four lifecycle stages. Paths describe the work frontier for a particular wave; they do **not** permanently belong to flight slots.

```text
                        STAGE 1           STAGE 2           STAGE 3           STAGE 4
                     Intake & Recon    Bounded Build    Verify & Proof    Warehouse Promote
                   +-----------------+-----------------+-----------------+-----------------+
PATH 1              | Cell P1-S1      | Cell P1-S2      | Cell P1-S3      | Cell P1-S4      |
PATH 2              | Cell P2-S1      | Cell P2-S2      | Cell P2-S3      | Cell P2-S4      |
PATH 3              | Cell P3-S1      | Cell P3-S2      | Cell P3-S3      | Cell P3-S4      |
PATH 4              | Cell P4-S1      | Cell P4-S2      | Cell P4-S3      | Cell P4-S4      |
PATH 5              | Cell P5-S1      | Cell P5-S2      | Cell P5-S3      | Cell P5-S4      |
                   +-----------------+-----------------+-----------------+-----------------+
```

### Stage Transitions & Authorization Gate

- **Stage 1:** SAGI Discovery generates candidates (`DiscoveryCandidate` -> `FlightSelectionProposal`).
- **Authorization Gate:** `FrontierIntelligenceBridge` validates explicit C2 authorization before Stage 2. Unapproved items fail closed.
- **Stage 2:** `MultiFrontierDispatcher` executes isolated builds using the current wave's explicit F1-F5 assignments.
- **Stage 3:** Reconvergence and the full platform test suite perform fail-closed verification.
- **Stage 4:** Cryptographic receipts and validated knowledge are eligible for capability-warehouse promotion.

## Work Item Tracking Contract

Every active item maps through:

```text
CURRENT PATH / FRONTIER
    -> LIFECYCLE STAGE
    -> REUSABLE FLIGHT SLOT (F1-F5)
    -> AUTHORIZATION GATE
    -> BOUNDED BUILD
    -> TEST & RECONVERGE
    -> RECEIPT & PROMOTION
```

Required record:

```text
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

## Flight Layer — Dynamic Assignment Only

F1-F5 are **five reusable slots**. They have no permanent mission labels.

For every wave, C2 MUST assign each slot explicitly:

```text
Flight F1 -> Mission selected for this wave
Flight F2 -> Mission selected for this wave
Flight F3 -> Mission selected for this wave
Flight F4 -> Mission selected for this wave
Flight F5 -> Mission selected for this wave
```

Assignment can change completely on the next wave. Historical reports, receipt filenames, examples, and previous assignments do not establish standing flight roles.

## Jules Flight Start Board

Before every flight:

```text
MISSION LOCK
- What capability are we creating or repairing?

REALITY LOCK
- What is verified?
- What requires checking?

STATE LOCK
- What already exists?
- What must not be rebuilt?

FLIGHT LOCK
- Which reusable slot is assigned this mission?
- What exact mission is bound to that slot for this wave?
```

The dispatcher must reject or hold any mission plan that omits an explicit slot assignment, duplicates a slot, or attempts to derive mission identity from the slot number.

## Completion Standard

A capability is real only when:

`BUILD + TEST + VERIFY + EVIDENCE + REUSE`

exist at the declared acceptance boundary.

## Capability Advancement Gate — Non-Negotiable

A green matrix, receipt, report, or test suite is not itself a capability delta. Every flight must establish a concrete before/after capability change against the authoritative pre-wave baseline.

If no concrete capability delta exists, record `NO_NET_CAPABILITY_DELTA` and return the target to selection.

Before BUILD, record:

- authoritative baseline SHA;
- exact target files / collision zone;
- existing capability already present;
- reason the target is uncovered and higher leverage than alternatives.

A target already present on the baseline MUST be replaced by the next-highest-leverage uncovered target.

## Deep Recon / Super Search Gate

Super Search is a reconnaissance sensor, not repository authority.

For substantive work, C2 establishes repository-first truth, determines whether external intelligence can materially change the decision, uses targeted current primary intelligence when useful, then reconciles external findings with canonical repository truth before mutation.

Super Search may be omitted only when external information cannot materially change implementation or verification.

## Velocity Measurement Contract

SAGE measures velocity as verified reusable capability added per scarce execution capacity, not task count, receipt count, elapsed time, or green-cell count.

Every wave should record, where available:

```text
External Sessions Consumed:
Active Flights Actually Executed:
Net Capability Deltas:
Capability Deltas Verified:
Reusable Outputs Promoted:
Rework / Conflicts:
Human Intervention:
No-Net-Delta Flights:
Targeted External Recon Used:
Execution Duration:
Verification Duration:
```

## C2 Stop/Continue Rule

C2 must continue authorized work through the complete bounded workflow. It may stop only at the declared completion boundary, a real external blocker, a governance/authorization boundary requiring human action, or a repository-proven decision that no safe implementation is justified.

## Operating Principle

Big Jump Wave leads execution.

C2 protects alignment.

SAGI discovers.

Reusable flights execute whatever missions C2 assigns.

Evidence promotes.

The goal is not more activity. The goal is faster verified capability and compounding execution speed.
