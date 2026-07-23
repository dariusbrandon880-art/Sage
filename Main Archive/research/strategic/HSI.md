# Human-SAGE Interaction (HSI) Spec — Strategic Research Core

## 1. Executive Research Summary
SAGE v1.0.0 is an exceptionally robust autonomous continuity platform. However, for SAGE to evolve from a stateful executor into a true long-term cognitive partner, the human-AI interaction layer must be optimized. Historically, AI systems have alternated between passive execution (waiting for prompts) and unchecked autonomy.

This research paper outlines **Human-SAGE Interaction (HSI)**: a structured, bidirectional, mixed-initiative framework enabling SAGE to actively collaborate with, learn from, challenge, and amplify its human operator. By embedding cognitive pacing, adaptive explanations, error self-correction loops, and structured context boundaries directly into SAGE's existing Autonomous Continuity Runtime (ACR), HSI transforms the human-SAGE relationship from transaction-oriented querying into continuous intelligence amplification.

---

## 2. Recommended Architecture Improvements
Rather than introducing a separate subsystem, HSI integrates directly into SAGE's existing v2 modular architecture:

### A. Kernel & ACR Continuity Bridge (Mixed-Initiative Pacing)
*   **Recommendation:** Implement a **Bidirectional Turn Evaluator (BTE)** inside the Continuity Bridge.
*   **Functionality:** Instead of automatically executing or passively answering, the BTE analyzes the user's input complexity and SAGE's internal certainty. It selects an *interaction mode*:
    *   `EXECUTE`: Direct task fulfillment (low uncertainty, high instruction clarity).
    *   `ELABORATE`: Offer alternative architectures/tradeoffs before committing (high design impact).
    *   `CHALLENGE`: Intervene if the proposed user action violates existing Master Archive constraints or ADRs (critical architecture safety).
    *   `CLARIFY`: Ask targeted questions (high ambiguity, missing critical variables).

### B. Memory & Archive (Optimized Context & Retrieval)
*   **Recommendation:** Implement an **Active Context Filter (ACF)** inside the Memory and Archive submodules.
*   **Functionality:** To prevent memory bloat and context-window degradation, raw chat transcripts are discarded. Instead, SAGE extracts:
    1.  *Semantic Core:* Compact state transitions, architectural decisions, and finalized technical goals.
    2.  *Cognitive Preference Vector (CPV):* Tracks user domain expertise, preferred explanation formats (e.g., highly technical vs. architectural), and historical correction trends.
*   **Retrieval Unification:** Unified search maps active `SessionState` context over both local `Memory` and immutably indexed `Archive` relationships.

### C. Runtime (Adaptive Explanation Scaling)
*   **Recommendation:** Integrate an **Explanation Adapter (EA)** into SAGE's Runtime `ExecutionContext`.
*   **Functionality:** The EA maps the complexity of technical descriptions based on the operator's CPV:
    *   *Level 1 (Exploratory):* Focuses on conceptual mental models, systemic design blocks, and high-level flows.
    *   *Level 2 (Co-Pilot):* Details module-level interfaces, code structures, and concrete API definitions.
    *   *Level 3 (Autonomous Unification):* Provides direct merge diffs, test specifications, and performance profiles with zero conceptual hand-holding.

### D. Tools & Validation (Joint System Building)
*   **Recommendation:** Create **Cooperative Verification Protocols (CVP)**.
*   **Functionality:** SAGE exposes `/tools/validate` and `/tools/co-verify` endpoints. When the operator edits a file or defines a new objective, SAGE and the human co-verify the code. SAGE runs local checks (Ruff, Black, Pytest) and translates failures into localized recommendations, allowing the human and SAGE to jointly debug the execution.

### E. Evolution Loop (Error Detection and Improvement Loop)
*   **Recommendation:** Establish a dedicated **System Feedback and Correction Loop (SFCL)**.
*   **Functionality:** When a misunderstanding or logical error occurs (detected via user corrections, failed test suites, or reverted commits), SAGE initiates a 5-step self-correction pipeline:
    1.  **Error:** Detect divergence between human intent and SAGE action.
    2.  **Analysis:** Audit the `SessionState` and `ContinuityContext` history to trace the exact turn where the misconception was ingested.
    3.  **Correction:** Revert or apply targeted code repairs locally.
    4.  **Prevention:** Generate an internal "Preventative Constraint" stored in SAGE's memory cache.
    5.  **Validation:** Run the complete test suite to ensure the corrected behavior is stable.

---

## 3. Interaction Flow Mapping
The diagram below shows how the Human-SAGE Interaction (HSI) flows through the unified platform:
```
[Human Operator]
       │
       ▼ (Command, Code, or Design Spec)
[ACR Continuity Bridge / BTE] ──► (Decides Mode: Execute, Challenge, Clarify)
       │
       ▼
[Runtime Execution & EA] ───────► (Scales Explanations based on Operator Profile)
       │
       ▼
[Validation Suite / CVPs] ──────► (Cooperative Bug-Fixing and Verification)
       │
       ▼
[Memory/Archive Stores] ────────► (Updates SessionState, Decisions, and preference vectors)
```

---

## 4. Possible Implementation Roadmap

### Phase 1: Prototype Cognitive Pacing (Short-Term)
*   **Objective:** Implement the `BTE` (Bidirectional Turn Evaluator) mode classification within `SageRuntime.ingest_session_payload`.
*   **Deliverable:** An internal classifier assigning incoming instructions an execution mode and outputting targeted clarification questions if uncertainty bounds are exceeded.

### Phase 2: Memory Prefectures & CPV Integration (Medium-Term)
*   **Objective:** Introduce user preference tracking (`CognitivePreferenceVector`) and session memory compaction into `session_state.py` and `context_tracker.py`.
*   **Deliverable:** Automated extraction of high-level state decisions and preferred abstraction depths, excluding raw conversation transcripts from memory storage.

### Phase 3: Cooperative Verification UI/CLI (Long-Term)
*   **Objective:** Fully expose the `/tools/co-verify` endpoint and CLI utility.
*   **Deliverable:** A collaborative development workspace interface where human developer adjustments and SAGE test verification run simultaneously.

---

## 5. Risks and Validation Requirements

### A. Core Architectural Risks
1.  **Explanation Drift:** The adaptive explanation module might oversimplify highly technical operations, causing SAGE to omit critical implementation details.
2.  **Challenge Fatigue:** If SAGE challenges human assumptions too frequently, it leads to user frustration and reduced trust.
3.  **Context Over-Compaction:** Aggressive memory-transparency algorithms might prune details that, while seemingly redundant, contain critical logical dependencies for subsequent sessions.

### B. Validation & Safety Checks
*   **Quantitative Metrics:**
    *   *Correction Ratio:* Calculate the percentage of user prompts that contain corrections of previous SAGE actions (target: < 5%).
    *   *Latency Overheads:* Ensure cognitive evaluations add less than 100ms of overhead to the ingestion path.
*   **Qualitative Verification:**
    *   *Pacing Audits:* Verify that SAGE only challenges instructions when a direct conflict with an immutably stored ADR or test specification occurs.
    *   *Consistency Tests:* Run automated integration scripts to confirm that updating explanation levels never modifies the actual code payload produced by SAGE.
