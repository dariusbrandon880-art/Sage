# SAGE Agent Coordination Protocol Specification

**Record ID:** SAGE-COORDINATION-PROTOCOL-2026-07-30
**Classification:** Research / Proposed
**Status:** PROPOSED — Strategic Protocol Design Phase
**Target Schema:** SAGE Provenance Schema v0.1
**Execution Context:** SAGE Agent Coordination Protocol Specification Lane

---

## Section 1 — Coordination Protocol Purpose

As SAGE matures into a model-independent AI Reliability Infrastructure and Agent Governance Control Layer, the coordination of multiple autonomous AI agents requires a formal, deterministic communication protocol.

### 1.1 The Necessity of Formal Coordination Protocols
Without formal protocols, multi-agent systems suffer from uncoordinated execution, context drift, duplicate efforts, trace gaps, and circular dependencies. A formal protocol enforces:
- **Causal Lineage Tracking:** Ensuring that every agent contribution is linked back to an explicit human directive.
- **State Transition Monotonicity:** Preventing out-of-order execution states in distributed networks.
- **Perfect Auditability:** Generating immutable, verifiable traces for security reviews.

### 1.2 Relationship Between Agents, Evidence, and Governance
SAGE coordinates agents purely in an assistive capacity. Agents do not operate autonomously outside of sandboxed boundaries.

The SAGE governance pipeline enforces a strict progression:
$$\text{Research} \longrightarrow \text{Validation} \longrightarrow \text{Evidence} \longrightarrow \text{Human Review} \longrightarrow \text{Master Archive}$$

- **Agents** execute tasks and compile raw trace data.
- **Evidence Frameworks** serialize that data into standard-compliant exchange contracts (such as CMAPS v1.0).
- **Governance Layers** enforce absolute isolation boundaries, preventing circular imports or unauthorized filesystem writes.

### 1.3 Absolute Separation: Assistance vs. Authority
SAGE establishes an immutable boundary regarding authority:

$$\textbf{Agents Assist Execution. Agents Do Not Become Governance Authorities.}$$

No software code, model connector, or multi-agent workflow has the power to:
- Promote its own lifecycle state.
- Write to or approve promotions inside protected production enclaves (`sage/runtime/`, `sage/core/`, `sage/acr/`).
- Bypass the human review gate.

---

## Section 2 — Agent Communication Envelope

All inter-agent communications and state handoffs must be encapsulated inside a structured, validated metadata envelope. The **Agent Communication Envelope** requires exactly twelve fields:

1. **Task Identifier:** A unique, chronologically ordered task tracking ID (e.g., `TASK-ACT-001`).
2. **Agent Identifier:** The executing model or agent node identifier (e.g., `AGENT-GPT4-01`, `AGENT-JULES-02`).
3. **Agent Passport Reference:** The active passport record proving registration and authorization limits of the agent.
4. **Mission Objective:** A high-fidelity statement of the causal goal the agent is authorized to achieve.
5. **Input Context:** References to the specific signed parent state and cryptographic nonces received by the agent.
6. **Allowed Scope:** A strict set of authorized directories, APIs, or mock providers the agent can query.
7. **Restricted Scope:** Explicitly blocked directories (such as core production enclaves) and actions.
8. **Expected Output:** The mathematically or logically predicted output and file types.
9. **Evidence Requirements:** The specific schema format (such as CMAPS v1.0) and files the agent must output.
10. **Validation Requirements:** The designated testing, observation, or simulation checks (such as SAGE-SDR validation) the output must pass.
11. **Reviewer Assignment:** The assigned human supervisor or auditor responsible for evaluating the contribution.
12. **Archive Destination:** The designated final repository destination inside the Master Archive (such as `docs/`).

---

## Section 3 — Agent Workflow Sequence

To prevent uncoordinated execution, all agent actions must progress through a deterministic, nine-stage sequential pipeline:

```
        [ Human Direction ]  ──► Direct causal instructions from a human supervisor.
                │
                ▼
      [ Task Classification ] ──► Map directive to a specific passport capability.
                │
                ▼
       [ Agent Assignment ]  ──► Delegate execution to the authorized model connector.
                │
                ▼
    [ Execution Within Boundary ] ─► Sandbox isolation (e.g., SAGE-SDR sandbox) active.
                │
                ▼
     [ Artifact Generation ] ──► Code drafts, specs, or validation reports produced.
                │
                ▼
       [ Evidence Capture ]  ──► Passive intercept of state-differentials and traces.
                │
                ▼
      [ Independent Review ] ──► Adversarial model audits (e.g., Claude checking Jules).
                │
                ▼
        [ Human Decision ]   ──► Manual evaluation of completeness and safety.
                │
                ▼
    [ Master Archive Update ] ─► Synchronization of indices (`INDEX.md`) as VALIDATED.
```

No stage in this sequence can be bypassed. If an agent encounters a boundary violation or failure during execution, the workflow fails-closed and triggers isolated recovery.

---

## Section 4 — Cross-Agent Handoff Rules

Multi-agent coordination requires strict context preservation and linear traceability across different model provider interfaces. SAGE standardizes the handoff sequence below:

### 4.1 The Intake and Auditing Sequence
1. **Intake and Formulation (ChatGPT $\rightarrow$ Jules):**
   - OpenAI's ChatGPT acts as the intake node, translating high-level human directives into structured technical drafts.
   - The resulting payload is handed off to Gemini's Jules, which formalizes the specific validation strategies and drafts code prototypes.
2. **Formulation and Auditing (Jules $\rightarrow$ Claude):**
   - Jules hands off the finalized drafts and validation schemas to Anthropic's Claude.
   - Claude acts as the independent, adversarial validation node, auditing the draft for schema compliance, duplicate task patterns, or code injection hazards.
3. **Auditing and Verification (Claude $\rightarrow$ Human):**
   - Claude compiles all raw traces, validation logs, and state-differentials into a read-only SDR Evidence Package, signing it with its private connector key.
   - The package is presented to the human supervisor for final validation and Master Archive promotion sign-off.

### 4.2 Handoff Invariants
- **Context Preservation Requirements:** Every cross-agent handoff must include the complete historic trace of preceding agent decisions. Striping or truncating historical context is strictly blocked.
- **Decision Traceability Requirements:** Every file differential or conceptual decision must reference the specific model connector that executed it, preventing multi-agent identity drift.
- **Conflict Handling Rules:** If two agents generate conflicting outputs, execution is halted. The conflict must be packaged as an *Anomaly Event* and escalated to the human supervisor. No autonomous conflict resolution or consensus-based promotion is permitted.

---

## Section 5 — Evidence and Accountability Model

To ensure absolute system accountability, SAGE enforces strict verification invariants on all developer contributions:

### 5.1 Contribution Passport Requirements
Every single agent contribution requires exactly five verified elements:
- **Identity:** Cryptographic signature proving the executing agent node.
- **Purpose:** Direct correlation with an authorized mission objective.
- **Traceable Action:** Linear chronological log of all file changes and decisions.
- **Evidence Location:** Verifiable path of the serialized SDR Evidence Package.
- **Review Status:** Signed review record from the assigned human supervisor.

### 5.2 The Three Immutable Accountability Invariants

$$\begin{aligned}
\textbf{No Trace} &\implies \textbf{No Contribution} \\
\textbf{No Evidence} &\implies \textbf{No Promotion} \\
\textbf{No Human Review} &\implies \textbf{No Lifecycle Movement}
\end{aligned}$$

- **No Trace = No Contribution:** Any code or specification introduced without an associated chronological execution log is immediately isolated and rejected.
- **No Evidence = No Promotion:** Transitioning a capability's lifecycle state requires an empirical evidence package. Theoretical assumptions do not qualify.
- **No Human Review = No Lifecycle Movement:** Software observes, collects, and checks; but only human reviews authorize state progression.

---

## Section 6 — Coordination Failure Recovery

When distributed agent systems fail, they must fail-closed. SAGE-SDR coordinates graceful recovery for six specific failure taxonomies:

1. **Lost Context:** If an agent encounters context decay or missing parent nonces, it halts execution, rolls back to the last signed checkpoint, and requests context rehydration.
2. **Conflicting Outputs:** If concurrent agents draft contradictory patches or documents, the system locks the affected directories and escalates the conflict as an anomaly event.
3. **Duplicate Tasks:** If two connectors register identical mission objectives, the second task is automatically pruned by the `SessionStateTaskLinker` to prevent race conditions.
4. **Invalid Evidence:** If the generated CMAPS payload fails schema validation, the simulation is flagged as *Corrupted Trace* and the state is immediately torn down.
5. **Agent Disagreement:** If an auditor agent (e.g., Claude) detects validation errors in an executor's (e.g., Jules) output, the draft is rejected and sent back to the draft phase.
6. **Handoff Interruption:** If a network partition interrupts a cross-agent handoff, the receiving node rejects the incomplete payload and rolls back to the previous validated step.

---

## Section 7 — Future Expansion Boundaries

Onboarding future agent connectors (such as advanced model releases or specialized task agents) requires satisfying five strict, non-bypassable prerequisites:

1. **Agent Passport:** Drafting and registering a new Agent Passport detailing its specific operational limits and identity keys.
2. **Mission Definition:** Aligning its capabilities purely to assistive research roles, with zero production core write access.
3. **Authority Limits:** Hardcoding strict AST and SPEK directory block lists to prevent accidental write attempts to core paths.
4. **Evidence Pathway:** Enforcing standard-compliant CMAPS v1.0 and SDR Evidence package serialization formats on all output traces.
5. **Human Approval Boundary:** Obtaining written supervisor sign-off and registering the passport in the Master Archive as `VALIDATED` before executing any sandboxed simulation.

---

## Section 8 — Conclusion

The SAGE Agent Coordination Protocol provides a deterministic, secure, and robust framework for coordinating diverse, model-independent agent teams. By strictly separating assistance from authority, enforcing standardized communication envelopes, and upholding the Three Immutable Accountability Invariants, SAGE guarantees absolute baseline stability and represents the gold standard for secure multi-agent collaboration.
