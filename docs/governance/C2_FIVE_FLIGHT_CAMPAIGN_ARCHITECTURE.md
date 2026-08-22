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
