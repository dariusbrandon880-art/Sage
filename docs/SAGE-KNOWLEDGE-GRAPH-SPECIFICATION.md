# SAGE Knowledge Graph Specification

**Record ID:** SAGE-KG-SPEC-2026-07-30
**Classification:** Strategic Research & Relational Specification
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Non-mutating structural model mapping.

---

## 1. Introduction & Relational Schema

This document specifies the **SAGE Relational Knowledge Graph Specification**. By formalizing explicit relationship predicates between SAGE's documents, research tracks, and validated code baselines, SAGE transitions from a passive, flat text archive into an active, multi-dimensional relational knowledge graph.

### 1.1. Edge Predicates (Relationship Definitions)
The knowledge graph uses typed directional edge predicates to represent structural dependencies, design evolution, and validation mappings:

* **`derived_from` (Historical Lineage):** Shows conceptual or technical evolution (e.g., SAGE 2 is derived from SAGE monolithic ideas).
* **`validated_by` (Evidence Mapping):** Maps a specification or proposal to its corresponding test file or evaluation report.
* **`originates_from` (Research Inception):** Connects a capability to its originating strategic speculation or creative inspiration.
* **`depends_on` (Structural Dependency):** Shows direct runtime or architectural dependencies between modules or protocols.
* **`replaces` (Deprecation/Replacement):** Identifies when a concept is superseded by an updated standard (e.g., CMAPS replaces raw log memory formats).
* **`proposes` (Proposal History):** Connects a capability parent to its corresponding proposal or roadmap spec.
* **`governed_by` (Compliance Boundary):** Indicates which constitutional rule or SPEK policy regulates a given capability.

---

## 2. Explicit Node & Edge Mappings

This section defines the precise relational triples (Node ──► Edge ──► Node) representing SAGE's architectural, research, and validation boundaries.

### 2.1. Architectural & Historical Lineage Triples
1. `SAGE 2 Architecture` ──► `derived_from` ──► `Monolithic Cognitive Loop`
2. `SAGE 2 Architecture` ──► `governed_by` ──► `SAGE Constitution (CONSTITUTION.md)`
3. `Jules Sandboxed Runner` ──► `derived_from` ──► `Marvel Friday Archetype`
4. `SAGE Multi-Role Collaborator Model` ──► `derived_from` ──► `Marvel Jarvis Model (as a decentralized alternative)`
5. `ActiveClientHook (SAGE-ACH)` ──► `replaces` ──► `Monolithic unmonitored shell executions`
6. `SAGE-ACH` ──► `originates_from` ──► `Prometheus Evolutionary Containment Protocols`

### 2.2. Research to Proposal & Evaluation Triples
1. `Stateless Context Rehydration` ──► `proposes` ──► `Milestone 3 Proposal (SAGE-ACT-MILESTONE-3-PROPOSAL.md)`
2. `Milestone 3 Proposal` ──► `evaluated_by` ──► `Milestone 3 Proposal Review Record`
3. `Stateless Context Rehydration` ──► `validated_by` ──► `Cross-Model Audit Payload Schema (CMAPS v1.0)`
4. `CMAPS v1.0` ──► `originates_from` ──► `Star Wars Holocrons & Security Clearance metaphors`
5. `CMAPS v1.0` ──► `validated_by` ──► `SAGE-CROSS-MODEL-AUDIT-ADVERSARIAL-VALIDATION-REPORT.md`
6. `SAGE-ACT Sandbox` ──► `governed_by` ──► `One-Way Import Law (SAGE-EVOL-001)`

### 2.3. Future Dependency Triples
1. `SAGE-CRC Cryptographic Session Receipt Chain` ──► `depends_on` ──► `Stateless Context Rehydration`
2. `SAGE-SDR Safe Dry-Run Rehydration` ──► `depends_on` ──► `SAGE-ACH Telemetry Diffs`
3. `SAGE-SDR Safe Dry-Run Rehydration` ──► `originates_from` ──► `Prometheus Evolutionary Containment Protocols`
4. `SAGE-ACT-SRACA (Milestone 5 Auditor)` ──► `depends_on` ──► `SAGE-CRC` & `SAGE-SDR`

---

## 3. Relational Knowledge Graph Visualizations

The following relational diagrams illustrate SAGE’s fully connected knowledge structure, preserving the conceptual flow across different layers:

### 3.1. Creative Metaphors ──► Architectural Influences
```
[Prometheus Containment] ────(originates)───► [One-Way Import Law AST] ────(governs)────► [SAGE-ACT Namespace]
                                                        ▲
                                                        │ (derived_from)
[Marvel Jarvis Model] ───────(replaced_by)──► [Multi-Role Collaborator] ──(governed_by)──► [SAGE Constitution]
                                                        ▲
                                                        │ (executes)
[Marvel Friday Model] ───────(originates)───► [Jules Sandboxed Runner] ────(validated_by)─► [test_runtime_contract]
```

### 3.2. Core Capabilities ──► Validation Evidence Lineages
```
[SPEK Policy Kernel v1.1] ───(validated_by)─► [tests/test_spek.py] ─────────(depends_on)──► [spek_vault.json]
                                                        ▲
                                                        │ (governs)
[SAGE-ACR Nonce Ledger] ────(validated_by)─► [tests/test_acr.py] ───────────(depends_on)──► [nonce_ledger.py]
                                                        ▲
                                                        │ (attests)
[CMAPS Execution Traces] ───(validated_by)─► [test_cross_model_audit_schema]─(depends_on)──► [rehydrator.py]
```

---

## 4. Expected Continuity & Navigation Benefits

The formalization of these triples allows future SAGE rehydration sessions to rapidly parse, trace, and navigate SAGE's vast context:
* **Algorithmic Path Traversal:** A future developer agent can algorithmically traverse these triples to find the exact test files, ADRs, or creative speculations associated with any active core module.
* **Validation Provenance Protection:** When promoting a rule candidate, SAGE can trace its lineage path back to the originating strategic spec, verifying that it remains within constitutional boundaries.

---

*Prepared by Jules, Software Engineer.*
*Submitted and Validated under Master Archive Authority.*
