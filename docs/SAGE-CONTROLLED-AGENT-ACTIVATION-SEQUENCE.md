# SAGE Controlled Agent Activation Sequence Plan

**Document Identifier:** SAGE-ACTIVATION-SEQ-2026-07-29
**Classification:** Controlled Activation Planning
**Status:** PROPOSED — Strategic Governance Design Phase
**Author:** Jules (SAGE Engineering Node)
**Date:** July 2026

---

## Executive Summary

This document establishes the **SAGE Controlled Agent Activation Sequence Plan**, defining the exact operational phases required to bring experimental AI agent nodes into a governed, non-production sandbox environment.

Consistent with our strict architectural laws:
- **No production agents are activated or introduced.**
- **No autonomous workflows, self-modification, or unrestricted authority is enabled.**
- **All core production runtimes (`sage/runtime/`, `sage/core/`, `sage/acr/`) remain 100% untouched and locked.**

This plan details Phase 0 through Phase 5, establishing a safe, structured, and human-in-the-loop validation path for future experimental SAGE agent executions.

---

## Section 1 — Phase 0 — Activation Preconditions

Before any sandbox simulation is authorized to start, the validation framework must programmatically verify the existence of six baseline preconditions:

1. **Governance Approval:** The target simulation scenario must have a corresponding, approved RFC record registered in the Master Archive.
2. **Experiment Authorization:** Explicit manual sign-off on the target experiment configuration by the human supervisor steering node.
3. **Identity Assignment:** The execution engine must register a valid `AgentPassport` defining the participant node's identity and boundaries.
4. **Capability References:** All mock tool dependencies must link back to registered, valid `CapabilityPassport` nodes.
5. **Evidence Infrastructure:** The local file output directory must be fully functional and writable for exporting `CapabilityEvidenceReceipt` files.
6. **Human Reviewers:** A human supervisor node must be registered and designated to receive the final review gate payload.

---

## Section 2 — Phase 1 — Agent Registration

Every participant agent node entering the validation environment must possess a complete, verified registry record:

- **Agent Identity Creation:** Generation of a unique identity hash (e.g., `sim-agent-01`) signed by the simulation validator.
- **Role Assignment:** Allocation of a specific, strictly defined operational role (e.g., `sim-coordinator`, `sim-validator`).
- **Allowed Capabilities:** Explicit list of registered capability passport IDs the agent node is authorized to use during the execution.
- **Restricted Actions:** Rigid definitions of forbidden pathways, network access boundaries, and system file write locks.
- **Audit Requirements:** Standardized tracking of all CLI actions, console dumps, and API requests executed by the agent node.

---

## Section 3 — Phase 2 — Sandbox Activation

The sandbox validation environment enforces a highly restricted runtime jail:

- **Sandbox Environment:** Isolation of all execution within the ephemeral `sage/experimental/act/` directory structures.
- **Controlled Inputs:** Restricting execution exclusively to pre-parsed, static mock payloads.
- **Approved Tools:** Restricting agent action execution to a predefined set of mock utility functions.
- **Execution Limits:** Strict constraints on time-to-live, CPU usage, and total operation loops to prevent resource starvation.
- **Monitoring Requirements:** Continuous, non-intrusive tracing of all sandbox side-effects by the test runner.

---

## Section 4 — Phase 3 — Evidence Generation

Every step of sandbox execution must generate verifiable evidence for subsequent evaluation:

- **Execution Records:** Logging of every internal state change and API call to structured JSON output files.
- **Evidence Receipts:** Exporting a signed `CapabilityEvidenceReceipt` compiling the experiment outcome.
- **Validation Artifacts:** Preserving any generated code snippets or configuration files in local validation output folders.
- **Failure Capture:** Logging and classification of any exceptions, schema violations, or execution halts.
- **Review Package:** Bundling all execution logs and receipts into a single package for presentation to the human review gate.

---

## Section 5 — Phase 4 — Human Review

The human supervisor node maintains absolute, final gatekeeping authority over the capability state:

- **Approval Checkpoints:** Reviewing execution logs, verification receipts, and passport parameters.
- **Rejection Criteria:** The immediate rejection of the validation trial if any boundary violation, schema corruption, or trace mismatch is detected.
- **Archive Decision Process:** The manual generation of a signed review record with `review_decision: APPROVED` or `REJECTED`, which is then committed to the decentralized index layer.

---

## Section 6 — Phase 5 — Expansion Criteria

Progressing beyond initial dry-run simulations requires the accumulation of structured validation evidence:

- **Incremental Experiments:** Transitioning to slightly larger simulation scenarios only after 50 consecutive green loop runs.
- **Broader Sandbox Access:** Granting restricted, local read-only permissions to additional sandbox folders.
- **Future Engineering Consideration:** Formalizing a proposal to the SAGE steering committee for production-track integration.

---

## Section 7 — Explicit Exclusions and Frozen Boundaries

To prevent any capability drift or production instability, the following boundaries are strictly frozen and write-locked:

- **No production deployment:** No experimental agent code may be deployed or referenced within `sage/runtime/`, `sage/core/`, or `sage/acr/`.
- **No autonomous operation:** No agent node may run as a background daemon or trigger self-initiated loops.
- **No self-evolution:** No agent may write, edit, or refactor any production codebase file.
- **No capability promotion without review:** Transitions of capability lifecycle states require manual human review.

---

## Section 8 — Conclusion

This Controlled Agent Activation Sequence Plan provides the definitive, safe roadmap for bringing experimental agents under SAGE's complete governance framework. By establishing precise phase constraints, explicit exclusions, and rigid boundary isolation, SAGE ensures absolute system stability and complete human-in-the-loop control.
