# Canonical Index Registry (CIR) Spec

The Canonical Index Registry is the centralized schema and indexing authority within SAGE.

## 1. Concept Overview
To prevent namespace conflicts, duplicate schema models, or parallel runtimes, CIR provides:
- **Centralized Register**: A strict register of all valid `object_type` values (e.g. `github_event`, `workspace_artifact`, `decision_entry`).
- **Schema Mapping**: Map of JSON-schema specifications for every object type.
- **Lineage Integrity**: Guarantees that all items in the Master Archive are referenceable using matching parent and child UUID lines.

## 2. Integrity Enforcement
Any attempt to promote a memory object that does not conform to the types registered in the CIR will fail the validation step, protecting the Master Archive from dirty data.
