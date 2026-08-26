# SAGE C2 FRONTIER ADMISSION AND RECONCILIATION RULE

## Status

Canonical governance rule for selecting work that may enter the normal SAGE Big Jump Wave workflow.

## Purpose

SAGE must not create new execution work by treating every open pull request, branch, issue, experiment, or idea as automatically active. Historical work may be valuable, stale, superseded, research-only, blocked by dependencies, or already represented by newer canonical work.

The required control is lightweight:

> **Reconcile before expansion. Classify before dispatch. Verify before activation.**

This rule is an admission gate inside the normal Big Jump Wave workflow. It does not create another registry, approval bureaucracy, or mandatory topology.

## Canonical Frontier States

Every candidate frontier must be classified by repository and evidence reality before entering execution:

1. **ACTIVE** — currently executing against a valid, bounded target.
2. **READY** — current enough, bounded, and evidence-sufficient to enter verification or integration.
3. **RECONCILE** — potentially valuable, but stale, conflicted, stacked, or dependent on old state.
4. **RESEARCH** — idea, hypothesis, benchmark, or candidate knowledge; not implementation authority.
5. **SUPERSEDED** — replaced by newer canonical work or architecture.
6. **ARCHIVE** — historically useful, but not an active execution frontier.
7. **UNSTARTED** — distinct, valid opportunity with no implementation currently occupying the target.

A frontier state is a current classification, not a permanent identity. Repository truth may change it.

## Admission Gate

Before a candidate enters any Big Jump Wave flight:

1. Inspect repository truth and the exact current state.
2. Identify the target and its current implementation surface.
3. Check dependencies, stacked ancestry, conflicts, and collision zones.
4. Classify the candidate using the canonical frontier states.
5. Admit only a bounded mission with an explicit evidence requirement and stop condition.
6. Execute through the normal Big Jump Wave lifecycle.
7. Verify and reconverge before compounding the result into the next frontier board.

Conceptually:

REPO TRUTH
→ EXACT CURRENT STATE
→ DEPENDENCY / COLLISION CHECK
→ CLASSIFY
→ BOUND MISSION
→ EXECUTE
→ VERIFY / EVIDENCE
→ RECONVERGE / COMPOUND

## Historical Work Safety & Capability Preservation Rule

> **No historical branch is resumed merely because it exists, and closing a PR does not authorize capability deletion.**

Every substantive PR is treated as a capability-bearing artifact. Before a capability can be considered lost or discarded, C2 must evaluate its disposition through the capability extraction pipeline:

`PR → Capability Extraction → Capability Registry → Current-Main Reconciliation → Integration / Research / Retirement`

Before resuming, merging, or extracting historical work, compare it with current canonical state and determine whether it should be:

- adopted/integrated,
- recovered or reconstructed cleanly against current `main`,
- superseded by a stronger implementation,
- preserved as research,
- or retired with documented rationale.

Old base SHA, open status, or prior test success is not sufficient merge authority.

## Stacked Work Rule

Dependent pull requests or branches are treated as an explicit dependency program, not as unrelated merge candidates.

The program must be mapped before integration. Independent verification determines whether valid seams should be preserved, rebuilt against current state, or superseded by newer architecture.

## Minimal Frontier Identity

To prevent duplicate or colliding flights, each admitted target should have enough identity to establish distinction:

- `frontier_id`
- `target`
- `source`
- `state`
- `base_sha` or current repository reference
- `dependencies`
- `collision_zone`
- `evidence_required`
- `stop_condition`

This is a minimal mission identity, not a new mandatory database or permanent ledger.

## Big Jump Wave Alignment

Big Jump Wave remains the normal SAGE execution workflow.

The admission rule does not alter the canonical five-flight structure, 5×4 lifecycle model, or optional execution topology. It ensures that selected flights are genuinely distinct and grounded in current repository reality before dispatch.

Three concurrently executing five-flight waves may represent up to 15 distinct flight missions only when the underlying execution is actually active and the missions have been checked for dependency and collision overlap.

## Authority Order

Repository and Git evidence determine current implementation reality.

Research and Super Search may discover candidates, patterns, and external methods, but do not override repository truth.

## Non-Goals

This rule must not be used to introduce:

- another giant registry,
- mandatory multi-node architecture,
- additional evidence commits that create SHA recursion,
- approval chains unrelated to bounded execution risk,
- a scheduler that replaces human/C2 frontier selection,
- automatic promotion of research into implementation authority.

## Canonical Operating Rule

> **Do not expand from raw backlog count. Reconcile the frontier, classify the candidate, bound the mission, then fly distinct work with evidence.**

When uncertainty remains, classify the frontier as **RECONCILE** rather than assuming that it is READY or obsolete.
