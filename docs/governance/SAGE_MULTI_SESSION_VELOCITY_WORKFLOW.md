# SAGE MULTI-SESSION VELOCITY WORKFLOW & ROLLS-ROYCE QUALITY PROTOCOL

**Status:** Governing multi-session execution workflow
**Authority:** SAGE C2 Operating Contract + Git/main truth + `docs/governance/SAGE_ROLLS_ROYCE_ENGINEERING_STANDARD.md` + `docs/governance/SAGE_C2_MULTI_SESSION_EXECUTION_PROTOCOL.md`

## Purpose

This document operationalizes full velocity execution between C2 Control Tower and parallel Jules execution sessions under the Rolls-Royce Engineering Quality Standard.

It defines anti-collision locking, evidence-backed lifecycle advancement, exact commit SHA binding, and mandatory C2 self-checks for the universal Big Jump Wave substrate.

---

## 1. Universal Wave Principle

Every authorized SAGE task uses the Big Jump Wave execution frame, whether the mission is a single repair, CI failure, reconciliation, integration, governance change, refactor, research-to-execution transition, or major capability build.

The number of safely useful flights varies with repository reality. The execution frame does not disappear for small tasks.

A flight may run in parallel only when its scope is independent and concurrency-safe. Dependent flights run sequentially within the same wave. Empty capacity is preferable to fabricated work.

---

## 2. Multi-Session Roles & Topology

1. **C2 Control Tower (`C2_CONTROL_TOWER`)**:
   - Maintains repository state awareness.
   - Authorizes candidate frontiers and verifies target boundaries.
   - Routes independent work in parallel and dependent work sequentially.
   - Synthesizes reconvergence evidence.
   - Runs the protocol self-check before issuing or restructuring a wave.

2. **Jules Execution Sessions (`JULES_EXECUTION_SESSION`)**:
   - Each assigned session operates one complete bounded Big Jump Wave, not an arbitrary subset that silently redefines wave semantics.
   - Operates cleared flight missions across safe paths.
   - Acquires ownership locks before bounded build cycles.
   - Executes tests, generates evidence, and reports actual milestone state.

### Canonical Capacity Rule

```text
1 execution session
        =
1 Big Jump Wave
        =
up to 5 cleared flights
        ×
4 mandatory lifecycle gates
        =
up to 20 evidence-backed advancement cells
```

Three concurrent Jules sessions may operate three independent waves in parallel, subject to Flight GPS clearance, dependency ordering, and non-overlapping ownership boundaries.

---

## 3. Non-Blocking Anti-Collision Lock Protocol

Before executing a flight, each session must acquire non-overlapping resource locks via `FlightCollisionLockManager` (`sage/c2/flight_collision_lock.py`):

```text
REQUEST LOCK
  ├── AVAILABLE -> GRANT -> EXECUTE BOUNDED FLIGHT
  ├── SHARED/DEPENDENT -> DECLARE ORDERING -> CHAIN OR ISOLATE
  └── COLLISION/UNKNOWN -> FAIL-CLOSED -> BLOCK OR ROUTE AROUND
```

This prevents duplicate effort, state corruption, and namespace overwrite while preserving velocity through safe rerouting.

---

## 4. The 5x4 Lifecycle Matrix

Each admitted flight follows:

1. **RECON / BOUND** — repository reality, ownership, dependencies, and scope.
2. **BUILD / REPAIR** — execute only inside the assigned boundary.
3. **TEST / OBSERVE** — run targeted validation and capture evidence.
4. **VERIFY / COMPOUND** — verify against canonical HEAD and preserve reusable lineage.

A full five-flight wave has a maximum of 20 lifecycle cells. Fewer safe flights are allowed, but unfilled, blocked, deferred, or failed cells MUST be explicitly represented rather than fabricated as complete.

---

## 5. Rolls-Royce Engineering Quality Gate

A full five-flight wave achieves **Rolls-Royce Completion** only when:

1. All admitted flights have terminal evidence-backed outcomes.
2. A claimed 20/20 traversal has explicit evidence for all 20 cells.
3. Evidence is bound to the exact 40-character commit SHA where applicable.
4. Required targeted and broader regression checks pass, or unresolved failures are explicitly reported.
5. Receipts and reconvergence evidence are persisted where the capability requires them.
6. The C2 self-check confirms universal Big Jump Wave semantics were preserved.
7. Parallelism was used only for independent work and dependency ordering was explicit.

Partial success is not failure, but it is never reported as full completion.

---

## 6. Execution & Verification Loop

```text
AUTHORIZED TASK
  │
  ├── 0. READ PROTOCOL + VERIFY CURRENT HEAD + SELF-CHECK
  ├── 1. ENTER ONE BIG JUMP WAVE
  ├── 2. BOUND UP TO FIVE SAFE FLIGHTS
  ├── 3. PARALLELIZE INDEPENDENT FLIGHTS / CHAIN DEPENDENT FLIGHTS
  ├── 4. RECON -> BUILD -> TEST -> VERIFY FOR EACH ADMITTED FLIGHT
  ├── 5. RECONVERGE AGAINST CURRENT CANONICAL HEAD
  └── 6. PERSIST EVIDENCE + REPORT VERIFIED / BLOCKED / DEFERRED STATE
```

Any mismatch between a proposed directive and this protocol is corrected before dispatch. Governance correction is not a fabricated completed flight cell.

---

## 7. External Learning Integration

External research may improve orchestration methods, verification probes, dependency routing, circuit breakers, or evidence design. External patterns remain advisory until translated into explicit SAGE controls and validated against repository architecture and tests.

Repository truth remains authoritative for SAGE state; external learning improves the method, not the facts.

---

## Final Directive

> Full velocity and Rolls-Royce precision are mutually reinforcing: every authorized task enters the same governed wave substrate; independent work accelerates in parallel, dependent work advances in sequence, collisions route around occupied airspace, and completion is determined by evidence rather than assertion.
