# Architecture Index

This document serves as an exhaustive directory layout index mapping files to architectural modules.

---

## 1. Directory Layout

- **`sage/`**: The root Python package containing core runtime logic.
  - **`acr/`**: Autonomous Continuity Runtime state linkage.
  - **`archive/`**: Permanent Master Archive data structures and file persistence.
  - **`config/`**: System configuration, environment loaders, and parameters.
  - **`memory/`**: Unified memory layers and short-term laboratory buffers.
  - **`runtime/`**: Execution loop engines and orchestrators.
  - **`c2/evidence/`**: Local Integrity Kernel evidence schema, append-only registry, and fail-closed reconvergence validation.
- **`tests/`**: Automated verification suite checking unit and integration features.
- **`docs/`**: Operational control snap-shots and logs.
  - **`master/`**: Snapshots, snapshot archives, command center logs, and active session sprints.
  - **`labs/`**: Specialized engineering, research, business, and validation logs.
- **`Main Archive/`**: Permanent immutable facts, strategic roadmap locked files, research specifications, and ADR history.

## 2. Local Integrity Boundary

The C2 execution path is now explicitly separated into four authority layers:

1. **C2 intent** — mission, authorization, ordering, and target identity.
2. **Flight execution** — bounded work performed against an exact checkout.
3. **Local Integrity Kernel (`sage/c2/evidence/`)** — exact execution-tuple and independently observed artifact-digest verification.
4. **Reconvergence/promotion** — all required fronts must reach `RECEIPT_VALID` before a merge/promotion decision is admissible.

Flat evidence files remain historical indexes only; live gate authority is identity-addressed by wave, executed commit, and front.
