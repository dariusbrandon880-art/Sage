# SAGE MASTER ARCHIVE - Operational Reference

The SAGE Master Archive is the authoritative, immutable source of truth for validated engineering knowledge, decisions, and system specifications.

## 1. Core Architecture
The archive is managed by the `Archive` core engine (`sage/archive/core.py`) and backed by the `PersistentArchiveStore` (`sage/archive/persistence.py`).

### Data Structure (`ArchiveEntry`)
All archived items are strictly typed under `ArchiveEntry` (`sage/models.py`):
- **id**: Unique archive entry ID (`archive_` + UUID).
- **title**: High-level descriptive name of the validated asset.
- **tags**: Indexed keyword list for relationship mapping and indexing.
- **knowledge_state**: Defaults to `KnowledgeState.ARCHIVED` once finalized.
- **created_at**: Timestamp of instantiation (timezone-aware UTC).
- **validation_timestamp**: Timestamp of successful promotion.
- **decision_history**: List of associated `DecisionEntry` IDs that drove this state.
- **lineage**: Chain of previous memory object IDs (`MemoryObject.id`) that formed this knowledge.
- **content**: Structured dictionary containing the payload (specifications, schemas, facts).

---

## 2. Knowledge Promotion Workflow
The validation and promotion pathway guarantees that unverified hypothesis or draft state is scrutinized before it reaches immutability.

```
Hypothesis (MemoryObject in Lab Memory Store)
                      │
                      ▼
            Quality & Schema Check
         (ValidationSystem.validate_memory)
                      │
                      ▼
               Promote to VALIDATED
       (ValidationSystem.promote_to_validated)
                      │
                      ▼
              Associate Decision
          (DecisionTracker.record_decision)
                      │
                      ▼
         Promote to Permanent Master Archive
        (ValidationSystem.promote_to_archive)
```

### Validation Rules
1. **Substance Check**: Content cannot be empty and must contain non-empty keys or text.
2. **Type Enforcement**: Object type must be specified and conform to registered capability schemas.
3. **Traceability**: Memory tags and lineage chains must link to the active session ID.

---

## 3. Querying & Pagination
To ensure scalability, the Master Archive supports:
- Keyword substring searches over titles (`GET /archive/search/title/{title}`).
- Tag indexing (`GET /archive/search/tag/{tag}`).
- Chronological sorting with limit and offset parameters.

---

## 4. Validated Lineage Record: Architecture Alignment Preservation #25

- **Milestone Event**: Architecture Alignment Preservation #25
- **Status**: ✅ MERGED INTO MAIN
- **Commit**: d58e001
- **Validation**: ✅ Build/checks passed cleanly

### Core Governance & Specifications
The following core specifications are confirmed as SAGE 2 constitutional governance baselines:

#### A. SAGE 2 Unified Architecture Model
The structural tiers of SAGE 2 are locked into three non-overlapping execution zones:
1. **Continuity Layer**: Managed via ACR (Adaptive Continuity Runtime) for state serialization and CIV (Continuity Independence Validation) for rehydration verification.
2. **Intelligence Layer**: Comprises SKAL (intake validation), HSI-001 (Human-SAGE Interaction trust boundaries), and KL (Knowledge Longevity promotion pipeline).
3. **Discovery Layer**: Powered by speculative SAGE-X mathematical, historical, and scientific concepts.

#### B. Governed Knowledge Promotion Contract (SAGE-RT-KL-002)
- **Principal Directive**: SAGE must never autonomously write permanent architectural knowledge. Rule Candidates generated from Layer 2 (Working Evidence) require manual validation and authorized signature before promotion to Layer 3 (Immutable Ledger).

#### C. Strict Execution Separation Rules
- **Write-Pipeline**: Single-transaction, zero-trust, HMAC-authenticated state mutators (Objectives, Checkpoints, SKAL payloads).
- **Read-Pipeline**: Side-effect-free, read-only queries (diagnostics, metrics, search results).
