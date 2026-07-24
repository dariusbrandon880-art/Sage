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

---

## 3. Engineering Lineage: SAGE 2 Continuity Update & Tracking

- **Milestone Event**: Architecture Alignment Preservation #25
- **Status**: ✅ MERGED INTO MAIN
- **Merge Commit**: d58e001
- **Changed Files**:
  - `docs/master/CONSTITUTION.md`
  - `docs/master/ROADMAP.md`
  - `.sage/ROADMAP.md`
  - `Main Archive/INDEX.md`
  - `Main Archive/research/strategic/CIC.md`
  - `Main Archive/research/strategic/HSI.md`
  - `Main Archive/research/strategic/SAGE_Research_Track_Comparative_Intelligence_Architecture_Study_Review.md`
  - `sage/validation.py`
  - `sage/acr/skal.py`
  - `sage/api.py`
  - `tests/test_reliability_and_skal.py`

### Repository Alignment Status
- All core files (under `sage/` and `tests/`) are verified 100% compliant with locked SAGE 2 Unified Architecture specifications, timezone-aware UTC datetime guidelines, and zero-drift parameters.

### Priority Backlog (Future Engineering Tasks)
The following tasks are scheduled for future milestone iterations as controlled implementation tasks:
1. **`state_calibration.py` Integration**: Refine continuous state calibrations during rehydration events.
2. **`state_validator.py` Completion**: Enhance deep validator rules and dependency graph traversal checks.
3. **`memory_importance.py` Pipeline**: Implement dynamic memory importance ranking to drive automated caching.
4. **`apoptosis_manager.py` Lifecycle Handling**: Safe, scheduled process pruning and background process garbage collection.
5. **Repository Topology Cleanup**: Consolidate redundant configuration patterns and obsolete test logs.
