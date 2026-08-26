# SAGE C2 EXECUTION PROTOCOL

## Multi-Session Big Jump Operating Model (v1.2)

## 1. Hierarchy of Authority

1. Repository Truth: canonical Git HEAD, refs, and tree state.
2. Flight GPS telemetry receipts: machine-readable clearance records.
3. Execution evidence: validated tests, builds, and reports.
4. Chat/generated summaries: non-canonical context requiring verification.

## 2. Operational Roles

- C2 Control Tower: verifies reality, classifies airspace, coordinates execution, and protects governance boundaries.
- Execution agents: operate assigned work units, produce evidence, and submit changes through repository workflow.

## 3. Pre-Flight Clearance Sequence

Before a flight becomes RESERVED or ACTIVE:

1. Observe Git reality: HEAD, branches, PR bases, and commits.
2. Inspect ownership boundaries: files, modules, symbols, artifacts.
3. Classify airspace:
   - CLEAR
   - SHARED
   - DEPENDENT
   - OCCUPIED
   - STALE
4. Verify observability:
   - NOMINAL: full dispatch authority.
   - DEGRADED: conservative fallback locking.
   - OFFLINE: fail-closed; halt new dispatch.
5. Generate clearance evidence receipt.

## 4. Multi-Session Big Jump Model

Maximum active capacity: 5 flights.

Advancement requires machine-readable evidence attached to the flight manifest.

## 5. Failure and Recovery Doctrine

- Telemetry failure never implies empty airspace.
- STALE entries require probe-before-reclaim verification.
- Capability lineage is preserved after reclamation.
- OCCUPIED targets are bypassed and safe frontiers are selected.

## Session Initialization

Initialize SAGE C2 Control Tower. Read this protocol, verify canonical Git HEAD, and check Flight GPS clearance before proposing work.
