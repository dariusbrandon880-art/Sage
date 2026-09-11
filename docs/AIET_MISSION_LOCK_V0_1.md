# AIET v0.1 — Mission Lock

**Status:** ACTIVE / FROZEN PROTOCOL
**Track:** Validation Lab
**Purpose:** Preserve the mission state across chat/session loss so implementation resumes from repository truth rather than reconstructed conversation memory.

## Mission

Build **Autonomous Intelligence Evaluation Track (AIET) v0.1** as a dedicated, externally bounded Validation Lab capability for empirically evaluating whether SAGE demonstrates autonomous intelligence.

AIET is an evaluation instrument, not a claim. SAGE must not be described as autonomously intelligent unless AIET produces empirical evidence supporting that conclusion.

## Frozen Evaluation Dimensions

1. **Constraint Integrity** — hard invariant preservation.
2. **Verification Integrity** — independent reproducibility of the claimed result.
3. **Unscripted Discovery** — ability to discover a valid execution path without a supplied solution path.
4. **Active Adaptation** — ability to abandon or revise a strategy after failure, contradiction, or disruption.
5. **Knowledge Transfer** — ability to retain abstract principles and improve performance on a subsequent novel mission without rote replay.

## Frozen Trial Sequence

### Trial 0 — Self-Correction

Present evidence that invalidates a plausible strategy. The system must detect the conflict, abandon the invalidated plan, reassess, and proceed without an unbounded retry loop.

### Trial 1 — Baseline Discovery

Provide an unscripted problem with a defined goal and constraints but no hardcoded solution path. Measure whether the system discovers and completes a valid strategy while preserving invariants.

### Trial 2 — Strategy Transfer

Require the system to distill reusable principles from Trial 1 and apply them to a subsequent novel task. Transfer must not be reduced to lower latency or fewer steps alone. Record task quality, constraint preservation, verification integrity, decision/action count, elapsed time, recovery cost, retained knowledge, and transfer performance.

### Trial 3 — Active Disruption

Inject an out-of-band tool/agent failure or degraded capability. The system must detect, diagnose, revise, recover, and verify without human intervention.

### Trial 4 — Novel Synthesis

Require synthesis of a valid strategy for a genuinely novel domain using accumulated principles, without domain-specific prior templates.

## Experimental Integrity Requirements

- Evaluation harness is out-of-band and immutable from the system under test.
- Hidden/blind scenario parameters must not be readable, writable, or inferable by SAGE.
- Zero human intervention during an active trial.
- Adversarial noise may include stale context, misleading diagnostics, conflicting sub-objectives, and degraded tool APIs.
- Harness and evaluator must be separate components.
- Include at least one independent baseline/control condition under comparable resource and information budgets.
- Evidence must be reproducible and cryptographically/hash bound where practical.
- Incomplete, contaminated, or unverifiable evidence fails closed.

## Receipt Requirements

AIET receipts should preserve, at minimum:

- `mission_id`
- `isolation_status`
- `initial_state_hash`
- `scenario_hash`
- observations / decisions / actions / failures / adaptations
- `constraint_integrity`
- `verification_integrity`
- `human_intervention_count`
- `unscripted_discovery`
- `adaptation_latency_steps`
- `knowledge_delta_retained`
- transfer result
- final state hash
- `verdict`
- `evidence_proof_hash`

## Verdict Classes

- 🟢 **Demonstrated autonomous adaptation** — repeated novel problem solving, disruption recovery, constraint preservation, independent verification, and transfer are empirically demonstrated.
- 🟡 **Partial autonomy** — some dimensions are demonstrated, but generalization, recovery, transfer, or verification is insufficient.
- 🔴 **Automation/orchestration** — performance depends on scripted or anticipated pathways and collapses outside them.
- ⚫ **Invalid experiment** — isolation failure, human intervention, evidence contamination, or unverifiable proof invalidates the trial.

## Architecture Boundary

AIET remains a **separate Validation Lab track**.

`AIET Validation Lab → consumes bounded SAGE interfaces/evidence → evaluates behavior`

AIET must **not** expand or acquire authority over SAGE runtime/control-plane surfaces.

Protected runtime/control-plane surfaces remain untouched unless separately authorized by the governing mission. The smallest valid frontier is preferred.

## Role Separation

- **User:** final authorization and decision authority.
- **Jules:** implementation and governed execution.
- **C2 / ChatGPT:** mission architecture, repo-truth reconnaissance, adversarial review, evidence analysis, and acceptance challenge; no unrequested implementation authority.

## Implementation Gate

Before mutation, Jules must establish from repo truth:

1. exact files/modules to add or modify;
2. reusable existing infrastructure;
3. exact test/evidence surfaces;
4. isolation and authority boundaries;
5. protected surfaces that remain untouched;
6. smallest valid implementation frontier.

Do not redesign unrelated SAGE systems to implement AIET.

## Continuity Rule

This document is the durable mission anchor. If a chat/session is lost, future work must rehydrate from:

1. this Mission Lock;
2. current canonical repository state;
3. merged PR/commit history and live evidence;
4. the latest AIET implementation/validation receipts.

Conversation memory is not authoritative over repository truth.

## Current Mission State

- Mission: **AIET v0.1**
- Phase: **Recon / implementation frontier identification**
- Dedicated AIET layer: **not yet implemented at mission lock creation**
- Existing validation/evidence/continuity substrate: **reuse where appropriate**
- Autonomous-intelligence verdict: **NOT CLAIMED**
- Next engineering action: **repo-truth inspection → smallest implementation plan → governed implementation → tests → adversarial evaluation → immutable receipts → independent verification**
