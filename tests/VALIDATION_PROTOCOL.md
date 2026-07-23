# SAGE VALIDATION LAB RECORDS & TESTING PROTOCOLS

## SAGE Validation Protocol v1.0

- **Purpose**: To provide an exhaustive, zero-trust validation framework designed to vigorously test and attempt to break SAGE's capabilities through evidence-based testing, ensuring high durability in production environments.

---

## 1. Zero Trust Validation Rules
SAGE assumes that any external system or connector payload is potentially corrupt, unverified, or adversarial.
- **Enforcement**:
  - Every payload must pass strict Pydantic parsing (`ExternalSessionPayload`).
  - Webhooks must pass cryptographically secure HMAC SHA256 signature verification.
  - Endpoints require global header-based `x-api-key` authentication if `SAGE_REQUIRE_AUTH` is active.

---

## 2. Intent Reconstruction Tests
Tests designed to verify that SAGE can successfully rehydrate complex project goals and tasks from standard state snapshots without loss of developmental focus or direction.
- **Verification**: Programmatic E2E tests (`test_handoff_and_restore_endpoints` and `test_workspace_snapshot_and_restore_continuity_intelligence`) verify that when SAGE is fully reset, it correctly re-establishes the identical objective, active task, and context tracker state from handoff files.

---

## 3. Dependency & Risk Mapping
A dynamic risk check to evaluate runtime safety and environment dependencies.
- **Verification**: `scripts/production_check.py` and `generate_diagnostic_report()` perform real-time checking of:
  - Python versions compatibility (3.10+)
  - Package installations (fastapi, pydantic, pydantic_settings)
  - Directory read/write access and permissions
  - Active and empty credentials JSON existence

---

## 4. Constitutional Review
Auditing that all codebase modifications and integrations strictly follow SAGE's master architecture governance (as defined in `docs/master/CONSTITUTION.md`):
- **Law Compliance Check**: Every proposed commit must be verified via Ruff and Black to ensure style formatting compliance, and undergo peer code reviews to ensure **Validation Before Expansion** is honored.

---

## 5. Evidence Lineage Requirements
No technical decision is accepted as valid within the SAGE runtime without satisfying bidirectional lineage links to supporting facts.
- **Lineage Verification**: Programmatic tests (`test_archive_intelligence_automatic_promotion`) confirm that promoted facts contain validation review histories (ValidationSystem), confidence coefficients, and associated decision histories.

---

## 6. Human Evaluation Scoring
Allows returning human builders or administrators to audit SAGE's current performance and status quickly.
- **Evaluation Gateway**: `generate_system_status_report()` generates a clean, plain-text layout score (SAGE Status checklist) summarizing active runtime state, components availability, capability loads, and validation readiness on demand.
