# SAGE Index Layer v0.1 Design Record: Evolutionary Schema & Lineage Models

**Record ID:** SAGE-DR-INDEX-001-2026-07-27
**Classification:** Research and Prototyping / Lab Only
**Status:** PROPOSED
**Target Path:** `sage/lab/index_layer_v0_1/`
**Research Node:** Jules (SAGE Engineering Node)

---

## 1. Scope & Isolation Boundary

This design record establishes the active research expansion for the **SAGE Index Layer v0.1** within the authorized lab workspace. In strict compliance with the **One-Way Import Law**, all models, schemas, and tracking logic detailed herein operate under sandbox constraints:
1.  **Zero Runtime Modifications:** No production code in `sage/runtime/` or `sage/core/` references or imports files from this lab directory.
2.  **No Production Side Effects:** This work is preserved strictly for cognitive validation and research purposes.

---

## 2. Provenance Schema Improvements

To transition SAGE's decentralized tracking from basic JSON metadata to a secure, audit-hardened structure, we propose the following schema improvements:

### 2.1. Cryptographic Record Salt & Entropy
- **Issue:** Standard document hashing allows predictable hash analysis, potentially revealing document content from known indices.
- **Improvement:** Inject an ephemeral `nonce` or a 16-byte cryptographically secure salt into the hash calculation block. This ensures that even identical files generate unique, context-tied provenance hashes.

### 2.2. Human-in-the-Loop Multi-Signature Support
- **Improvement:** Standardize the `signature` field to support multiple signatures (array of objects), verifying that both the creating AI Agent (e.g. Google AI or ChatGPT) and the approving Human Operator have signed the record before promotion:
```json
"signatures": [
  {
    "agent_role": "executor",
    "node_id": "Jules",
    "timestamp": "2026-07-27T14:50:00Z",
    "hash": "abc123executorhash"
  },
  {
    "agent_role": "approver",
    "node_id": "HumanOperator",
    "timestamp": "2026-07-27T14:55:00Z",
    "hash": "def456approverhash"
  }
]
```

---

## 3. Metadata Lineage Models

To guarantee trace-causality across complex multi-step rehydration, rollback, and migration events, SAGE maps documents using a **Directed Acyclic Graph (DAG)** lineage model:

```
[Origin State / Spec] ────➔ [PR / Implementation] ────➔ [Validation / Receipt]
         │                                                      │
         └───────────── Ancestral Link (Parent IDs) ────────────┘
```

- **Lineage Properties:**
  - `ancestor_chain`: A chronological array of parent document hashes tracking the exact path from origin constitution to current version.
  - `dependency_depth`: Integer indicating the nesting level to prevent infinite graph loops during traversals.
  - `branch_lineage_id`: String identifying the Git branch context (e.g. `feature/sage-evol-001-sync`) where the transaction was initialized.

---

## 4. Archive Artifact Relationship Mapping

Document metadata is not isolated; SAGE maps structural dependencies between artifacts to detect gaps automatically:

1.  **Constitutional Dependency:** Links strategic specs (under `Main Archive/research/strategic/`) back to their authorizing constitutional laws (`docs/master/CONSTITUTION.md`).
2.  **Technical Dependency (Imports/APIs):** Automatically scans python file headers to build a dependency matrix showing which modules import others, mapping imports against the Five Tiers of SAGE's architecture.
3.  **Audit Trail linking:** Associates every verification report (under Section 5) with its physical attestation receipt (`sage_data/compliance/`). If an index entry claims to be `VALIDATED` but has no corresponding receipt hash in the ledger, SAGE flags a **Provenance Gap**.

---

## 5. Lifecycle State Tracking Improvements

SAGE defines a deterministic state-machine for document lifecycles to standardize quality gates:

```
[PROPOSED] ──(Auto-Logger Checks)──➔ [VALIDATED] ──(Approval Gate)──➔ [ARCHIVE_CANDIDATE] ──(Merge/Sign)──➔ [CANONICAL]
```

- **Lifecycle Transition Rules:**
  - **PROPOSED:** Default state for newly created specs, research drafts, or lab experiments.
  - **VALIDATED:** Assigned only after 100% test suites pass and file hashes are registered in the compliance log.
  - **ARCHIVE_CANDIDATE:** Assigned once the Human Operator pre-approves the document for promotion.
  - **CANONICAL:** Permanent, locked status assigned when the file is successfully merged into the canonical main branch and signed off.

---

## 6. Prototyping Code Blueprint

```python
# SAGE Prototyping Code Blueprint (Lab Only - Never Imported in Production)
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Dict, Any

class EnhancedProvenanceRecord(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    hash: str
    salt: str
    signatures: List[Dict[str, Any]] = Field(default_factory=list)
    lifecycle_state: str = "PROPOSED"  # PROPOSED, VALIDATED, ARCHIVE_CANDIDATE, CANONICAL
    ancestor_chain: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
