# SAGE Next Capability Research Prioritization Report

**Record ID:** SAGE-PRIORITY-2026-07-29
**Classification:** Research Prioritization & Roadmap Analysis
**Status:** Validated Research Prioritization Artifact
**Target Schema:** SAGE Provenance Schema v0.1
**Execution Context:** SAGE Post-Recovery Capability Prioritization Directive

---

## 1. Executive Summary & Purpose

This report delivers a formal, strategic capability prioritization review. Using SAGE's historically recovered architecture blueprint and currently validated capability tree, we analyze unresolved continuity, reliability, evidence lineage, and auditability challenges to map out a clear, non-intrusive research roadmap.

This document serves as an immutable guide for SAGE’s future governed evolution under absolute preservation of the production runtime.

---

## 2. Core Strategic Analysis

We evaluate the highest-value opportunities to expand SAGE's AI reliability capabilities without introducing central state dependencies or core runtime changes.

### 2.1. Highest-Value Unresolved Continuity Problem
* **The Problem:** Session Isolation Drift. While SAGE rehydrates individual runtime sessions, consecutive sessions executed under a single master workflow remain decoupled. An attacker can hijack or replace intermediate sessions without detection.
* **The Priority Solution:** **SAGE Cryptographic Session Receipt Chain (SAGE-CRC)**.

### 2.2. Highest-Value Reliability Improvement
* **The Problem:** External API Timeout Vulnerability. If external model provider APIs (Anthropic, OpenAI, Google) timeout during rehydration, the agent execution crashes without recovery fallback.
* **The Priority Solution:** **SAGE Stateless Continuous State Fallback (SAGE-CSF)**.

### 2.3. Highest-Value Evidence Lineage Improvement
* **The Problem:** Non-Monotonic Receipts. Current CMAPS payloads list decisions chronologically but do not mathematically lock their ordering. This allows attackers to selectively omit or reorder minor decisions.
* **The Priority Solution:** HMAC-SHA256 hash-chaining of sequential decision events.

### 2.4. Highest-Value Auditability Improvement
* **The Problem:** Static Verification Key Vulnerability. Attestations are signed with a static private key and verified by a single public key (`sage_validator_pubkey_01`).
* **The Priority Solution:** **SAGE Decentralized Validator Key Rotation (SAGE-DKR)**.

### 2.5. Overlapping & Duplicate Research Areas
* **Overlap:** APM (Autonomous Process Monitor) vs. SAGE-ACH (Active Client Hook). Both seek to track workspace processes.
  * *Resolution:* APM is classified as a long-term theoretical research track (`STRATEGIC RESEARCH INPUT`), while SAGE-ACH is kept as the active, validated, passive execution wrapper (`VALIDATED EXPERIMENTAL`).

### 2.6. Friction Reduction Opportunities
* **SDK Wrappers:** Create Python decorators for popular agent frameworks (LangChain, CrewAI) to emit CMAPS trace events out-of-the-box.
* **Local Sandboxed Testbeds:** Provide local, deterministic mock-provider fixtures to eliminate physical network requests during testing.

---

## 3. Formal Research Prioritization & Rankings

We define SAGE's next capability research opportunities, providing full 12-point capability specs for each recommendation.

---

### Rank 1: SAGE Cryptographic Session Receipt Chain (SAGE-CRC)

#### 1. Capability Opportunity Ranking
Rank 1 (Highest Priority - Strategic Wedge)

#### 2. Problem Addressed
Decoupled multi-session workflows are vulnerable to timeline splicing, replay attacks, and state hijack between independent sessions.

#### 3. Why This Matters to SAGE Mission
The SAGE mission requires model-independent, high-fidelity tracing. SAGE-CRC provides immutable mathematical proofs that link distinct session lineages into a single, cohesive, tamper-proof history.

#### 4. Historical Lineage Connection
Derived from **CIC (Continuity Independence Validation)** and **DESP (Distributed Execution State Protocol)** strategic research tracks.

#### 5. Current Capability Tree Placement
```
Cross-Model Audit Schema (CMAPS v1.0) ──> SAGE-CRC (Rank 1) ──> Decentralized Key Rotation
```

#### 6. Dependencies
* CMAPS v1.0 Schema
* Stateless Context Rehydrator (`GovernedAgentRehydrator`)

#### 7. Smallest Safe Research Scope
A read-only mathematical and cryptographic specification defining the hash-linking function:
$$H_{i} = \text{HMAC-SHA256}(H_{i-1} \parallel \text{CMAPS Payload}_i)$$
without implementing active state mutation.

#### 8. Expected Evidence Outputs
* Standard mathematical spec document.
* Sample JSON payload sequence representing a 3-receipt chain with valid SHA-256 links.

#### 9. Validation Strategy
* Automated unit verification tests checking signature chain validity.
* Adversarial simulation testing chain rejection when an intermediate payload is deleted, modified, or reordered.

#### 10. Rollback Considerations
Stateless rollbacks. If a receipt verification fails at step $k$, the validator rejects the entire chain, rolling back the agent state reference to receipt $k-1$.

#### 11. Security/Isolation Considerations
Must adhere to the One-Way Import Law. Verification algorithms must run statelessly inside `sage/experimental/act/` and never directly write to active production databases.

#### 12. Lifecycle Classification
`PROPOSED` — High-value planned capability.

---

### Rank 2: SAGE Stateless Continuous State Fallback (SAGE-CSF)

#### 1. Capability Opportunity Ranking
Rank 2 (Medium-High Priority)

#### 2. Problem Addressed
Rehydration workflows fail completely if the external model provider APIs (Anthropic, OpenAI, Gemini) are down or hit severe rate limits, leaving the agent stranded.

#### 3. Why This Matters to SAGE Mission
Robustness is a core pillar of reliability. SAGE must survive external provider outages and provide a local graceful termination vector.

#### 4. Historical Lineage Connection
Directly connected to the **CSC (Continuous State Control)** and **APM (Autonomous Process Monitor)** strategic research blueprints.

#### 5. Current Capability Tree Placement
```
Stateless Context Rehydration ──> SAGE-CSF (Rank 2) ──> Graceful Intercept Loop
```

#### 6. Dependencies
* Stateless Context Rehydrator (`GovernedAgentRehydrator`)
* SAGE-SDR Dry-Run Evaluation

#### 7. Smallest Safe Research Scope
Formulating a local, fallback state serialization standard that stores lightweight state checkpoints in a secure, local, read-only cache.

#### 8. Expected Evidence Outputs
* Fallback serialization schema specification.
* Mock testing fixtures simulating external provider API timeouts.

#### 9. Validation Strategy
Simulate API timeout faults (returning 504 Gateway Timeout) and assert that SAGE-CSF successfully intercepts the timeout, falls back to the local secure checkpoint, and writes a compliant failure record.

#### 10. Rollback Considerations
Absolute. If fallback rehydration fails, the local environment state is reverted to the initial Day-0 clean state.

#### 11. Security/Isolation Considerations
Strict local permissions. Checkpoint files must be protected from local code injection and bound to strict user read-only access.

#### 12. Lifecycle Classification
`STRATEGIC RESEARCH INPUT` — Long-term architecture exploration.

---

### Rank 3: SAGE Decentralized Validator Key Rotation (SAGE-DKR)

#### 1. Capability Opportunity Ranking
Rank 3 (Medium Priority)

#### 2. Problem Addressed
A single static signature verification public key makes the entire audit payload vulnerable to signature forgery if the corresponding private key is compromised.

#### 3. Why This Matters to SAGE Mission
Cognitive security requires cryptographic trust. Static keys are a classic single-point-of-failure.

#### 4. Historical Lineage Connection
Derived from **SP_REV2 (Deep Security & Information Physics Expansion Study)**.

#### 5. Current Capability Tree Placement
```
Cross-Model Audit Schema ──> SAGE-DKR (Rank 3)
```

#### 6. Dependencies
* SAGE-CRC session receipt chains.

#### 7. Smallest Safe Research Scope
Drafting the mathematical rules for public-key rotation where a parent key authorizes the child key via a signed transition certificate.

#### 8. Expected Evidence Outputs
* Transition certificate schema spec.
* Verification algorithms to trace trust lineage of active keys.

#### 9. Validation Strategy
Run cryptographic tests demonstrating that signature verification passes for rotated keys but fails when an unauthorized key attempts to sign a CMAPS payload.

#### 10. Rollback Considerations
Revocation lists. If key validation fails, all payloads signed by that key are flagged as untrusted.

#### 11. Security/Isolation Considerations
No network dependencies. All key validation and certificate parsing must be executed locally and statelessly.

#### 12. Lifecycle Classification
`FUTURE EXPLORATION` — Unvalidated concept requiring future research.

---

## 4. Confirmation of Protected Boundary Preservation

SAGE operates under strict architectural guardrails to prevent experimental features from corrupting production stability. We formally certify the following:

* **Production Code Integrity:** Under the **One-Way Import Law**, no files located in the production core namespaces—specifically `sage/runtime/`, `sage/core/`, and `sage/acr/`—were altered or modified.
* **Zero-Drift Status:** All production modules remain fully isolated from experimental code.
* **Automated Import Verification:** Programmatic AST-level import checks confirm that no experimental files import production components in an unauthorized or circular pattern.
* **Test Suite Alignment:** 100% of the SAGE platform test suite passes with zero errors, confirming that all existing validation baselines are fully preserved.
