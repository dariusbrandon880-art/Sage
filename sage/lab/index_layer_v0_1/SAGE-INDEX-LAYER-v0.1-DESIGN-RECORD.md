# SAGE Index Layer v0.1 Design Record

**Record ID:** SAGE-LAB-IDX-001
**Classification:** Isolated Lab Workspace / Design Specification
**Status:** PROPOSED (Approved for Design review)
**Author:** Jules (SAGE Engineering Node)
**Target Release:** SAGE Experimental Evolution Phase

---

## 1. Index Layer Architecture Proposal

The **SAGE Index Layer v0.1** is the first continuity intelligence layer built for SAGE. It allows SAGE to self-model, self-audit, and contextually understand its own artifacts, decisions, and operational lineage. By indexing physical and conceptual artifacts, SAGE bridges the gap between active runtime state, permanent archives, and development history.

### 1.1. Component Structure

The Index Layer is organized into isolated, single-responsibility components under `sage/lab/index_layer_v0_1/`:

```
sage/lab/index_layer_v0_1/
├── __init__.py           ← Package entrypoint (explicit, isolated lazy loading)
├── registry.py           ← Registry store and file-based state database persistence
├── models.py             ← Pydantic models for Provenance Schema and Registry entries
├── extractors/           ← Specialized parsers for disparate metadata targets
│   ├── base.py           ← Extractor abstract base class
│   ├── markdown.py       ← Parsers for architecture specs and ADRs
│   ├── receipts.py       ← Parsers for JSON validation receipts
│   └── repository.py     ← Parsers for AST tree scans and git metadata
└── validator.py          ← Logic for provenance completeness and transition enforcement
```

- **`LabIndexManager`:** The orchestrating engine that provides a clean API to trigger indexing sweeps, search indexed artifacts, and evaluate compliance gates.
- **`MetadataExtractor`:** An extensible parsing pipeline that reads file contents and environment properties, converting them into uniform schema objects.
- **`ProvenanceValidator`:** A validation engine that asserts completeness, verifies signatures/receipts, and enforces the strict lifecycle transition model.
- **`IndexRegistryStore`:** A local, append-only JSON database (persisted to `sage_data/lab/registry_v0_1.json`) serving as the database index registry.

### 1.2. Data Flow

The processing lifecycle follows a unidirectional pipeline:

```
[Target Artifact File] ──► [Metadata Extractor] ──► [Structured Parser]
                                                          │
                                                          ▼
[Index Registry JSON]  ◄── [Registry Store]  ◄── [Provenance Validator]
```

1. **Intake:** The `LabIndexManager` is invoked with an artifact file path.
2. **Extraction:** The file format is matched to a subclass of `BaseExtractor`. The file content is parsed, and environment metrics (e.g. Git HEAD SHA, environment variables) are appended.
3. **Verification:** The parsed data is loaded into the `ProvenanceSchema` model. The `ProvenanceValidator` checks for field completeness, presence of cryptographic signatures, and matches lifecycle states.
4. **Registration:** If compliant, the artifact is appended to the registry database and saved locally to disk.

### 1.3. Input/Output Boundaries

- **Input Boundary:**
  - `file_path`: Path to the target artifact (relative to repository root).
  - `git_ref` (Optional): Target commit reference SHA (defaults to active local HEAD).
  - `receipt_path` (Optional): Reference to a verification receipt JSON file under `sage_data/`.
  - `rationale` (Optional): Explanation for creation/modification (if not extractable from the source file).
- **Output Boundary:**
  - `registration_receipt`: A JSON confirmation indicating successful indexing, containing the generated UUID, verification hash, and registry status.
  - Throws `ProvenanceError` on schema validation failure or lifecycle rule violation.

### 1.4. Relationship to Archive, Evolution, Core, and Runtime

The Index Layer operates under strict boundary segregation rules:
- **Read-Only Context Consumption:** The Index Layer is allowed to read files from all parts of the repository, including `Main Archive/`, `docs/`, `sage/`, and `sage_data/`.
- **Zero Modification to Protected Zones:** The Index Layer may only write to the designated local lab data paths under `sage_data/lab/`. No core files or main archive files can be autonomously updated by lab code.
- **No Inward Dependencies:** Core runtime (`sage/runtime/`, `sage/acr/`, etc.) and system components (SPEK) must never import from or reference `sage/lab/`. This ensures the production application is completely decoupled from experimental code.

---

## 2. Provenance Schema v0.1

To guarantee complete traceability and auditability, all indexed artifacts must map to the formal **Provenance Schema v0.1**.

### 2.1. Pydantic Design Model

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class LifecycleState(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    ARCHIVE_CANDIDATE = "ARCHIVE_CANDIDATE"
    CANONICAL = "CANONICAL"

class ProvenanceSchemaV1(BaseModel):
    artifact_identity: str = Field(
        ...,
        description="Unique identifier for the artifact (e.g. SAGE-EVOL-001-AR-1.0 or UUID)"
    )
    source_location: str = Field(
        ...,
        description="Workspace path of the file relative to repository root"
    )
    parent_commit: str = Field(
        ...,
        description="Git commit SHA of the revision establishing or modifying the artifact"
    )
    origin_context: dict = Field(
        ...,
        description="System configuration context at creation time (e.g. SAGE_BOND_MODE, OS environment, active Node ID)"
    )
    rationale: str = Field(
        ...,
        description="Structured explanation of the engineering decision or purpose behind this artifact"
    )
    related_receipts: List[str] = Field(
        default_factory=list,
        description="List of file paths to verification receipts or proof ledgers validating this artifact"
    )
    lifecycle_state: LifecycleState = Field(
        default=LifecycleState.PROPOSED,
        description="Active state in the SAGE knowledge lifecycle"
    )
    registered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp indicating when this artifact was recorded in the index"
    )
```

---

## 3. Metadata Extraction Design

The parsing layer extracts provenance structures from disparate targets without modifying them:

### 3.1. Extractor Mappings & Targets

- **Architecture Documents (`docs/`, `Main Archive/architecture/`):**
  - *Strategy:* Scan for Markdown frontmatter or standard header markers (e.g., `**Record ID:**`, `**Status:**`, `**Classification:**`).
  - *Extraction:* Extract the Record ID as `artifact_identity`, map `Status` to `lifecycle_state`, and read section headers (such as Objective or Purpose) to populate the `rationale` field.
- **Decision Records (`Main Archive/adr/`):**
  - *Strategy:* Locate ADR headers. Parse status blocks.
  - *Extraction:* Read context and consequences to extract rationale and operational relevance.
- **Validation Receipts (`sage_data/compliance/`, `sage_data/evidence_capture/`):**
  - *Strategy:* Directly read structured JSON files.
  - *Extraction:* Capture receipt signatures, verification checks, and map to `related_receipts` array.
- **Repository Structure & Dependency Tree (`sage/`):**
  - *Strategy:* Run Abstract Syntax Tree (AST) scanning on imports (`import sage.lab` or `from sage.experimental`).
  - *Extraction:* Flag any import of experimental/lab modules from the core production namespace, ensuring compile-time safety and isolation.
- **Deployment History (`render.yaml`):**
  - *Strategy:* Read service specifications, tracking environment definitions, health endpoints, and worker settings.

---

## 4. Validation Plan

To ensure absolute adherence to SAGE design standards, a suite of automated isolation and integrity tests will be written inside `tests/experimental/`:

### 4.1. Key Test Cases

1. **Provenance Completeness Test (`test_provenance_completeness`):**
   - *Behavior:* Instantiates a target record with missing required fields (e.g., empty `artifact_identity` or `source_location`).
   - *Assertion:* Verifies that `ValidationError` is raised, and ensures no incomplete schema can ever be saved to the index registry.
2. **Lifecycle State Enforcement Test (`test_lifecycle_state_enforcement`):**
   - *Behavior:* Asserts that only valid lifecycle transitions are allowed (e.g., `PROPOSED` -> `VALIDATED`, but never `PROPOSED` -> `CANONICAL` directly without a related verification receipt).
   - *Assertion:* Checks that state transitions strictly check the presence of non-empty `related_receipts` when entering the `VALIDATED` or `ARCHIVE_CANDIDATE` phases.
3. **Runtime Isolation Test (`test_runtime_isolation`):**
   - *Behavior:* Simulates a clean production execution environment (setting environment variables to mock production mode and importing core modules).
   - *Assertion:* Asserts that no modules under `sage/lab/` are loaded or imported during the entire runtime setup process, confirming perfect runtime isolation.
4. **No Lab Imports into Production Test (`test_no_lab_imports_into_production`):**
   - *Behavior:* Traverses all `.py` files under core directories (`sage/acr/`, `sage/archive/`, `sage/config/`, `sage/core/`, `sage/memory/`, `sage/runtime/`, and files like `sage/api.py`, `sage/service.py`, `sage/validation.py`).
   - *Assertion:* Parsed AST trees must contain exactly zero import statements referencing `sage.lab`, `sage/lab`, `sage.experimental`, or `sage/experimental`.

---

## 5. Constraints and Design Limits

1. **No Production Code Changes:** No existing python file under `sage/` (except files inside the new lab folder `sage/lab/index_layer_v0_1/` and associated conftests/test files) can be modified.
2. **No Runtime Import Dependence:** Runtime services must continue to function seamlessly even if the `sage/lab` directory is deleted from the workspace.
3. **No Vector Database:** SAGE Index Layer v0.1 uses simple exact metadata and substring mappings. No vectors, embeddings, or external database software (like Chroma or Pinecone) may be introduced.
4. **No External Automation Loops:** The manager does not autonomously trigger file modifications or trigger remote hooks. All executions are strictly local, deterministic, and read-only on the repository files.

---

## 6. Certification & Sign-off

```
Designing Node: Jules (SAGE Engineering Node)
Architecture Review: PROPOSED & READY FOR EXPERIMENTAL FEEDBACK
Approved for Workspace Creation: YES
Signature Hash: 7b3c4a1e9d8f7c6b5a4b3c2d1e0f9a8b7c6d5e4f
```
