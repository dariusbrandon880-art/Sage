# SAGE C2 BIG JUMP WAVE — 15-FLIGHT CONCURRENCY DOCTRINE

**Status:** Canonical execution doctrine

**Authority:** SAGE C2 governance + Git/main truth + validated Master Archive

**Purpose:** Preserve the exact meaning of the Big Jump Wave, the 5x4 operating frame, and multi-session Jules execution so future C2 sessions do not collapse logical flights, lifecycle cells, execution sessions, or nodes into the wrong abstraction.

---

## 1. Canonical Operating Rule

**BIG JUMP WAVE IS THE NORMAL SAGE EXECUTION WORKFLOW.**

Medium Flow is retired and is not the default, current, or recommended SAGE operating mode.

The canonical execution loop is:

```text
SENSE
-> RECON
-> SUPER SEARCH (when useful)
-> BOUND
-> DECIDE
-> AUTHORIZE
-> BIG JUMP WAVE
-> BUILD
-> OBSERVE
-> VERIFY
-> RECONVERGE
-> COMPOUND
-> NEXT BIG JUMP WAVE
```

Big Jump Wave coordinates multiple independent capability frontiers. It does not mean five flights building one item.

---

## 2. Five-Flight Wave Is the Core Unit

One Big Jump Wave contains **five independent flights**:

```text
                 C2 MISSION CONTROL
                         |
        ┌────────┬────────┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼

     FLIGHT 1  FLIGHT 2  FLIGHT 3  FLIGHT 4  FLIGHT 5

     Own       Own       Own       Own       Own
     Frontier  Frontier  Frontier  Frontier  Frontier

        \        |        |        |        /
                 ▼
          C2 RECONVERGENCE
          Evidence + Receipts
          Promotion Gate
```

A flight is an **independent capability attack vector** and a bounded full-engine mission.

A flight is NOT merely:

- a discovery stage;
- a build stage;
- a testing stage;
- a governance stage;
- a narrow subsystem assignment.

Each flight may advance any causally relevant part of SAGE, provided its frontier is explicitly bounded and distinct from the other flights.

---

## 3. The 5x4 Rule

The canonical Big Jump Wave operating frame is:

**5 independent paths x 4 lifecycle stages = 20 advancement cells.**

The four lifecycle stages are milestone gates, not four separate jobs:

1. **RECON / BOUND**
2. **BUILD / REPAIR**
3. **TEST / OBSERVE / RERUN**
4. **VERIFY / COMPOUND**

The 5x4 frame is a governance and measurement matrix. It does **not** reduce a flight to one stage.

Every flight traverses its lifecycle gates as required by the mission.

The existing canonical 5x4 operating frame remains authoritative for its path/cell tracking and promotion requirements:

`docs/governance/BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md`

---

## 4. 5x4 Is Not the Same Dimension as Flight Count

Do not confuse these quantities:

```text
5 = independent flight vectors in one Big Jump Wave
4 = lifecycle milestone gates for each flight/path
20 = 5 x 4 advancement cells
```

The 20 cells are **not 20 separate permanent features** and are not 20 independent Jules tasks.

They are the lifecycle measurement surface through which the five independent paths advance.

---

## 5. Multi-Session Jules Execution

When multiple Jules sessions are actively running Big Jump Waves, each session can carry a complete five-flight wave.

Therefore, with three independently executing Jules sessions:

```text
3 Jules sessions x 5 flights per wave = 15 distinct flight missions
```

The resulting **15** is a concurrency/execution-capacity calculation, not a replacement for the canonical five-flight wave.

```text
                         C2
                          |
                   BIG JUMP WAVE
                          |
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
    JULES #1           JULES #2           JULES #3
       |                  |                  |
    BIG WAVE            BIG WAVE            BIG WAVE
   F1 F2 F3 F4 F5     F1 F2 F3 F4 F5     F1 F2 F3 F4 F5
       |                  |                  |
       └──────────────────┼──────────────────┘
                          ▼
                    C2 RECONVERGENCE
                          |
                15 DISTINCT FLIGHT
                 CAPABILITY FRONTIERS
```

If all three Jules sessions are actually executing concurrently, the system can have up to **15 independently targeted flight assignments in the same execution window**.

If the execution substrate only permits fewer active tasks, the architecture does not change; the available execution slots are simply the current physical bottleneck. C2 must never falsely report queued work as concurrently executing.

---

## 6. The 15 Are Not 15 Pieces of One Project

The 15 flight missions must be **distinct bounded targets**.

They may originate from any relevant part of SAGE, including but not limited to:

- runtime;
- governance;
- architecture;
- cognition;
- research;
- continuity;
- persistence;
- evidence;
- testing;
- validation;
- product capability;
- discovery;
- learning;
- security;
- capability warehouse.

The determining rule is **frontier independence and bounded scope**, not subsystem ownership.

Do not manufacture artificial differences merely to fill flight slots. If two missions are actually the same frontier, they must be merged or one must be rejected.

---

## 7. Every Flight Gets the Full SAGE Engine

Each flight may use the complete governed execution aperture:

```text
SENSE
-> RECON
-> SUPER SEARCH
-> BOUND
-> DECIDE
-> AUTHORIZE
-> BUILD
-> OBSERVE
-> VERIFY
-> EVIDENCE
-> RECONVERGE
-> COMPOUND
```

A flight is not assigned only one function such as “research,” “coding,” or “testing.”

The mission target determines what work is causally necessary.

Super Search is an intelligence/reconnaissance sensor. Repository/Git truth and validated governance remain authoritative.

---

## 8. Do Not Confuse Flights, Cells, Sessions, or Nodes

These are four different concepts:

| Concept | Meaning |
|---|---|
| **Flight** | One independent bounded capability mission |
| **5x4 cell** | A lifecycle/path measurement position |
| **Jules session** | An execution interface/process capable of carrying a wave or bounded mission |
| **Node** | An optional execution-topology construct; not a mandatory SAGE role |

The architecture must never silently convert one into another.

In particular:

**3 Jules sessions does NOT mean the SAGE architecture has only 3 flights.**

**5x4 does NOT mean 20 tasks.**

**3 nodes are NOT mandatory.**

**Five flights remain the canonical wave unit.**

---

## 9. Multi-Node Is Optional Topology

Multi-node execution is an implementation/scaling mechanism inside Big Jump Wave execution.

It is not a new SAGE lane and does not require exactly three nodes.

Node topology may be introduced when it provides real execution isolation, parallelism, or verification value and is explicitly bounded and authorized.

Do not encode:

```text
Node A = build
Node B = verify
Node C = adversarial
```

as a universal SAGE architecture rule.

The stronger rule is:

> **Each flight is a full-engine independent mission; topology is an implementation detail used to execute and isolate those missions.**

---

## 10. True Concurrency vs Rolling Execution

C2 must distinguish:

### True concurrency

Multiple independent flight processes are actively executing at the same time.

### Rolling/batched execution

Some flights are executing while others are waiting for execution capacity.

A five-flight campaign with only three active execution slots is **not five-way concurrent execution**. It is a five-flight wave with a three-slot execution window.

Likewise, if three Jules sessions each actively execute a five-flight wave, C2 may report up to 15 active flight missions only when the underlying execution is actually active.

Never inflate evidence by counting planned, queued, or merely described flights as running.

---

## 11. C2 Responsibility

C2/Mission Control must:

1. inspect the whole repository and current state;
2. use Super Search for external reconnaissance when useful;
3. identify consequential independent frontiers;
4. prevent duplicate or overlapping missions;
5. bound each flight;
6. preserve architecture and governance;
7. dispatch the wave through available execution capacity;
8. track actual execution state separately from planned state;
9. independently verify results;
10. reconverge evidence before capability promotion.

C2 must never claim concurrency that the execution substrate did not actually perform.

---

## 12. Jules Responsibility

Jules is the engineering/execution station inside the shared C2 Big Jump Wave protocol.

Jules receives bounded missions and returns:

```text
Flight:
Mission:
Target Frontier:
Changes:
Tests:
Evidence:
Capability Gained:
Blockers:
Next Move:
```

C2 remains responsible for cross-flight alignment, architecture protection, verification, and reconvergence.

There is no separate Jules governance universe.

---

## 13. Mission Director Interface

The Mission Director may launch Big Jump Wave missions through multiple available Jules sessions.

If three sessions are available and each is independently running a five-flight wave, the theoretical execution surface is:

**3 x 5 = 15 distinct flight missions.**

This is legitimate orchestration of available execution capacity. It is not a bypass of account limits, access controls, quotas, or product restrictions.

C2 may prepare and coordinate missions ahead of execution, but must not claim that a task has launched until the execution substrate confirms it.

---

## 14. Canonical Language for Future C2 Sessions

When this doctrine is active, use these terms precisely:

> **Big Jump Wave** = normal SAGE execution workflow.
>
> **Five flights** = canonical independent mission unit per wave.
>
> **5x4** = five paths x four lifecycle milestone gates = 20 advancement cells.
>
> **15** = three concurrently executing Jules wave sessions x five independent flights, when all 15 are actually active.
>
> **Full-engine flight** = each flight can traverse the complete governed SAGE execution loop.
>
> **Multi-node** = optional execution topology, not a mandatory three-node architecture.
>
> **C2 reconvergence** = independent verification and evidence reconciliation across the active wave.

---

## 15. Non-Negotiable Anti-Drift Rules

Future C2/Jules planning must not:

- reintroduce Medium Flow as the normal SAGE workflow;
- reduce five flights to three because only three execution sessions are available;
- call the 20 5x4 cells “20 tasks”;
- assign each flight permanently to one lifecycle stage;
- claim 15 active flights when some are only planned or queued;
- require exactly three nodes;
- treat Super Search as canonical authority;
- allow duplicate targets across flights without explicit justification;
- promote capability without tests, verification, evidence, and bounded provenance.

When ambiguity exists, **repository truth + this doctrine + validated Master Archive outrank conversational assumptions.**

---

## 16. Relationship to Existing Canonical Doctrine

This document is a precision clarification of the existing Big Jump Wave architecture. It does not replace the existing operating frame.

Primary references:

- `docs/governance/BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md`
- `docs/governance/C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md`
- `docs/governance/C2_FLIGHT_CONTROL_OPERATING_MODEL.md`
- `docs/governance/SAGE_C2_CONTINUOUS_BIG_JUMP_EXECUTION_MODEL.md`

The existing five-flight and 5x4 governance remains intact. This doctrine exists so C2 can correctly interpret the relationship between **waves, flights, lifecycle cells, Jules sessions, and optional execution nodes** across future conversations.

---

## Final Lock

```text
BIG JUMP WAVE = NORMAL SAGE FLOW

5 FLIGHTS = 1 CANONICAL WAVE

5 x 4 = 20 LIFECYCLE/PATH ADVANCEMENT CELLS

3 JULES WAVE SESSIONS x 5 FLIGHTS
= UP TO 15 DISTINCT ACTIVE FLIGHT MISSIONS

ONLY COUNT WHAT IS ACTUALLY EXECUTING

EACH FLIGHT = FULL SAGE ENGINE

TARGETS MUST BE DISTINCT + BOUNDED

MULTI-NODE = OPTIONAL TOPOLOGY

C2 = RECON + BOUND + COORDINATE + VERIFY + RECONVERGE

SUPER SEARCH = SENSOR
GIT / REPO TRUTH = AUTHORITY
MASTER ARCHIVE = CANONICAL VALIDATED STATE
```
