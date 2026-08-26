# SAGE MULTI-SESSION VELOCITY WORKFLOW & ROLLS-ROYCE QUALITY PROTOCOL

**Status:** Governing multi-session execution workflow
**Authority:** SAGE C2 Operating Contract + Git/main truth + `docs/governance/SAGE_ROLLS_ROYCE_ENGINEERING_STANDARD.md` + `docs/governance/SAGE_C2_MULTI_SESSION_EXECUTION_PROTOCOL.md`

## Purpose

This document operationalizes full velocity multi-session execution between C2 Control Tower and parallel Jules execution sessions under the Rolls-Royce Engineering Quality Standard.

It defines the non-blocking anti-collision locking, 20-cell lifecycle matrix advancement, exact commit SHA evidence binding, and mandatory C2 self-check required for parallel Big Jump Waves.

---

## 1. Multi-Session Roles & Topology

Multi-session Big Jump Waves operate across two explicit station roles:

1. **C2 Control Tower (`C2_CONTROL_TOWER`)**:
   - Maintains complete repository state awareness.
   - Authorizes candidate frontiers and verifies non-overlapping target boundaries.
   - Synthesizes reconvergence evidence across parallel flights.
   - Runs the protocol self-check before issuing or restructuring a wave.

2. **Jules Execution Sessions (`JULES_EXECUTION_SESSION`)**:
   - Each assigned Big Jump Wave session operates one complete bounded wave, not an arbitrary subset that silently redefines wave semantics.
   - Operates assigned flight missions across independent paths.
   - Acquires non-overlapping resource locks prior to bounded build cycles.
   - Executes tests, generates evidence, and reports milestone completion.

### Canonical Capacity Rule

```text
1 Jules execution session
        =
1 Big Jump Wave
        =
up to 5 independently cleared flights
        ×
4 mandatory lifecycle gates
        =
up to 20 evidence-backed advancement cells
```

Three concurrent Jules sessions may therefore operate three independent waves in parallel, subject to Flight GPS clearance and non-overlapping ownership boundaries.

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

Every Big Jump Wave advances up to 5 independent parallel flight paths across 4 mandatory lifecycle milestone gates:

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

Advancement across a claimed full 20-cell wave is valid only when all 20 cells have explicit repository-bound evidence. Fewer safe flights are allowed, but missing flights or cells MUST be reported as unfilled, blocked, or deferred rather than fabricated as complete.

---

## 4. Rolls-Royce Engineering Quality Standard Gate

A full five-flight Big Jump Wave achieves **Rolls-Royce Completion** only when:

1. **100% Execution Success**: All 5 flights complete execution without unhandled errors or collisions (`execution_result == "PASS"`).
2. **20/20 Cell Matrix Traversal**: All 20 lifecycle cells across the 5 paths are explicitly verified (`advancement_matrix_20_cells == 20 TRUE`).
3. **Exact Commit HEAD Binding**: All flight evidence is bound to the exact 40-character commit SHA (`git rev-parse HEAD`), rejecting short or stale SHAs.
4. **100% Platform Test Pass Rate**: Full test suite passes without regressions.
5. **Cryptographic Receipt Persistence**: `MultiSessionVelocityReceipt` and reconvergence evidence package are signed and persisted.
6. **Protocol Self-Check Pass**: The dispatch and completion report conform to the canonical one-session/one-wave/five-flight/four-gate model.

---

## 5. Execution & Verification Loop

```text
C2 CONTROL TOWER / JULES SESSION
  │
  ├── 0. READ PROTOCOL + VERIFY CURRENT HEAD + SELF-CHECK WAVE SEMANTICS
  ├── 1. REGISTER SESSIONS (C2 Tower + Jules Session)
  ├── 2. LOCK TARGET NAMESPACES (FlightCollisionLockManager)
  ├── 3. TRAVERSE 20-CELL MATRIX (Stage 1 -> Stage 2 -> Stage 3 -> Stage 4)
  ├── 4. EVALUATE ROLLS-ROYCE QUALITY STANDARD (Tests + Exact SHA)
  ├── 5. RELEASE LOCKS & SYNTHESIZE RECONVERGENCE
  └── 6. PERSIST Cryptographic Evidence Receipt
```

Any mismatch between a proposed directive and this protocol is corrected before dispatch. Correction is governance work, not a fabricated completed flight cell.

---

## Final Directive

> Full velocity execution and Rolls-Royce precision are mutually reinforcing: concurrency without isolation causes collision; speed without verification causes drift. Multi-session velocity is achieved when parallel execution operates within strict non-overlapping boundaries, exact SHA binding, protocol self-checks, and 100% test-proven evidence.
