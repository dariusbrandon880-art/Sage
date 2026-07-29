# SAGE Archive Navigation Standard

**Record ID:** SAGE-ANS-2026-07-30
**Classification:** Documentation Governance Standard
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Standardizing document-only reference schemas.

---

## 1. Document Discovery & Canonical Source Identification

To ensure seamless cognitive continuity and zero search latency during SAGE state rehydration, this standard establishes the authoritative guidelines for discovering, traversing, and referencing repository documents.

### 1.1. Document Discovery Rules
1. **Autoritative Entry Point:** All search and discovery operations must initiate from `Main Archive/INDEX.md` (The Canonical Index).
2. **Category Isolation:** Every record must be listed under its appropriate section in the index (Architecture Specs, Strategic Research, ADRs, Roadmaps, or Reports).
3. **Keyword Searches:** Title searches must match the exact Title or Record ID used in the index register.

### 1.2. Canonical Source Identification
* **Ground-Truth Source:** The Git repository's `main` branch serves as SAGE's immutable ground-truth.
* **Master Archive Directory:** Documents located in `docs/master/` and `Main Archive/` represent canonical historical and architectural records once validated and signed.
* **Lab Space Directory:** Documents located in `docs/labs/` or under local workspace folders represent working hypotheses (`Layer 2 - Working Evidence`) and are non-canonical until promoted.

---

## 2. Naming & Reference Identifier Conventions

### 2.1. File Naming Conventions
* **Case and Hyphenation:** All new documentation files must use uppercase alphanumeric characters separated by hyphens (e.g., `SAGE-ARCHIVE-NAVIGATION-STANDARD.md`).
* **Extension:** Files must use the standard Markdown extension `.md`.

### 2.2. Reference Identifier Conventions
Every strategic, operational, or governance document must feature a standardized header containing a unique **Record ID** matching the following schema:
$$\text{Record ID} = \text{SAGE} - \text{ABBREV} - \text{YYYY} - \text{MM} - \text{DD}$$
*Example:* `SAGE-ANS-2026-07-30`

---

## 3. Relationship Traversal & Cross-Linking Standards

Future collaborator sessions must traverse documentation dependencies using explicit, bi-directional cross-reference headers.

```
                  ┌─────────────────────────────────┐
                  │      Parent Specification       │
                  └───────────────┬─────────────────┘
                                  │ (governs / depends_on)
                                  ▼
                  ┌─────────────────────────────────┐
                  │    Downstream Proposal / Spec   │
                  └───────────────┬─────────────────┘
                                  │ (validated_by)
                                  ▼
                  ┌─────────────────────────────────┐
                  │      Verification Evidence      │
                  └─────────────────────────────────┘
```

### 3.1. Standard Cross-Linking Headers
Every strategic document must conclude with a standard **Lineage & References** section containing:
* **Parent Spec Link:** Direct link to the governing parent document.
* **Alternative Approaches:** Direct links to any alternative or rejected concept documents.
* **Evidence Link:** Direct links to the corresponding test file or validation receipt.
* **Downstream Research:** Direct links to dependent roadmap items.

---

## 4. Lineage & Evidence Attachment Requirements

### 4.1. Decision Lineage Requirements
Every major architectural decision must document its complete rationale, including:
* *Why Proposed:* The structural motivation.
* *Problem Solved:* The technical friction point addressed.
* *Alternatives Considered:* Non-selected designs and the explicit reasons for their rejection.

### 4.2. Capability Lineage Requirements
Any new capability proposal must trace its ancestry directly to the founding SAGE blueprint or general roadmap specs.

### 4.3. Evidence Attachment Requirements
No capability or strategy is considered validated without a corresponding **Evidence Attachment**:
* **Technical Evidence:** Must link directly to green passing unit/integration test files (e.g., `tests/test_spek.py`).
* **Operational Evidence:** Must link to a signed post-merge validation receipt or execution gate report.

---

## 5. Historical & Retired Concept Preservation Rules

### 5.1. Historical Lineage Requirements
All documents must preserve their historical design evolution. Earlier design iterations, creative metaphors (Marvel, Star Wars, Prometheus), and scientific analogs are kept intact as **Historical Strategic Inputs** and must never be stripped or deleted during refactoring.

### 5.2. Retired Concept Preservation Rules
* **Marking Rules:** When a capability or concept is superseded or abandoned, it must **not** be deleted. Instead, its header status must be set to `RETIRED` or `ARCHIVED EXPLORATION`, and it must be moved to `Main Archive/research/archive/`.
* **Replacement Mapping:** The document must feature an explicit link pointing to its active successor spec (Edge predicate: `replaces`).

---

## 6. Duplicate Documentation & Promotion Rules

### 6.1. Duplicate Documentation Handling Rules
If duplicate records or overlapping conceptual summaries are discovered across files:
1. **Document the Overlap:** Compile the findings in a formal health assessment report.
2. **Do Not Merge Automatically:** Maintain separation to prevent state-drift until a human operator authorizes a consolidation.
3. **Cross-Referencing:** Add temporary "Overlap Warnings" to the affected headers linking them to each other.

### 6.2. Archive Promotion Reference Rules
When promoting an unverified proposal (`Layer 2`) to the immutable Master Archive (`Layer 3`), SAGE must update the `Main Archive/INDEX.md` file to register its new lifecycle status. The promotion must reference the exact Record ID and the corresponding automated validation receipt.

---

*Standardized and Validated under Master Archive Authority.*
