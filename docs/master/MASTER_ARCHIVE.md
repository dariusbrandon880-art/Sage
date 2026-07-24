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

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_62cee1b7
- **Timestamp**: 2026-07-24T06:59:38.778037+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_e81f883f
- **Timestamp**: 2026-07-24T06:59:38.805785+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_3bbfc7d3
- **Timestamp**: 2026-07-24T06:59:38.830474+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_d6ea2b00
- **Timestamp**: 2026-07-24T06:59:43.634428+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_9f5b58a2
- **Timestamp**: 2026-07-24T06:59:43.649801+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'ae3d5ba5-faa8-4958-8f50-b5d5aa2b9442' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_34f66623
- **Timestamp**: 2026-07-24T06:59:43.688446+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ae044d0e
- **Timestamp**: 2026-07-24T07:11:38.760946+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_1af775a8
- **Timestamp**: 2026-07-24T07:11:38.782031+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_76fdc758
- **Timestamp**: 2026-07-24T07:11:38.805706+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_86e8960d
- **Timestamp**: 2026-07-24T07:11:43.820940+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_5f2f696a
- **Timestamp**: 2026-07-24T07:11:43.834460+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'b22c5d84-d618-4a15-8b9d-0293d9c190ce' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_2f0c5995
- **Timestamp**: 2026-07-24T07:11:43.865340+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_62b7928a
- **Timestamp**: 2026-07-24T09:00:55.038746+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_264ecf55
- **Timestamp**: 2026-07-24T09:00:55.068444+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_ad778c0a
- **Timestamp**: 2026-07-24T09:00:55.094874+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_73c4cfb5
- **Timestamp**: 2026-07-24T09:01:00.911128+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_bd90d486
- **Timestamp**: 2026-07-24T09:01:00.922770+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision '3f08c1d5-11d1-4ef0-9b50-409a00ebca94' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_c9110e9d
- **Timestamp**: 2026-07-24T09:01:00.956757+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_14fc8333
- **Timestamp**: 2026-07-24T10:27:22.735045+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_6f4a33c2
- **Timestamp**: 2026-07-24T10:27:22.758511+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_a78c72d4
- **Timestamp**: 2026-07-24T10:27:22.780740+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_83ffd0c8
- **Timestamp**: 2026-07-24T10:27:28.676888+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_53cd9d53
- **Timestamp**: 2026-07-24T10:27:28.687694+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'b74d9fbf-0f3d-45e7-9af7-d2f6f4bee245' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_4d4f255e
- **Timestamp**: 2026-07-24T10:27:28.717104+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_879c5511
- **Timestamp**: 2026-07-24T10:32:35.371688+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: ci-propulsion-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_6a60817e
- **Timestamp**: 2026-07-24T10:32:35.388173+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-reconcile
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_509c36d7
- **Timestamp**: 2026-07-24T10:32:35.406144+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: e2e-pipeline-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_4f9a2eda
- **Timestamp**: 2026-07-24T10:32:41.700882+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: github-actions-ci
- **Lineage Details**: Validation report promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_afae2fca
- **Timestamp**: 2026-07-24T10:32:41.752677+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Approved Decision: ADR-010-redis-cache
- **Lineage Details**: Architecture decision 'bd611b46-2548-4f7d-97b4-d8b8bab72895' promoted to Master Archive by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_validation_report_987a2593
- **Timestamp**: 2026-07-24T10:32:41.781557+00:00
- **Payload Type**: `validation_report`
- **Title/Subject**: Validated Report: api-tests
- **Lineage Details**: Validation report promoted to Master Archive by Jules.
