# SAGE 60/40 Hardening Era Doctrine

**Locked:** 2026-08-29
**Status:** Strategic operating doctrine
**Authority:** subordinate to the SAGE Constitution, canonical Jigsaw architecture, C2 mission authority, and live repository truth.

## Intent

SAGE enters a deliberate hardening era while continuing necessary advancement. The allocation is **60% hardening / verification / reliability** and **40% necessary advancement / frontier capability**.

This is not a feature freeze, redesign, or new authority layer. It is a resource-allocation doctrine for the existing SAGE organism.

## Core rule

> Build less by default. Prove more. Break it harder. Recover better. Repeat.

No new capability should be added merely because it is interesting. Advancement earns priority when it closes a demonstrated reliability gap, satisfies a real customer need, provides a required dependency, or is a high-value research experiment authorized by C2.

## 60% HARDEN

Harden the existing organism across:

- architecture and dependency integrity;
- state, continuity, replay, recovery, and reconciliation;
- C2 anti-drift and mission-boundary enforcement;
- SAGI-to-C2-to-Flight handoff integrity;
- Five-Flight isolation and concurrency;
- evidence lineage, immutability, freshness, and deterministic receipts;
- adversarial verification and promotion-gate resistance;
- runtime reliability, resource behavior, and long-horizon execution;
- duplicate-authority and bypass detection;
- Capability Warehouse validity, reuse, rollback, and retirement;
- reproducibility, baseline comparison, and trajectory-level evaluation.

Hardening work must attack real existing surfaces rather than manufacture complexity for its own sake.

## 40% NECESSARY ADVANCEMENT

Advance only when justified by:

1. a demonstrated failure or missing control;
2. a required dependency for validation or customer work;
3. a real customer workflow or measurable value opportunity;
4. a high-value SAGI research hypothesis approved for controlled experimentation;
5. an evidence-backed opportunity with unusually high capability leverage.

The 40% lane must remain subordinate to the same Jigsaw boundaries and cannot become a loophole for uncontrolled feature accumulation.

## Organism-wide execution model

SAGI, C2, Flights, Evidence/Learning, Warehouse, Research, and Business are one organism with distinct functions:

`SAGI discovers/researches -> C2 frames/bounds/authorizes -> Flights execute -> Evidence observes/verifies -> Validation determines truth -> Warehouse/Archive preserves validated capability -> SAGI updates the frontier.`

No component may create a parallel C2, state, workflow, evidence, or promotion authority.

## Concurrent operation

The 60/40 doctrine may run concurrently with active Five-Flight waves where tooling and resource constraints permit.

- Hardening is not Flight 6.
- The Experiment Ledger is not a command authority.
- Independent work may proceed in parallel only when boundaries do not conflict.
- Active flight execution takes precedence if resource contention or evidence contamination appears.
- Concurrency must be evidenced; never claim parallel execution without actual evidence.

## Measurement doctrine

SAGE must measure improvement beyond binary task success. For important missions, evaluate:

- outcome quality;
- process/trajectory quality;
- consistency across repeated runs;
- robustness under perturbation;
- predictability and bounded failure;
- safety and boundary compliance;
- recovery/reconciliation quality;
- resource cost and efficiency;
- evidence quality and lineage;
- generalization across mission classes.

A lucky pass is not a mastered technique.

## Technique mastery ladder

`Outcome success -> technique candidate -> repeatable technique -> validated technique -> promoted capability`

Promotion requires explicit evidence. A single successful run, self-reported completion, or unverified benchmark result cannot establish doctrine.

## Scientific validation

Research hypotheses may draw from distributed computing, mathematics, quantum information, biology, scientific computing, and HPC. These are hypothesis sources, not new SAGE organs.

The controlled loop is:

`Hypothesis -> Baseline -> Experiment -> Observation -> Counterexample search -> Replication -> Independent evidence -> Validation -> Authorized promotion.`

## External research alignment

The doctrine is informed by current agent-reliability research showing that final outcomes alone can hide trajectory failures, lucky passes, unsafe intermediate actions, and long-horizon instability. Recent work emphasizes trajectory-level diagnosis, process-vs-outcome verification, consistency/robustness measurement, and stronger validation infrastructure. SAGE should therefore treat execution trajectories and evidence as first-class validation material rather than relying on final-task success alone.

## Business alignment

Hardening is itself customer-value work when it improves reliability, recoverability, evidence, auditability, efficiency, or deployment trust. The business loop remains:

`Customer workflow -> observed need/failure -> technique candidate -> controlled validation -> measured outcome -> authorized promotion -> reusable capability.`

## Anti-drift rule

This doctrine does not override live repo truth. At every major execution boundary, C2 must rehydrate exact HEAD, current mission state, active work, evidence, and architecture before acting.

If evidence contradicts this doctrine, preserve the evidence, stop the affected promotion, and revise the hypothesis rather than forcing the system to fit the plan.

> **60% make what exists harder to break. 40% advance only where evidence says the organism needs to move.**
