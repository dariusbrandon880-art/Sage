# SAGE Experiment Ledger + Concurrent Wave Doctrine

**Locked:** 2026-08-29
**Status:** Strategic architecture / execution doctrine
**Authority:** subordinate to the SAGE Constitution and canonical Jigsaw architecture

## Decision

SAGE's Experiment Ledger is a first-class evidence/learning capability for recording hypotheses, baselines, candidate techniques, authorized experiments, execution lineage, observations, evidence, counterexamples, cost/risk, replication, generalization, and decisions.

The Experiment Ledger must operate **concurrently with active Big Jump Wave / Five-Flight execution whenever safe and non-conflicting**, but it must never become a second command path, block authorized flights unnecessarily, mutate active mission state, or contaminate experiment evidence.

## Organism placement

`SAGI Brain → C2 Mission Control → Big Jump Wave → Five Flights / experiment cells → Experiment Ledger + evidence → Validation → Capability Warehouse / Archive → frontier update → SAGI`

SAGI discovers and proposes hypotheses. C2 frames, bounds, and authorizes. Flights execute bounded work. The Experiment Ledger observes and records the experiment/evidence state. Validation determines whether a result is trustworthy. Promotion/warehouse retention occurs only through existing authority.

## Concurrent execution rule

The Experiment Ledger is an **orthogonal observability/learning lane**, not a sixth flight and not a replacement for the five-flight system.

It may run alongside active flights when all of the following are true:

- it has a clearly bounded scope;
- it does not modify the active flight's authoritative state;
- it does not consume a contested execution slot needed by an authorized flight;
- it does not weaken evidence isolation or temporal boundaries;
- its inputs are immutable snapshots, receipts, or explicitly authorized observations;
- failures in the ledger lane fail closed and do not silently alter mission execution;
- reconciliation occurs against the exact mission/commit/flight identity.

If concurrency would create collision, contamination, ambiguity, or resource contention, C2 defers the ledger work rather than compromising the active wave.

## What runs concurrently

Where supported, the ledger lane may perform:

1. experiment registration;
2. baseline/metric binding;
3. receipt ingestion;
4. trajectory/evidence indexing;
5. failure localization;
6. counterexample collection;
7. candidate-technique comparison;
8. post-flight replication planning;
9. longitudinal metric updates.

These are observation/analysis activities unless explicitly promoted into a separately authorized execution mission.

## What must NOT run concurrently without explicit authorization

- mutation of authoritative mission state;
- promotion of capabilities;
- changes to constitutional/Jigsaw authority;
- changes to active flight objectives;
- evidence rewriting;
- synthetic outcome insertion;
- unbounded experimental branching against production state;
- resource capture that starves authorized flights;
- automatic deployment of a newly inferred technique.

## Experiment record

A serious experiment should preserve, where applicable:

- hypothesis;
- baseline;
- candidate technique;
- preconditions;
- authorization identity;
- mission / wave / flight identity;
- exact commit or state reference;
- execution lineage;
- observations;
- evidence references and hashes;
- counterexamples;
- cost and risk;
- outcome;
- replication status;
- generalization status;
- validation decision;
- promotion/rollback decision.

## State-aware design

The ledger should preserve execution state and lineage rather than acting as generic semantic memory. Long-horizon research indicates that state-aware memory, branch integrity, validation of summaries, and revision boundaries are materially important for reliable agent execution.

Therefore, ledger records must distinguish active authoritative state from historical observations and rejected branches. A failed or superseded experiment must remain inspectable without becoming active truth.

## Evidence-first scientific loop

`Hypothesis → Baseline → Authorized Experiment → Observation → Evidence → Counterexample Search → Replication → Generalization → Validation → Promotion/Reject → Frontier Update`

A single successful outcome does not establish a reusable technique.

## Workflow preservation rule

This doctrine **does not alter the existing Big Jump Wave workflow**. The five concurrent flights remain the primary bounded execution mechanism. The Experiment Ledger is an orthogonal support/learning lane that improves visibility and compounding without inserting a new command layer.

If a conflict exists between ledger work and an already-authorized flight, protect the flight and defer or narrow ledger work.

## Safety / fail-closed boundary

The ledger must never be treated as evidence merely because a record exists. Receipts must bind to actual execution identity and immutable source evidence. Missing, contradictory, stale, or unverifiable evidence produces `HOLD`, not inferred success.

## Strategic objective

The long-term objective is to make SAGE an organism that can continuously reduce uncertainty about how to perform useful work better, while keeping command authority, execution, observation, validation, and promotion distinct and auditable.

> **Run the experiment lane alongside the wave when it is orthogonal and safe; never let learning infrastructure interfere with the mission it exists to improve.**
