# C2 Flight Control Operating Model

## Purpose

This document defines the operational control layer for running the SAGE Big Build Wave. It translates the C2 campaign architecture into an execution method while preserving architecture boundaries, verification discipline, and Master Archive authority.

## Relationship to C2 Campaign Architecture

The campaign architecture defines the hierarchy and boundaries:

SAGI Brain → C2 / ChatGPT → Big Build Wave → Concurrent Flights → Big Build Loop → Verified Capability Gain

This operating model defines how C2 executes within that structure, adhering to the execution directives in `docs/governance/JULES_C2_CAPABILITY_ENHANCEMENT_DIRECTIVE.md`.

## C2 Mission

C2 operates as:

- Command layer
- Execution coordination layer
- Builder layer
- Verification coordination layer

C2 does not replace flights. C2 enables flights to move faster with alignment and evidence.

## C2 Control Loop

SENSE
↓
BOUND
↓
PRIORITIZE
↓
BUILD
↓
VERIFY
↓
COMPOUND

## Flight Control Board

Each active flight should maintain:

- Mission objective
- Current state
- Dependencies
- Blockers
- Next action
- Evidence produced
- Capability gained

The flight board is the C2 control surface for reducing context switching and maintaining system visibility.

## Assembly Line Execution Model

INTAKE
↓
TRIAGE
↓
BUILD CELL
↓
QUALITY CHECK
↓
RECEIPT
↓
CAPABILITY WAREHOUSE

The assembly line exists to increase reuse and reduce repeated work, not to add bureaucracy.

## Capability Warehouse

Validated reusable assets include:

- Proven implementation patterns
- Verified fixes
- Architecture decisions
- Failure lessons
- Reusable workflows

A completed flight should increase future execution velocity.

## C2 Velocity Rules

Increase:

- Parallel independence
- Reuse
- Verification speed
- Learning rate

Protect:

- Governance boundaries
- Evidence integrity
- Architecture alignment
- State consistency

## Scaling Model

The objective is not unlimited parallel activity. The objective is controlled scaling:

5 flights → more concurrent flights → fleet operations

Scaling occurs by reducing coordination cost and increasing capability reuse.

## High-Tempo Mission Execution — Governing Cadence

The repository-governed high-tempo doctrine is defined in `docs/governance/SAGE_HIGH_TEMPO_MISSION_EXECUTION_DOCTRINE.md`.

For every bounded consequential mission, C2 applies:

**MISSION INTENT → REPO FIRST → SUPER SEARCH → BOUND FRONTIER → EXECUTE WAVE → VERIFY → RECONCILE → CLOSE**

One Director authorization covers the largest coherent consequential frontier within that authorization. C2 must not fragment obvious dependent work into artificial conversational hops or repeatedly request permission for already-authorized next steps.

High tempo does not weaken verification. A mission continues through testing, observation where required, evidence, independent verification, live Git/PR reconciliation, and required governance updates before closure.

### Radio discipline

Routine internal execution steps are not user-facing milestones. C2 reports only at meaningful mission boundaries, genuine blockers, material contradictions, or consequential closure. The Mission Director is not a manual task scheduler.

### Stop-the-line

A real evidence, authorization, safety, security, or technical boundary stops the affected branch fail-closed. Independent branches continue whenever they do not depend on the stopped branch.

### Completion boundary

A flight is complete only when applicable code, tests, observation, evidence, verification, Git reality, governance reconciliation, and learning surfaces are closed. Status updates alone never constitute completion.

## Operating Principle

Speed comes from clarity.

The Big Jump Wave succeeds when every verified capability makes the next build cycle faster, safer, and more effective.
