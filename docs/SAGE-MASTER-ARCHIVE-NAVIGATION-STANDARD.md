# SAGE Master Archive Navigation Standard

**Record ID:** SAGE-NAV-STANDARD-2026-07-29
**Classification:** Documentation Architecture Foundation
**Status:** Validated
**Target Schema:** SAGE Provenance Schema v0.1
**Execution Context:** SAGE Documentation Health Audit and Continuity Navigation Standard Directive

---

## 1. Executive Summary & Purpose

This standard defines the **SAGE Master Archive Navigation Standard**.

As SAGE grows, human engineers and automated AI agents must have a deterministic protocol to navigate the directory structure, trace decisions to their physical validation evidence, and re-establish session context. This standard guarantees that SAGE's immutable Master Archive remains a highly organized, easily discoverable repository of truth.

---

## 2. Canonical Entry Points

SAGE defines exactly two canonical entry points for any engineer or agent seeking truth:
1. **The Human Entry Point (`README.md`):** High-level mission statement, repository overview, and quick-start testing commands.
2. **The Machine/Agent Entry Point (`Main Archive/INDEX.md`):** The definitive, immutable index mapping every spec, decision record, research paper, and validation ledger to its formal provenance lifecycle classification.

---

## 3. Document Discovery Flow

Agents or engineers seeking information must follow this sequential document discovery flow:

```
            ┌──────────────────────────────────────────┐
            │          Step 1: Check Index             │
            │          (Main Archive/INDEX.md)         │
            └──────────────────────────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │       Step 2: Read Reference Map         │
            │        (SAGE-SYNC-005 Knowledge Graph)   │
            └──────────────────────────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │        Step 3: Read Specific Document    │
            │          (Target Spec/Report)            │
            └──────────────────────────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │       Step 4: Verify Test Code           │
            │             (tests/ directory)           │
            └──────────────────────────────────────────┘
```

---

## 4. Structured Lookup Protocols

SAGE organizes its documents into five explicit lookup structures to make automated query parsing seamless.

### 4.1. Capability Lookup Structure
* *Protocol:* Trace the capability from the active tree to its proposal and physical evidence.
* *Example:* Continuity Control $\rightarrow$ `docs/SAGE-ACT-MILESTONE-3-CONTINUITY-CONTROL-PROPOSAL.md` $\rightarrow$ `tests/experimental/test_cross_model_audit_schema.py` (Unit tests verifying monotonicity).

### 4.2. Research Lookup Structure
* *Protocol:* Trace theoretical research specs under `Main Archive/research/strategic/` to their parent index and classification status.
* *Example:* SKAL spec $\rightarrow$ `Main Archive/research/strategic/SKAL.md` $\rightarrow$ Classified as `STRATEGIC RESEARCH INPUT`.

### 4.3. Decision Lookup Structure
* *Protocol:* Trace architectural decisions (ADRs) to their baseline parameters and validation files.
* *Example:* Decoupling control plane $\rightarrow$ `Main Archive/adr/ADR-001-architecture-baseline.md` $\rightarrow$ Verified via lazy-loading test suites.

### 4.4. Validation Lookup Structure
* *Protocol:* Trace an active capability to its shadow telemetry run logs or compliance tests.
* *Example:* Shadow Telemetry $\rightarrow$ `docs/SAGE-MISSION-0.7-SHADOW-EVIDENCE-REVIEW.md` $\rightarrow$ Provenance verified.

### 4.5. Historical Lineage Lookup Structure
* *Protocol:* Check `docs/SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md` to map concept origins, rejected alternatives, and inspiration analogies.

---

## 5. Cross-Reference and Formatting Conventions

To ensure perfect structural consistency across all SAGE directories:
1. **Cite Unique Document IDs:** Always mention the unique document identifier alongside its relative link.
   * *Example:* `SAGE-ACT-001 ([CMAPS](../docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md))`
2. **Metadata Front-Matter:** Every document must carry the standard front-matter metadata block defining its Record ID, Classification, and Validation level.
3. **Anchor Consistency:** Maintain standardized section headings to prevent broken sub-links across reports.

---

## 6. Future Automated Retrieval Strategy

This navigation standard is fully optimized for automated AI-agent indexing and retrieval:
* **JSON-LD Schema Integration:** Future tools can parse SAGE metadata to automatically generate JSON-LD schema blocks, mapping documentation relationships directly into semantic search engines.
* **Deterministic Chunking:** Delimiting sections strictly by unique sub-headers allows RAG (Retrieval-Augmented Generation) parsers to generate precise vector embeddings without mixing unrelated context blocks.
