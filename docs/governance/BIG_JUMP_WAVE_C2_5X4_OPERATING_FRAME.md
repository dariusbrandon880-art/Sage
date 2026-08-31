# BIG JUMP WAVE C2 5x4 OPERATING FRAME

**Status:** Governing workflow extension
**Authority:** SAGE C2 Persistent Operating Contract + Git/main truth + validated Master Archive

## Purpose

The Big Jump Wave is SAGE's primary parallel execution frame. It coordinates five independent flights that execute five separately assigned missions and then reconverge under C2 verification.

The five flight identifiers are **reusable execution slots**. They are not permanent departments, capabilities, frontiers, or workflow stages.

## Core Model

```text
                         C2 MISSION CONTROL
                                  |
                 +----------------+----------------+
                 |                |                |
                 v                v                v
              F1 / F2 / F3 / F4 / F5
                 |                |                |
                 +----------------+----------------+
                                  |
                     FIVE CURRENT MISSIONS
                    assigned independently
                                  |
                                  v
                         CONCURRENT EXECUTION
                                  |
                     collision / ownership guard
                                  |
                                  v
                          C2 RECONVERGENCE
                                  |
                         VERIFY + EVIDENCE
                                  |
                         PROMOTION GATE
```

## Flight Identity Rule — Canonical

**F1, F2, F3, F4, and F5 are generic reusable mission slots.**

No slot has a permanent functional role.

A flight may be assigned any authorized mission, including but not limited to:

- research;
- reconnaissance;
- implementation;
- repair;
- testing;
- governance/security hardening;
- architecture investigation;
- evidence capture;
- capability construction;
- integration or convergence work.

The assignment can change completely on the next wave.

For example:

```text
Wave N:
F1 -> repair runtime
F2 -> investigate architecture
F3 -> build capability
F4 -> security hardening
F5 -> verification

Wave N+1:
F1 -> governance repair
F2 -> research
F3 -> integration
F4 -> test infrastructure
F5 -> capability build
```

The flight number remains stable only as an execution/reconciliation identity. **Mission meaning belongs to the current `FlightMissionSpec`, never to F1-F5 themselves.**

## Mission Assignment Contract

Every Big Jump Wave supplies exactly five current mission assignments. Each assignment contains:

```text
Flight ID: F1 | F2 | F3 | F4 | F5
Mission Name:
Target Path:
Collision Zone:
Evidence Reference:
PR / Change:
Test References:
```

The engine must reject missing mission assignments and must fail closed on invalid or duplicate flight slots.

A wave must never derive mission meaning from the flight number.

## Five Independent Paths

The five flights execute independently and concurrently. Their target paths and collision zones are selected for the **current wave** and may be completely different on the next wave.

Safety comes from explicit mission boundaries, ownership fingerprints, collision admission, exact repository HEAD binding, verification, and evidence—not from permanently assigning work categories to flight numbers.

## 5x4 Lifecycle Matrix

The Big Jump Wave retains its 20-cell advancement model:

**5 concurrent mission slots x 4 lifecycle stages = 20 advancement cells.**

```text
STAGE 1             STAGE 2          STAGE 3          STAGE 4
Intake & Recon      Build            Verify & Proof   Reconverge / Promote

F1 current mission  -> ... -> ... -> ...
F2 current mission  -> ... -> ... -> ...
F3 current mission  -> ... -> ... -> ...
F4 current mission  -> ... -> ... -> ...
F5 current mission  -> ... -> ... -> ...
```

The matrix tracks the current mission assignment; it does **not** create permanent flight roles.

## C2 Role

C2 Mission Control:

- establishes repository reality before dispatch;
- selects the highest-leverage current missions;
- assigns five independent missions to F1-F5;
- protects against collisions and semantic drift;
- requires exact-head evidence;
- verifies net capability delta;
- reconverges the wave;
- promotes only validated reusable capability.

## Jules Integration

Jules is the governed engineering execution station. Jules may receive any of the five mission assignments.

A Jules flight report identifies:

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

## Execution Loop

```text
SENSE
-> RECON
-> SUPER SEARCH (when materially useful)
-> ASSIGN CURRENT MISSIONS
-> BUILD / REPAIR / RESEARCH / TEST AS ASSIGNED
-> OBSERVE
-> VERIFY
-> RECONVERGE
-> COMPOUND
```

## Governance / Rolls-Royce Standard

Parallel execution never weakens the quality gate.

Every flight remains subject to:

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

Each current mission must demonstrate:

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

Super Search is a reconnaissance sensor, not canonical authority. For substantive missions, C2 first locks repository truth, then uses targeted external intelligence when it can materially change mission selection, implementation, security, or verification.

External findings remain candidate intelligence until validated against repository truth.

## Adaptive Evolution

SAGE may measure wave throughput, collision rates, verification latency, rework, and capability gain to improve future mission assignment and concurrency decisions.

Learning may propose better future assignments. It may not silently change authority or promote itself.

## Anti-Drift Rules

- Never treat F1-F5 as permanent functional roles.
- Never infer mission meaning from flight number.
- Never overwrite another current mission's protected boundary.
- Never use stale evidence as current proof.
- Never confuse concurrency with capability.
- Never claim unperformed work.
- Never promote without verification and evidence.
- Never replace the Big Jump Wave with a different execution frame merely to increase parallelism.

## Operating Principle

**Five reusable flights. Five current missions. Concurrent execution. Safe separation. One reconvergence gate.**

The mission changes. The flight slot does not acquire a permanent job.

The goal is faster verified capability with uncompromised engineering quality.
