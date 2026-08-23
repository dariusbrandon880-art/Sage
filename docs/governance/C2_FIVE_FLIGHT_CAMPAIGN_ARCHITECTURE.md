# SAGE C2 Campaign Architecture

## Purpose

Define how SAGE may organize large capability campaigns while preserving:

- Master Archive authority
- authorization boundaries
- evidence discipline
- continuity
- fail-closed execution

This document defines a coordination architecture only. It does not create active work items.

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

# C2 Operating Loop

```text
SENSE
RECON
SUPER SEARCH
BOUND
DECIDE
AUTHORIZE
BUILD
OBSERVE
VERIFY
COMPOUND
```

---

# Campaign Model

When authorized, C2 may coordinate parallel capability work through bounded execution paths.

Each active flight must have:

- explicit objective
- reused components
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
AUTHORIZED BUILD
        |
        v
FLIGHT AIRBORNE
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
Campaign Architecture
      |
      v
Authorized Flights Only
      |
      v
Validated Evidence
```

The three SAGE lanes remain authoritative. Campaign coordination does not create new lanes.

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

The **Big Build** is not just the build process itself.

It represents the **velocity multiplier** created by:

* parallel execution,
* compounding capability,
* increasing build scale,
* moving into larger jump levels over time.

So the hierarchy becomes:

```text
SAGI Brain
(opportunity discovery)

        ↓

C2 / ChatGPT
(command + execution coordination)

        ↓

Big Build Wave
(parallel execution velocity)

        ↓

5 Concurrent Flights
(each running independent targets)

        ↓

Big Build
(input → build → verify → next task)

        ↓

Verified capability gain
        ↓
Higher jump level
```

The evolution of workflow scale:

```text
Small / Minimal
        ↓
Medium
        ↓
Big
        ↓
Large
```

Meaning:

* **Small / Minimal** = focused execution and narrow changes
* **Medium** = current expanded workflow with stronger coordination
* **Big** = multiple connected builds increasing production velocity
* **Large** = major capability jumps where parallel waves compound into a new operating level

Important separation stays:

* **SAGI Brain** finds possible next builds.
* **C2/ChatGPT** coordinates and executes the selected wave.
* **Big Build Wave** creates parallel velocity.
* **Five Flights** are the concurrent execution units.
* **Big Build** is the production law that each flight follows.

No mixing the layers. This is the corrected architecture interpretation.
