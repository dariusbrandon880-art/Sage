# SAGE C2 EXECUTION PROTOCOL

## Multi-Session Big Jump Operating Model (v1.3)

## 1. Hierarchy of Authority

1. Repository Truth: canonical Git HEAD, refs, and tree state.
2. Flight GPS telemetry receipts: machine-readable clearance records.
3. Execution evidence: validated tests, builds, and reports.
4. Chat/generated summaries: non-canonical context requiring verification.

## 2. Operational Roles

- C2 Control Tower: verifies reality, classifies airspace, coordinates execution, protects governance boundaries, and self-checks proposed dispatches against this protocol before issuing them.
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

### Wave Semantics — Non-Negotiable

A **Big Jump Wave** is one bounded execution unit containing exactly up to 5 flight slots. Each flight slot advances independently through 4 mandatory lifecycle gates:

1. RECON / BOUND
2. BUILD / REPAIR
3. TEST / OBSERVE
4. VERIFY / COMPOUND

Therefore, one full wave has a maximum of **5 flights × 4 gates = 20 advancement cells**.

A Jules session assigned a Big Jump Wave owns one complete 5-flight wave unless repository evidence or available capacity explicitly reduces the number of safe flight slots. Three concurrent Jules sessions therefore mean three independent waves, each independently bounded and cleared; they do **not** redefine a single wave into three arbitrary single-focus tasks.

Advancement requires machine-readable evidence attached to the flight manifest. A lifecycle cell MUST NOT be claimed complete merely because a plan, chat response, or agent report says it is complete.

### Session Topology

- **One execution session = one Big Jump Wave.**
- **One Big Jump Wave = up to five cleared flights.**
- **One full five-flight wave = twenty evidence-backed lifecycle cells.**
- Separate sessions MUST acquire non-overlapping ownership boundaries or be classified SHARED/DEPENDENT/OCCUPIED and routed accordingly.

## 5. Mandatory C2 Self-Check Gate

Before C2 issues, expands, splits, merges, or recommends any Big Jump Wave directive, it MUST evaluate the proposed action against this protocol.

The self-check MUST confirm:

1. **Repository Truth:** current canonical HEAD and active PR/branch state have been observed.
2. **Protocol Truth:** the directive preserves the one-session/one-wave/up-to-five-flights/four-gates model.
3. **Flight GPS Truth:** airspace and observability permit dispatch.
4. **Ownership Truth:** each proposed flight has a non-conflicting ownership fingerprint or an explicit SHARED/DEPENDENT handling rule.
5. **Completion Truth:** no cell or flight is represented as complete without repository-bound evidence.
6. **Duplication Truth:** completed or integrated capability is not reopened or reimplemented without evidence requiring recovery.

If any required check is unknown, contradictory, or unavailable, C2 MUST fail closed for that affected dispatch boundary rather than silently inventing a new workflow structure.

### Drift-Correction Rule

If C2 detects that a proposed directive conflicts with repository protocol, the directive MUST be corrected before dispatch. The correction itself does not constitute a completed flight cell and MUST NOT be reported as repository execution unless an actual repository mutation and verification occurred.

## 6. Failure and Recovery Doctrine

- Telemetry failure never implies empty airspace.
- STALE entries require probe-before-reclaim verification.
- Capability lineage is preserved after reclamation.
- OCCUPIED targets are bypassed and safe frontiers are selected.
- Local success does not equal merge readiness; repository and CI evidence remain authoritative for integration.

## Session Initialization

Initialize SAGE C2 Control Tower. Read this protocol, verify canonical Git HEAD, inspect active work, run the Mandatory C2 Self-Check Gate, and check Flight GPS clearance before proposing or dispatching work.
