# SAGE MULTI-SESSION VELOCITY WORKFLOW & ROLLS-ROYCE QUALITY PROTOCOL

**Status:** Governing multi-session execution workflow
**Authority:** SAGE C2 Operating Contract + Git/main truth + `docs/governance/SAGE_ROLLS_ROYCE_ENGINEERING_STANDARD.md` + `docs/governance/SAGE_C2_MULTI_SESSION_EXECUTION_PROTOCOL.md`

## Purpose

This document operationalizes full velocity multi-session execution between C2 Control Tower and parallel Jules execution sessions under the Rolls-Royce Engineering Quality Standard.

It defines the non-blocking anti-collision locking, 20-cell lifecycle matrix advancement, and exact commit SHA evidence binding required for parallel Big Jump Waves.

---

## 1. Multi-Session Roles & Topology

Multi-session Big Jump Waves operate across two explicit station roles:

1. **C2 Control Tower (`C2_CONTROL_TOWER`)**:
   - Maintains complete repository state awareness.
   - Authorizes candidate frontiers and verifies non-overlapping target boundaries.
   - Synthesizes reconvergence evidence across parallel flights.

2. **Jules Execution Sessions (`JULES_EXECUTION_SESSION`)**:
   - Operates assigned flight missions across independent paths.
   - Acquires non-overlapping resource locks prior to bounded build cycles.
   - Executes tests, generates evidence, and reports milestone completion.

---

## 2. Non-Blocking Anti-Collision Lock Protocol

Before executing a flight, each session must acquire non-overlapping resource locks via `FlightCollisionLockManager` (`sage/c2/flight_collision_lock.py`):

```text
REQUEST LOCK (session_id, flight_id, target_files, target_namespaces)
  ├── IF AVAILABLE -> GRANT LOCK -> EXECUTE BOUNDED BUILD
  └── IF COLLISION -> FAIL-CLOSED (BLOCKED_LOCK_COLLISION) -> ISOLATE & RE-SCHEDULE
```

This prevents duplicate effort, state corruption, or namespace overwrite across concurrent execution sessions.

---

## 3. The 5x4 20-Cell Lifecycle Matrix

Every Big Jump Wave advances 5 independent parallel flight paths across 4 mandatory lifecycle milestone gates:

```text
                       STAGE 1           STAGE 2           STAGE 3           STAGE 4
                    Intake & Recon    Bounded Build    Verify & Proof    Warehouse Promote
                  +-----------------+-----------------+-----------------+-----------------+
PATH 1: F1 Core   | Cell P1-S1      | Cell P1-S2      | Cell P1-S3      | Cell P1-S4      |
PATH 2: F2 Intel  | Cell P2-S1      | Cell P2-S2      | Cell P2-S3      | Cell P2-S4      |
PATH 3: F3 Exec   | Cell P3-S1      | Cell P3-S2      | Cell P3-S3      | Cell P3-S4      |
PATH 4: F4 Guard  | Cell P4-S1      | Cell P4-S2      | Cell P4-S3      | Cell P4-S4      |
PATH 5: F5 Evidence| Cell P5-S1     | Cell P5-S2      | Cell P5-S3      | Cell P5-S4      |
                  +-----------------+-----------------+-----------------+-----------------+
```

Advancement across all 20 cells is mandatory for wave reconvergence.

---

## 4. Rolls-Royce Engineering Quality Standard Gate

A Big Jump Wave achieves **Rolls-Royce Completion** only when:

1. **100% Execution Success**: All 5 flights complete execution without unhandled errors or collisions (`execution_result == "PASS"`).
2. **20/20 Cell Matrix Traversal**: All 20 lifecycle cells across the 5 paths are explicitly verified (`advancement_matrix_20_cells == 20 TRUE`).
3. **Exact Commit HEAD Binding**: All flight evidence is bound to the exact 40-character commit SHA (`git rev-parse HEAD`), rejecting short or stale SHAs.
4. **100% Platform Test Pass Rate**: Full test suite passes without regressions.
5. **Cryptographic Receipt Persistence**: `MultiSessionVelocityReceipt` and reconvergence evidence package are signed and persisted.

---

## 5. Execution & Verification Loop

```text
C2 CONTROL TOWER / JULES SESSION
  │
  ├── 1. REGISTER SESSIONS (C2 Tower + Jules Session)
  ├── 2. LOCK TARGET NAMESPACES (FlightCollisionLockManager)
  ├── 3. TRAVERSE 20-CELL MATRIX (Stage 1 -> Stage 2 -> Stage 3 -> Stage 4)
  ├── 4. EVALUATE ROLLS-ROYCE QUALITY STANDARD (Tests + Exact SHA)
  ├── 5. RELEASE LOCKS & SYNTHESIZE RECONVERGENCE
  └── 6. PERSIST Cryptographic Evidence Receipt
```

---

## Final Directive

> Full velocity execution and Rolls-Royce precision are mutually reinforcing: concurrency without isolation causes collision; speed without verification causes drift. Multi-session velocity is achieved when parallel execution operates within strict non-overlapping boundaries, exact SHA binding, and 100% test-proven evidence.
