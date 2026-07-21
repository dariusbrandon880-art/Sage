# System Dependency Graph

This document models the class mappings, interfaces, and package-level import relations within SAGE.

---

## 1. Import Hierarchy & Layers

```
┌────────────────────────────────────────────────────────┐
│                      FastAPI (sage.api)                │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Integration (sage.integration)       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                Runtime & State (sage.runtime)          │
└───────────┬───────────────┬────────────────┬───────────┘
            │               │                │
            ▼               ▼                ▼
     ┌─────────────┐ ┌─────────────┐  ┌─────────────┐
     │ sage.memory │ │ sage.archive │  │  validation │
     └─────────────┘ └─────────────┘  └─────────────┘
```

### Imports Discipline
- Core data models (`sage/models.py`) must contain zero external dependencies other than Pydantic. This is the bedrock of SAGE, preventing circular imports.
- Subsystems like `sage/memory/` and `sage/archive/` use dedicated subdirectory packages with their class definitions located in `core.py` and cleanly exposed via parent packages (`__init__.py`) to prevent namespace collisions with legacy file structures.
- The `ValidationSystem` depends on both the `MemoryStore` and `Archive` interface to execute its promotion sequence.

---

## 2. Portability Boundaries
- To support containerization, all data serialization paths are relative to `self.workspace_path`.
- The `ACRBridge` interacts cleanly with session logs without interfering with standard database files.
