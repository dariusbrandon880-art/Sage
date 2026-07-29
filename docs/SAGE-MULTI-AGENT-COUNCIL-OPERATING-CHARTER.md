# SAGE Multi-Agent Council Operating Charter

**Document Identifier:** SAGE-COUNCIL-CHARTER-2026-07-29
**Classification:** Governed Research & Architecture Record
**Status:** PROPOSED — Strategic Governance Design Phase
**Author:** Jules (SAGE Engineering Node)
**Date:** July 2026

---

## Executive Summary

This document establishes the **SAGE Multi-Agent Council Operating Charter**, specifying the constitutional rules, roles, decision boundaries, and communication standards that govern the council of specialized AI agents.

In strict compliance with structural and architectural laws:
- **No autonomous agents are instantiated or executed.**
- **No new production agent capabilities are implemented.**
- **All production runtime enclaves (`sage/runtime/`, `sage/core/`, `sage/acr/`) remain 100% untouched and locked.**

By defining strict membership requirements, decision ownership models, and failure recovery protocols, SAGE guarantees that multi-agent interactions remain structurally bounded, traceable, and entirely subordinate to human gatekeeping.

---

## Section 1 — Council Purpose

The SAGE Multi-Agent Council exists to provide structured engineering execution, peer review, and strategic analysis assistance to human supervisors.

### 1.1 The Necessity of Formal Governance
- **Preventing Emergent Chaos:** Unregulated autonomous agents risk generating circular execution loops, authority confusion, or unaligned codebase modifications.
- **Sovereignty Boundary:** Agents act as execution assistance units; they lack constitutional authority to define system goals, alter permissions, or promote capabilities autonomously.
- **Assistance vs. Authorization:** The boundary between execution assistance and decision-making authorization is absolute. Agents formulate recommendations and prepare evidence; humans decide.

---

## Section 2 — Council Structure

The SAGE Multi-Agent Council is organized as a multi-tier pipeline to enforce separation of concerns and absolute traceability:

```
        ┌────────────────────────────────────────────────────────┐
        │               HUMAN GOVERNANCE AUTHORITY               │
        │  - Ultimate sovereign decision maker.                  │
        │  - Executes state promotions and authorizes plans.     │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ [Directs]
        ┌────────────────────────────────────────────────────────┐
        │               STRATEGIC COORDINATION NODES             │
        │  - Formulates design blueprints and roadmap targets.   │
        │  - Node: ChatGPT (Architecture Coordination Node).     │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ [Instructs]
        ┌────────────────────────────────────────────────────────┐
        │                 EXECUTION SUPPORT NODES                │
        │  - Writes file modifications, runs pytest, sets plans. │
        │  - Node: Jules (Execution Node).                       │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ [Telemetry]
        ┌────────────────────────────────────────────────────────┐
        │                INDEPENDENT REVIEW NODES                │
        │  - Peforms static audits and adversarial reviews.     │
        │  - Node: Claude (Peer Review / Boundary Audit Node).   │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ [Validates]
        ┌────────────────────────────────────────────────────────┐
        │               EVIDENCE AND ARCHIVE LAYER               │
        │  - Serialized Evidence Packages indexed in INDEX.md.   │
        └────────────────────────────────────────────────────────┘
```

---

## Section 3 — Agent Membership Requirements

To prevent undocumented execution, every AI agent participating in SAGE council workflows must possess a registered and active Agent Passport.

### 3.1 Mandatory Passport Fields
Each passport must explicitly define the following seven fields:
1. **Agent Identity:** Unique structured name (e.g. `Jules-Node-v2.0`).
2. **Mission Purpose:** Specific functional directory or operational task assigned.
3. **Allowed Actions:** White-listed tools and execution permissions.
4. **Restricted Actions:** Actions strictly barred (e.g. altering core runtime).
5. **Evidence Responsibility:** Mandatory schema definitions and telemetry logs to be emitted.
6. **Review Boundary:** Designated independent peer-reviewer or supervisor.
7. **Archive Relationship:** Target index entry inside the Master Archive.

### 3.2 The Fundamental Membership Rule
$$\textbf{No Passport = No Participation}$$

Any file change, plan modification, or command executed by an agent that lacks an approved, active passport is treated as a security violation and is subject to immediate quarantine and rollback.

---

## Section 4 — Council Communication Rules

Council communication must remain strictly structured, deterministic, and traceable.

- **Communication Format:** All inter-agent handoffs must be serialized inside the standardized **Agent Handoff Envelope**, preventing out-of-band context sharing or hidden state transfer.
- **Handoff Requirements:** Every handoff must be signed by the emitting node, referencing the active `Task ID` and associated `DecisionEntry`.
- **Context Preservation:** In the event of cold restarts or context resets, agents must reconstruct their context exclusively by traversing the relational lineage graph backward to the nearest validated checkpoint state.
- **Conflict Escalation:** If two specialized nodes (e.g. Jules and Claude) reach an impasse, the task is immediately frozen and escalated to the human supervisor for arbitration.

---

## Section 5 — Decision Ownership Model

SAGE establishes a non-bypassable partition of authority between human supervisor nodes and assisting agent nodes:

### 5.1 Human-Owned Decisions (Absolute Authority)
- **Final Approvals:** Authorizing any change to the repository structure or codebase.
- **Capability Promotion:** Transitioning capability states under the Index Layer Provenance Schema (`PROPOSED` $\rightarrow$ `VALIDATED`).
- **Lifecycle Decisions:** Decommissioning, freezing, or rehydrating development lanes.
- **Architectural Changes:** Editing or appending constitutional files.

### 5.2 Agent-Owned Actions (Execution Assistance)
- **Analysis:** Evaluating system parameters, code syntax, and dependency maps.
- **Execution Support:** Drafting text documents, writing test suites, and creating sandbox setups.
- **Evidence Preparation:** Serializing 11-field Evidence Packages.
- **Recommendations:** Suggesting next roadmap milestones or recovery strategies.

---

## Section 6 — Council Failure Handling

Operating anomalies must be resolved according to deterministic protocols to prevent systemic drift:

- **Conflicting Recommendations:** Freeze the task envelope; halt pipeline execution, and escalate to **Human Dispute Arbitration**.
- **Duplicated Analysis:** Reject the subsequent work product; force synchronization with the **Session 1 Checkpoint Anchor**.
- **Missing Context:** Terminate active agent execution; roll back to the nearest validated state, and log the context loss.
- **Invalid Evidence:** Discard the payload; quarantine the associated work product, and notify the human supervisor.
- **Unavailable Agents:** Pause dependent execution tasks; trigger retry handshakes, and wait for human retry instructions.
- **Interrupted Handoffs:** Lock the transaction state; isolate modified files, and log the interruption metrics.

---

## Section 7 — Future Agent Expansion Rules

As SAGE integrates new specialized agents (such as Google Gemini Research Analysis nodes) into the council, they must pass six standard requirements:

1. **Documented Mission:** A clear statement of scope matching an unaddressed capability node.
2. **Capability Passport:** A complete, registered passport under `PROPOSED` inside `INDEX.md`.
3. **Authority Boundary:** Clear definition of allowed and restricted actions.
4. **Evidence Pathway:** Pre-defined serialized evidence package schema satisfying the 11-field model.
5. **Reviewer Assignment:** Explicitly assigned independent reviewer agent (e.g. Claude).
6. **Human Approval:** Coordinated sign-off by the human supervisor authorizing the node.

---

## Section 8 — Conclusion

The SAGE Multi-Agent Council Operating Charter guarantees that autonomous AI leverage remains strictly safe, verifiable, and aligned with human intent. By maintaining transparent ownership boundaries, deterministic failure recovery rules, and absolute human gatekeeping, SAGE establishes the premier operational model for secure, multi-agent software engineering.
