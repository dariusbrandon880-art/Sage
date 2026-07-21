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
