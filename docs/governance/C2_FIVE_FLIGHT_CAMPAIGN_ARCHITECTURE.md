# SAGE C2 Campaign Architecture

## Purpose

Define how SAGE organizes capability execution through the canonical **Big Jump Wave** while preserving:

- Master Archive authority
- authorization boundaries
- evidence discipline
- continuity
- fail-closed execution

This document defines coordination architecture. It does not create active work items.

---

# Critical Rule: No Pre-Labeled Flights

Flights are instantiated only after:

1. repository/context recon
2. evidence review
3. smallest consequential frontier identification
4. authorization
5. build execution begins

Before airborne execution:

- tasks are unknown
- flight numbers are not assigned
- capability claims are not created
- campaign paths are possibilities, not active missions

A campaign architecture is not a backlog.

---

# Canonical C2 Operating Loop

```text
SENSE
RECON
SUPER SEARCH
BOUND
DECIDE
AUTHORIZE
BIG JUMP WAVE
BUILD
OBSERVE
VERIFY
RECONVERGE
COMPOUND
```

**Big Jump Wave is the normal SAGE execution workflow.** There is no Medium Flow operating mode.

---

# C2 FIVE-FLIGHT MODEL (LOCKED)

```text
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┐
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

A flight is **NOT** a staged pipeline:
- NOT "Flight 1 = discovery stage"
- NOT "Flight 2 = testing stage"
- NOT "Flight 3 = build stage"

A flight **IS**:
- an independent capability attack vector
- a bounded build mission
- its own recon
- its own tests
- its own evidence
- its own milestone reporting back to C2 reconvergence

# Big Jump Wave Definition

A **Big Jump Wave** is the canonical SAGE execution unit:
> **One coordinated wave where multiple independent flights hit separate consequential frontiers and reconverge.**

It does **not** mean five flights building one single thing.

Example Big Jump Wave:
- Flight 1 → intelligence/capability advancement
- Flight 2 → product/runtime advancement
- Flight 3 → engineering advancement
- Flight 4 → governance/security advancement
- Flight 5 → evidence/continuity advancement

Each produces its own bounded delta, then C2 evaluates the combined strike.

---

# Big Jump Wave Operating Doctrine

Big Jump Wave is the **normal workflow**, not an escalation tier above Medium Flow.

The canonical pattern is:

```text
MISSION INTAKE
     ↓
RECON + SUPER SEARCH
     ↓
FRONTIER IDENTIFICATION
     ↓
BOUND + AUTHORIZE
     ↓
BIG JUMP WAVE
     ├── Flight 1
     ├── Flight 2
     ├── Flight 3
     ├── Flight 4
     └── Flight 5
     ↓
INDEPENDENT VERIFY
     ↓
C2 RECONVERGENCE
     ↓
EVIDENCE / RECEIPTS
     ↓
CAPABILITY COMPOUNDING
     ↓
NEXT BIG JUMP WAVE
```

The number of concurrent flights may scale when explicitly authorized, but scaling never removes bounded scope, independent verification, or evidence requirements.

---

# Campaign Model

When authorized, C2 coordinates parallel capability work through bounded execution paths.

Each active flight must have:

- explicit objective
- reused components where appropriate
- invariants
- required tests
- evidence requirements
- STOP boundary

Each flight is not:

- independent authority
- separate memory
- replacement for Master Archive
- permission to bypass governance

---

# Unknown Frontier State

The default state before authorization is:

```text
CAMPAIGN ARCHITECTURE READY
        |
        v
RECON REQUIRED
        |
        v
FRONTIER IDENTIFIED
        |
        v
AUTHORIZED BIG JUMP WAVE
        |
        v
FLIGHTS AIRBORNE
```

No transition may be skipped.

---

# Governance Relationship

```text
Master Archive
      |
      v
C2 Control Plane
      |
      v
BIG JUMP WAVE
      |
      v
Authorized Flights Only
      |
      v
Validated Evidence
      |
      v
Capability Compounding
```

The three SAGE lanes remain authoritative. Big Jump Wave coordination does not create new lanes.

---

# Rolls-Royce + Lamborghini Lock

## Rolls-Royce

Protects:

- truth
- boundaries
- evidence
- architectural stability

## Lamborghini

Enables:

- velocity after authorization
- parallel execution after validation
- capability compounding after proof

Velocity begins after control, not before it.

---

## Big Build = Production Velocity + Large Jump Levels

The **Big Build** represents the production law inside each flight: input → build → verify → next task.

The **Big Jump Wave** represents the coordinated parallel execution of independent frontiers.

```text
SAGI Brain
(opportunity discovery)

        ↓

C2 / ChatGPT
(command + execution coordination)

        ↓

BIG JUMP WAVE
(canonical execution workflow)

        ↓

5+ Concurrent Flights
(each running independent targets)

        ↓

Big Build Loop
(input → build → verify → next task)

        ↓

Verified capability gain
        ↓

Capability compounding
        ↓

Next Big Jump Wave
```

**Retired operating mode:** Medium Flow. It is not part of the current SAGE execution hierarchy and must not be described as the default, current, or recommended workflow.

Important separation stays:

* **SAGI Brain** finds possible next builds.
* **C2/ChatGPT** coordinates and executes the selected wave.
* **Big Jump Wave** is the normal production execution workflow.
* **Flights** are the concurrent execution units.
* **Big Build** is the production law that each flight follows.

No mixing the layers.

---

# Operational Reference

The execution method for the C2 control plane is maintained separately in:

`docs/governance/C2_FLIGHT_CONTROL_OPERATING_MODEL.md`

This preserves separation between architecture doctrine and operating procedure.
