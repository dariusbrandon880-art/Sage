# SAGE C2 Five-Flight Large-Build Campaign Architecture

## Status
Architecture Doctrine

## Purpose

Define how C2/GPT coordinates multiple capability missions in parallel while preserving one governance spine, one evidence model, and one canonical SAGE state.

## Core Definition

Five Flights are reusable C2/GPT execution slots for running five independent current missions simultaneously.

They are:
- separate mission paths for the current wave
- separate capability campaigns for the current wave
- separate upgrade/PR streams where appropriate
- reusable across future waves with different mission assignments

They are not:
- independent agents
- independent authorities
- separate memory systems
- independent truth sources
- permanent departments or functional roles

## System Layout

```
                    SAGE C2 CONTROL PLANE

SENSE
RECON
SUPER SEARCH
BOUND
DECIDE
AUTHORIZE
BUILD / REPAIR / TEST
OBSERVE
VERIFY
COMPOUND

                         |
                         v

              FIVE FLIGHT EXECUTION SLOTS

 F1              F2              F3              F4              F5
 current         current         current         current         current
 mission         mission         mission         mission         mission

                         |
                         v

              SHARED GOVERNANCE FABRIC

 Evidence
 Receipts
 Tests
 Authorization
 Continuity
 Master Archive

                         |
                         v

              RECONVERGED VALIDATED STATE
```

## Flight Contract

Each flight:

1. Receives a distinct current mission from C2.
2. Defines the mission's bounded frontier.
3. Performs recon.
4. Uses Super Search where useful.
5. Builds, repairs, researches, tests, or otherwise executes whatever the current mission requires.
6. Produces evidence and receipts.
7. Passes verification.
8. Promotes only validated state.

The flight number itself never determines the kind of work performed.

## Mission Assignment

For every Big Jump Wave, C2 assigns five current missions to F1-F5.

Example:

```
Wave N
F1 -> runtime repair
F2 -> architecture investigation
F3 -> capability build
F4 -> security hardening
F5 -> verification infrastructure

Wave N+1
F1 -> research
F2 -> integration
F3 -> governance repair
F4 -> capability build
F5 -> recon
```

The same flight may receive any authorized mission on any subsequent wave.

## Full-Engine Rule

Every flight receives the same complete governed execution aperture. The mission determines which parts are causally necessary.

```
SENSE
-> RECON
-> SUPER SEARCH
-> BOUND
-> DECIDE
-> AUTHORIZE
-> BUILD / REPAIR / RESEARCH / TEST
-> OBSERVE
-> VERIFY
-> EVIDENCE
-> RECONVERGE
-> COMPOUND
```

A flight is never reduced to a permanent stage or subsystem function.

## Five Independent Paths

The five paths are independent **for the current wave**. Their target paths, files, collision zones, and mission meanings are selected per wave and may change completely on the next wave.

Safety comes from explicit mission boundaries, ownership, collision admission, exact repository HEAD binding, verification, and evidence—not from permanent functional assignment.

## Critical Distinction

```
F1 / F2 / F3 / F4 / F5
=
reusable execution identities

Current mission assignment
=
what that flight does in this wave
```

Never derive mission meaning from the flight number.

## Brain Tree Relationship

The Brain Tree is the cognitive substrate receiving campaign outputs:

```
Research Graph
      |
Evidence Evaluation
      |
Cognitive State
      |
Decision Object
      |
Authorization Boundary
      |
Execution
      |
Observation
      |
Learning Candidate
      |
Verification
      |
Validated Evolution
```

## Rolls-Royce + Lamborghini Principle

### Rolls-Royce Constraint

Protects:
- correctness
- provenance
- continuity
- safety
- evidence integrity

### Lamborghini Acceleration

Enables:
- parallel upgrades
- larger campaigns
- faster iteration
- capability composition

Rule:

> Increase jump size, not risk size.

## Promotion Path

```
Mission Selection
        |
Bound Frontier
        |
Build / Repair / Research / Test
        |
Observe
        |
Verify
        |
Receipt
        |
Master Archive Promotion
```

## Governance Invariants

- External intelligence is not canonical truth.
- Candidate knowledge is not validated knowledge.
- Recommendation is not authorization.
- Observation is not automatic learning.
- Implementation is not capability proof.
- Test passing alone is not complete evidence.
- F1-F5 have no permanent functional roles.
- Any authorized mission may be assigned to any flight.
- Parallel missions must remain distinct and reconverge through verification.
