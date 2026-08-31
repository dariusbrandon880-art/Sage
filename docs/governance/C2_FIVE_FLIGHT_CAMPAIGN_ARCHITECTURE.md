# SAGE C2 Campaign Architecture

## Purpose

Define how SAGE organizes capability execution through the canonical **Big Jump Wave** while preserving Master Archive authority, authorization boundaries, evidence discipline, continuity, and fail-closed execution.

This document defines coordination architecture. It does not create active work items.

## Critical Rule: Five Flights Have No Permanent Jobs

F1, F2, F3, F4, and F5 are **reusable execution slots**.

They are not permanent departments, frontiers, lifecycle stages, or capabilities.

Before each wave, C2 performs repository/context recon, evidence review, frontier selection, and authorization. Only then are five current missions assigned to the five slots.

On a later wave, the same five slots may receive completely different missions.

## Canonical C2 Operating Loop

```text
SENSE
RECON
SUPER SEARCH
BOUND THE CURRENT MISSION
DECIDE
AUTHORIZE
BIG JUMP WAVE
BUILD / REPAIR / RESEARCH / TEST AS ASSIGNED
OBSERVE
VERIFY
RECONVERGE
COMPOUND
```

**Big Jump Wave is the normal SAGE execution workflow.**

## C2 FIVE-FLIGHT MODEL

```text
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼
       F1       F2       F3       F4       F5
        |        |        |        |        |
   Mission  Mission  Mission  Mission  Mission
      A        B        C        D        E
        \        |        |        |        /
                 ▼
          C2 RECONVERGENCE
          Evidence + Receipts
          Promotion Gate
```

The labels A-E are intentionally placeholders: the current mission is selected for each slot by C2 for that wave.

A flight is an independent capability execution vector with its own current objective, target boundary, tests, evidence, and milestone reporting.

A flight may perform any authorized kind of work, including research, reconnaissance, implementation, repair, testing, governance/security hardening, architecture investigation, evidence work, integration, or capability construction.

## Mission Assignment Contract

Every Big Jump Wave assigns exactly five current missions:

```text
Flight: F1 | F2 | F3 | F4 | F5
Mission:
Target Boundary:
Dependencies:
Collision Scope:
Authorization:
Tests:
Evidence:
Completion Criteria:
```

The flight identifier is an address for the reusable execution slot. Mission meaning belongs only to the current assignment.

## Safety Model

The flights are separate because their **current mission boundaries** are separately admitted and reconciled—not because each flight is permanently restricted to one kind of work.

Safety comes from explicit target boundaries, ownership fingerprints, collision admission, dependency checks, exact repository HEAD binding, independent verification, and evidence.

## 5x4 Lifecycle Matrix

The Big Jump Wave retains the 20-cell model:

**5 reusable mission slots x 4 lifecycle stages = 20 advancement cells.**

```text
                    INTAKE       BUILD       VERIFY       RECONVERGE
F1                  current      current     current      current
F2                  mission      mission     mission      mission
F3                  assignment  assignment  assignment  assignment
F4
F5
```

The matrix tracks the current wave assignment. It does not assign permanent meaning to a flight number.

## C2 Role

C2:

- establishes repository truth;
- discovers the highest-leverage current missions;
- assigns five independent missions;
- prevents duplicate work and collisions;
- protects validated architecture;
- requires exact-head evidence;
- verifies capability delta;
- reconverges and promotes only validated capability.

## Jules Integration

Jules is the governed engineering execution station and may receive **any** of the five mission types.

Every Jules flight report identifies:

```text
Flight:
Current Mission:
Target Boundary:
Changes:
Tests:
Evidence:
Capability Gained:
Next Move:
```

Jules must never infer a permanent functional role from F1-F5.

## Execution Law

```text
F1 ─┐
F2 ─┤
F3 ─┼─> CURRENT WAVE MISSIONS -> VERIFY -> RECONVERGE
F4 ─┤
F5 ─┘
```

The five paths execute concurrently when admitted. Their work can be completely different, and their assignments can be completely reshuffled on the next wave.

## Governance / Rolls-Royce Standard

Parallelism never weakens quality.

```text
EXECUTION
-> EVIDENCE
-> VERIFY
-> VALIDATE
-> ACTION-BOUND AUTHORIZATION
-> PROMOTE
```

Failures, stale SHAs, collisions, incomplete proof, and ambiguous state fail closed.

## Capability Advancement Gate

A green matrix, receipt, or test result is not capability by itself.

Each current mission must establish:

```text
BASELINE
-> TARGET
-> CONCRETE CHANGE
-> DEDICATED VERIFICATION
-> EVIDENCE
-> REUSABLE OUTPUT
-> RECONVERGENCE
-> PROMOTION
```

No-net-delta work must not be inflated into velocity.

## Deep Recon / Super Search

Super Search is a reconnaissance sensor, not canonical authority. C2 establishes repository truth first, then uses targeted external intelligence when it can materially change mission selection, implementation, security, or verification.

External findings remain candidate intelligence until validated.

## Adaptive Evolution

SAGE may learn from wave receipts, verification latency, collisions, rework, and capability gain to improve future **mission selection and slot assignment**.

Learning may propose future assignments. It may not silently change authority or promote itself.

## Anti-Drift Rules

- F1-F5 are never permanent functional roles.
- Never infer mission meaning from flight number.
- Never collapse five separate missions into one shared task.
- Never overwrite another flight's admitted boundary.
- Never use stale evidence as current proof.
- Never claim unperformed work.
- Never promote without verification and evidence.
- Never replace the Big Jump Wave frame merely to increase throughput.

## Operating Principle

**Five reusable flights. Five separately chosen missions. Concurrent execution. Safe separation. One reconvergence gate.**

The mission changes. The slot does not acquire a permanent job.
