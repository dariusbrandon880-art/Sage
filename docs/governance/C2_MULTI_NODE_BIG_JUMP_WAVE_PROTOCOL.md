# SAGE C2 Multi-Node Big Jump Wave Execution Protocol

**Document ID:** `C2_MULTI_NODE_BIG_JUMP_WAVE_PROTOCOL`
**Version:** `1.1`
**Authority:** SAGE C2 Persistent Operating Contract + Master Archive + `docs/governance/BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md` + `docs/governance/C2_FIVE_FLIGHT_CAMPAIGN_ARCHITECTURE.md` + `docs/governance/SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md`

---

## 1. Executive Purpose

This protocol establishes the canonical execution rules for operating **Multi-Node Big Jump Waves** across concurrent C2/Jules execution nodes.

Five flights are the mandatory SAGE execution workflow unit. Multi-node topology is an optional execution configuration (supporting 1..N nodes).

When multiple C2 nodes or Jules execution sessions operate simultaneously on a repository, C2 MUST NOT alter, hallucinate, or collapse the workflow flow. C2 MUST NOT confuse lifecycle stages for flights, nor substitute single-issue task assignments for canonical 5-flight Big Jump Waves.

---

## 2. Multi-Node Architecture Model (Optional Topology)

```text
                               MISSION DIRECTOR
                                      │
                                      ▼
                                 SAGI BRAIN
                            opportunity discovery
                                      │
                                      ▼
                                 C2 / CHATGPT
                       command & multi-node coordination
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
      JULES NODE A               JULES NODE B               JULES NODE C
   Primary Repair Wave        Verification Wave          Adversarial Wave
   5 Flights + 2 Reserve     5 Flights + 2 Reserve      5 Flights + 2 Reserve
   (F1..F5 + R1, R2)         (F1..F5 + R1, R2)          (F1..F5 + R1, R2)
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      ▼
                          C2 MULTI-NODE RECONVERGENCE
                          evidence + receipts + head
                                      │
                                      ▼
                               PROMOTION GATE
                                      │
                                      ▼
                             VERIFIED CAPABILITY
```

---

## 3. Mandatory Multi-Node Operating Laws

### Law 1: Node Autonomy with Bounded Scope & Optional Topology
Multi-node topology is optional. Each active Jules Node (Node A, Node B, Node C, or a single node) operates as a complete, independent execution unit running a full **5-Flight Big Jump Wave** with 2 reserve capacity slots (up to 7 flight units total).

### Law 2: Flight Definition Preservation
A Flight is an **independent capability attack vector** operating on its own frontier with its own recon, implementation, tests, and evidence.
A Flight is **NEVER**:
- A staged pipeline step (e.g. Flight 1 = discovery, Flight 2 = testing).
- A single-purpose micro-task assigned to an entire Jules session.
- A pre-labeled backlog item.

### Law 3: Zero Flow Alteration
C2 or any execution adapter MUST NOT alter the C2 Operating Loop (`SENSE → RECON → SUPER SEARCH → BOUND → DECIDE → AUTHORIZE → BUILD → OBSERVE → VERIFY → COMPOUND`).
Any attempt by a language model or adapter to invent non-repo layouts or omit verification steps fails closed (`REJECTED_FLOW_DRIFT`).

### Law 4: Namespace Collision Locks
No two concurrent nodes or flights may execute write operations against the same target file or module namespace simultaneously.
The C2 Multi-Node Wave Engine enforces strict path collision checking before authorizing node dispatch.

### Law 5: Reserve Capacity Protocol
Each node maintains 2 reserve flight slots (R1, R2). Reserve slots are allocated dynamically when:
- Unforeseen defects or regressions are discovered during Flight 1–5 execution.
- Adversarial falsification or boundary validation requires immediate targeted repair.

### Law 6: Cryptographic SHA & Receipt Reconvergence
All flight outputs, test results, and evidence claims across Node A, Node B, and Node C must be bound to the exact git commit SHA at execution time. Reconvergence produces an aggregated SHA-256 `C2MultiNodeWaveReceipt` containing signatures from all node flights.

---

## 4. Work Order Schema

Every Multi-Node Big Jump Wave dispatch must declare:

```json
{
  "wave_id": "WAVE_MULTI_NODE_YYYYMMDD_001",
  "commit_sha": "<40-char-git-sha>",
  "nodes": {
    "NODE_A": {
      "role": "PRIMARY_REPAIR",
      "active_flights": ["F1", "F2", "F3", "F4", "F5"],
      "reserve_slots": ["R1", "R2"]
    }
  }
}
```

---

## 5. Verification Standard

A Multi-Node Big Jump Wave is verified ONLY when:
1. Every active flight in each node reports status `PASS` with zero test regressions.
2. No namespace collisions occurred across nodes.
3. Cryptographic evidence receipt `C2MultiNodeWaveReceipt` is generated, signed, and persisted in `evidence_capture/`.
4. Platform test suite passes 100% against the active HEAD commit SHA.
