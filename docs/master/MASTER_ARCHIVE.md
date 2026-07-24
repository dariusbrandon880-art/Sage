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

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_47cd4b03
- **Timestamp**: 2026-07-24T03:18:21.284365+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_6135984f
- **Timestamp**: 2026-07-24T03:18:21.299229+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'bbf7101f-0582-4b45-b3f2-4b7b34e2dbe8' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ff837d57
- **Timestamp**: 2026-07-24T03:18:21.408442+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_7334dcbf
- **Timestamp**: 2026-07-24T03:19:50.198240+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_1956f160
- **Timestamp**: 2026-07-24T03:19:50.211053+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision '9339c114-f011-4ec4-997f-0110287426b6' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_d57594ff
- **Timestamp**: 2026-07-24T03:19:50.242558+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_f1132b8e
- **Timestamp**: 2026-07-24T03:27:08.436280+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_ceed211c
- **Timestamp**: 2026-07-24T03:27:08.451534+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'fa00ef39-3d3c-458c-b2c9-860de49a8523' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_450f0142
- **Timestamp**: 2026-07-24T03:27:08.480312+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_cc6b5388
- **Timestamp**: 2026-07-24T03:30:52.590574+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_b7a5a7da
- **Timestamp**: 2026-07-24T03:30:52.603806+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'ff902ac4-01c9-4c6f-8e16-1e63d553529c' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_80175702
- **Timestamp**: 2026-07-24T03:30:52.633355+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_9ae6b8dc
- **Timestamp**: 2026-07-24T05:10:59.921252+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_1795fe91
- **Timestamp**: 2026-07-24T05:11:00.019794+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_06eef7f1
- **Timestamp**: 2026-07-24T05:11:00.180320+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_e2207ea1
- **Timestamp**: 2026-07-24T05:13:03.789370+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_aa3ef89c
- **Timestamp**: 2026-07-24T05:13:03.811039+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_987ac46c
- **Timestamp**: 2026-07-24T05:13:03.934887+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_a3ee047d
- **Timestamp**: 2026-07-24T05:23:42.374015+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_c361fdc6
- **Timestamp**: 2026-07-24T05:23:42.394831+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ea1bc287
- **Timestamp**: 2026-07-24T05:23:42.415841+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_e0b4d080
- **Timestamp**: 2026-07-24T05:23:46.394209+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_18b40c5c
- **Timestamp**: 2026-07-24T05:23:46.406580+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'bdc34a49-4153-4820-a836-7bc66b9634c7' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_437fa768
- **Timestamp**: 2026-07-24T05:23:46.442308+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_a1fd8ddd
- **Timestamp**: 2026-07-24T05:28:29.166178+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_f3b277eb
- **Timestamp**: 2026-07-24T05:28:29.182013+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_cb5d15d4
- **Timestamp**: 2026-07-24T05:28:29.199135+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_57d7c784
- **Timestamp**: 2026-07-24T05:28:33.105536+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_afab7973
- **Timestamp**: 2026-07-24T05:28:33.117850+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision '67cf3237-17c8-4b8e-8bea-86dde68f7d97' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ae3aca2d
- **Timestamp**: 2026-07-24T05:28:33.151038+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_702c8597
- **Timestamp**: 2026-07-24T05:30:22.342987+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_3045dcb8
- **Timestamp**: 2026-07-24T05:30:22.370324+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_2e039d12
- **Timestamp**: 2026-07-24T05:30:22.391876+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_a7617b1d
- **Timestamp**: 2026-07-24T05:30:26.367758+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_3f108867
- **Timestamp**: 2026-07-24T05:30:26.380657+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'dfdd1d7e-9f55-4fc2-a605-b4fcc4a0b389' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ff33be40
- **Timestamp**: 2026-07-24T05:30:26.410583+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.
