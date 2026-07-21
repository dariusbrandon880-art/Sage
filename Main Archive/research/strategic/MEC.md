# Multi-user Engineering Continuity (MEC) Spec

The Multi-user Engineering Continuity spec defines how SAGE coordinates and resolves simultaneous development actions from multiple human developers or AI agents.

## 1. Concept Overview
In a collaborative environment, different contributors might work on overlapping tasks. MEC prevents state corruption through:
- **Locking Mechanisms**: Introduces file-based write locks on `.sage/sage_state.json` to prevent concurrent write collisions.
- **Lineage Merging**: Resolves divergent session lineage paths using standard Git merge principles.
- **Traceable Attribution**: Attributes every `MemoryObject` and `DecisionEntry` to its specific author or AI engine client ID.

## 2. Collaborative Sync
When a developer pulls from main, SAGE automatically merges incoming Master Archive entries, indexing new knowledge without overwriting local unpromoted memory objects in the lab workspace.
