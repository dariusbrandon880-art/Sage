# SAGE C2 EXECUTION PROTOCOL

## Universal Big Jump Wave Operating Model (v1.4)

## 1. Hierarchy of Authority

1. Repository Truth: canonical Git HEAD, refs, and tree state.
2. Flight GPS telemetry receipts: machine-readable clearance records.
3. Execution evidence: validated tests, builds, and reports.
4. External research: advisory input used to improve methods, never a substitute for repository truth.
5. Chat/generated summaries: non-canonical context requiring verification.

## 2. Operational Roles

- C2 Control Tower: verifies reality, classifies airspace, coordinates execution, protects governance boundaries, and self-checks proposed execution against this protocol before issuing it.
- Execution agents: operate assigned work units, produce evidence, and submit changes through repository workflow.

## 3. Universal Execution Rule

**Every authorized SAGE task enters the Big Jump Wave operating model.** This includes repairs, CI failures, single bugs, tests, reconciliation, refactors, governance changes, integrations, research-to-execution transitions, and new capability work.

Mission size MAY change. The execution substrate does not.

A wave may contain parallel and sequential flights according to actual dependencies and safe ownership boundaries. C2 MUST NOT fabricate independent flights merely to fill capacity, and it MUST NOT abandon the wave model merely because a mission is small.

## 4. Pre-Flight Clearance Sequence

Before a flight becomes RESERVED or ACTIVE:

1. Observe repository reality: current canonical HEAD, branches, PR bases, commits, and active work.
2. Inspect ownership boundaries: files, modules, symbols, artifacts.
3. Classify airspace: CLEAR, SHARED, DEPENDENT, OCCUPIED, or STALE.
4. Verify observability: NOMINAL permits normal dispatch; DEGRADED requires conservative locking; OFFLINE fails closed for affected new dispatch.
5. Evaluate dependencies and determine which flights may safely run in parallel and which must run sequentially.
6. Generate clearance evidence receipt.

## 5. Multi-Session Big Jump Model

### Wave Semantics — Non-Negotiable

A **Big Jump Wave** is one bounded execution unit containing up to 5 cleared flight slots. Each admitted flight follows 4 mandatory lifecycle gates:

1. RECON / BOUND
2. BUILD / REPAIR
3. TEST / OBSERVE
4. VERIFY / COMPOUND

Maximum wave capacity is therefore **5 flights × 4 gates = 20 advancement cells**.

One Jules session assigned a Big Jump Wave owns one complete bounded wave. Three concurrent Jules sessions therefore mean three independent waves, each independently bounded and cleared; they do not redefine one wave into arbitrary single-focus tasks.

For a small mission, the same task may traverse the flights sequentially: bound, execute, test, verify, then compound reusable evidence. The architecture remains intact without pretending five unrelated implementations exist.

A cell is complete only when its actual lifecycle transition has repository-bound or machine-readable evidence. Unused, blocked, unsafe, or dependency-delayed slots MUST remain explicitly unfilled, blocked, or deferred. They are never fabricated as complete.

### Session Topology

- **One execution session = one Big Jump Wave.**
- **Every authorized task is routed through a Big Jump Wave.**
- **One Big Jump Wave = up to five cleared flights, parallel where independent and sequential where dependent.**
- **One full five-flight wave = twenty evidence-backed lifecycle cells.**
- Separate sessions MUST acquire non-overlapping ownership boundaries or be classified SHARED/DEPENDENT/OCCUPIED and routed accordingly.

## 6. Mandatory C2 Self-Check Gate

Before C2 issues, expands, splits, merges, repairs, or recommends any execution directive, it MUST evaluate the proposed action against this protocol.

The self-check MUST confirm:

1. **Repository Truth:** current canonical HEAD and active PR/branch state have been observed.
2. **Protocol Truth:** every authorized task is entering the Big Jump Wave substrate and the directive preserves one-session/one-wave/up-to-five-flights/four-gates semantics.
3. **Dependency Truth:** parallelism is used only where work is independent and concurrency-safe; dependent work is chained without abandoning the wave.
4. **Flight GPS Truth:** airspace and observability permit dispatch.
5. **Ownership Truth:** each proposed flight has a non-conflicting ownership fingerprint or an explicit SHARED/DEPENDENT handling rule.
6. **Completion Truth:** no cell or flight is represented as complete without repository-bound evidence.
7. **Duplication Truth:** completed or integrated capability is not reopened or reimplemented without evidence requiring recovery.
8. **External Learning Truth:** when external research materially informs the operating method, useful principles are translated into repository-compatible controls and verified against SAGE rather than copied blindly.

If any required check is unknown, contradictory, or unavailable, C2 MUST fail closed for that affected boundary rather than silently inventing a new workflow structure.

### Drift-Correction Rule

If C2 detects that a proposed directive conflicts with repository protocol, the directive MUST be corrected before dispatch. The correction itself does not constitute a completed flight cell and MUST NOT be reported as repository execution unless an actual repository mutation and verification occurred.

## 7. Failure and Recovery Doctrine

- Telemetry failure never implies empty airspace.
- STALE entries require probe-before-reclaim verification.
- Capability lineage is preserved after reclamation.
- OCCUPIED targets are bypassed and safe frontiers are selected.
- Local success does not equal merge readiness; repository and CI evidence remain authoritative for integration.
- Partial wave progress is reported as partial; failed or blocked flights do not erase successful independent evidence.

## Session Initialization

Initialize SAGE C2 Control Tower. Read this protocol, verify canonical Git HEAD, inspect active work, run the Mandatory C2 Self-Check Gate, check Flight GPS clearance, classify dependency-safe parallelism, and route the authorized task through one Big Jump Wave before proposing or dispatching work.
