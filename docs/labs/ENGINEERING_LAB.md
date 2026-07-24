# SAGE ENGINEERING LAB - Code Architecture & System Internals

This laboratory document provides deep technical details for developers extending or maintaining SAGE.

---

## 1. Class Mapping & Data Flow
The core runtime integrates 6 highly specialized classes to coordinate continuity:

1. **`SageRuntime`** (`sage/runtime/engine.py`): The main process host. Handles starting, stopping, setting objectives, and writing global checkpoints.
2. **`ACRBridge`** (`sage/acr/bridge.py`): Tracks session lineage, lineage trees, and session graph depth to preserve parent-child task history across restarts.
3. **`Memory`** / **`MemoryStore`** (`sage/memory/`): Manages the list of `MemoryObject` entries, providing memory backend persistence and key/tag lookup structures.
4. **`Archive`** (`sage/archive/`): Manages `ArchiveEntry` promotions, creating persistent JSON documents in the `archive/` path.
5. **`DecisionTracker`** (`sage/decision.py`): Logs system-level developer decisions (`DecisionEntry`), tracing rationale and evidence links.
6. **`ValidationSystem`** (`sage/validation.py`): Performs multi-rule schema constraints validation on memories and oversees the promotion workflow.

```
                  ┌──────────────────────┐
                  │     SageRuntime      │
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   Memory    │  │   Archive   │  │  Decisions  │
     └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 2. Test Suite & Hardening Procedures
SAGE features a complete automated verification test suite:

- **Unit & Integration Tests**: Located in `tests/`, covering serialization, lineaging, endpoints, config environments, and state rehydration.
- **Running Tests**:
  ```bash
  python -m pytest
  ```
- **Code Style Linting**: Enforced with Black and Ruff with zero style exceptions.
  ```bash
  black --check sage/ tests/
  ruff check sage/ tests/
  ```
- **Timezone Safety**: Python 3.12+ compliant timezone-aware datetimes are enforced via `datetime.now(timezone.utc)`.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_bd3f2b63
- **Timestamp**: 2026-07-24T03:18:21.380183+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_21328e2a
- **Timestamp**: 2026-07-24T03:19:50.217793+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_79bbf261
- **Timestamp**: 2026-07-24T03:27:08.457654+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_f038d6d5
- **Timestamp**: 2026-07-24T03:30:52.609165+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_8f2c1099
- **Timestamp**: 2026-07-24T05:23:46.412617+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_ec32c8e3
- **Timestamp**: 2026-07-24T05:28:33.123370+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_f17be815
- **Timestamp**: 2026-07-24T05:30:26.386497+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_fa39eab0
- **Timestamp**: 2026-07-24T06:59:43.656999+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_1687a637
- **Timestamp**: 2026-07-24T07:11:43.840296+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.

### SAGE-SKAL Promoted Lineage Entry: skal_architecture_decision_421f9617
- **Timestamp**: 2026-07-24T09:01:00.928810+00:00
- **Payload Type**: `architecture_decision`
- **Title/Subject**: Draft Decision: ADR-011-experimental
- **Lineage Details**: Unapproved decision routed to Engineering Lab.
