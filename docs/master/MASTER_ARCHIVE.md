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
