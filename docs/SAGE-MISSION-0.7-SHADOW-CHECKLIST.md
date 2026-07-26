# SAGE Mission 0.7: Shadow Observation Execution Checklist

**Record ID:** SAGE-EVID-007-CHECKLIST-0.7
**Classification:** Layer 3 Immutable Ledger / Production Operational Protocol
**Status:** PROPOSED (Awaiting Human Operator Sign-off)
**Configuration Target:** `SAGE_BOND_MODE="shadow"`

---

## 1. Executive Summary

This checklist establishes the definitive operational steps for executing the **Mission 0.7 Production Shadow Observation Phase**. Its purpose is to guide SAGE operators in verifying the performance and integrity of the SAGE Autonomous Continuity Runtime (ACR) during its non-blocking shadow evaluation window.

This protocol is purely observational. **Under no circumstances is active production enforcement to be enabled** without subsequent human authorization.

---

## 2. Shadow Observation Execution Checklist

- [ ] ### 2.1. Observation Start Conditions
  - [ ] **Env Variable Check:** Confirm that `SAGE_BOND_MODE` is strictly set to `"shadow"` in the production environment dashboard (Render / Server env config). Ensure it is *not* set to `"disabled"` or `"enforce"`.
  - [ ] **Staging Configuration Check:** Confirm that the staging environment `SAGE_BOND_MODE` is strictly set to `"enforce"` for comparison testing.
  - [ ] **Local State Integrity:** Verify that `git status` on the `main` branch is clean, with no untracked local modifications to core runtime code under `sage/`.
  - [ ] **Pre-Flight Health Verification:** Call `GET /health` and confirm that all core subsystems (`acr`, `archive`, `memory`, `configuration`) report as `"available"` with overall status `"healthy"`.
  - [ ] **Credentials Check:** Verify that google workspace credentials (`.sage/credentials.json`) are correctly positioned, or that dry-run/simulation fallback mode is verified functional.
  - [ ] **Nonce Ledger Baseline:** Confirm that `sage_data/nonces.json` exists and is initialized as an empty or active JSON list to prevent replay attacks.

- [ ] ### 2.2. Evidence Collection Verification Steps
  - [ ] **Hook Responsiveness Test:** Trigger a minor administrative update (e.g., calling `set_objective` via REST API or CLI).
  - [ ] **Evidence Directory Check:** Verify that a new JSON file named `evidence_trans_{transition_id}_{uuid}.json` was successfully written to `sage_data/evidence_capture/`.
  - [ ] **Receipt Content Audit:** Open the generated evidence file and verify that the `status` field equals `"VALIDATION_PASS"`, a non-empty `receipt_hash` is present, and the schema matches SAGE-EVID-003.
  - [ ] **Rejection Path Check:** Simulate an invalid state transition (such as passing an invalid `auth_token` or an out-of-order sequence target).
  - [ ] **Shadow Mode Bypass Verification:** Confirm that the failed validation logs a warning containing the exact `CIV-ERR-*` code to stdout, generates a corresponding `VALIDATION_FAIL` receipt in `sage_data/evidence_capture/`, and **does not raise a blocking exception**, allowing the transaction to proceed.

- [ ] ### 2.3. Daily Telemetry Review Procedure
  - [ ] **Operational Status Audit:** Query `GET /health` daily to check overall system state and component availability.
  - [ ] **Cognitive Control plane Telemetry Inspection:** Query `GET /runtime/control-plane` to extract:
    - `approved_mutations`: Confirm that this value increments with successful actions.
    - `rejected_mutations`: Confirm that shadow rejections are correctly captured.
    - `authority_stability_index` (ASI): Recalculate daily. Confirm that ASI remains within the warning threshold ($\ge 0.95$).
    - `cognitive_separation_index` (CSI): Ensure CSI remains exactly `1.0`. Any drop below `1.0` indicates an immediate policy violation.
  - [ ] **Divergence and Drift Audit:** Review the `drift_detection` section in `/health` daily to identify any active objectives or tasks that diverge from the latest checkpoints.

- [ ] ### 2.4. CIV Event Classification Review
  - [ ] **Shadow Rejection Logging:** If a shadow rejection occurs, locate the generated receipt inside `sage_data/evidence_capture/` and classify the failure:
    - [ ] **`CIV-ERR-MUT-003`:** Check if the transition author is unregistered or if the transition bypassed standard STP sequence milestones.
    - [ ] **`CIV-ERR-AUTH-001`:** Verify whether the security token or custom rules signature failed validation.
    - [ ] **`CIV-ERR-SCHM-002`:** Audit the structural fields to identify raw dict or Pydantic type violations.
    - [ ] **`CIV-ERR-SCHM-005`:** Scan for missing required fields or causality circular loops.
    - [ ] **`CIV-ERR-EXT-004`:** Check if the confidence score fell below `evidence_threshold` (default `0.7`).
  - [ ] **Rejection Analysis:** Cross-reference every shadow failure against the developer execution log to determine if the failure represents a true security violation or a false positive.

- [ ] ### 2.5. Receipt Integrity Checks
  - [ ] **Receipt Chain Auditing:** Run `GET /runtime/control-plane` and confirm that `receipt_chain.integrity_valid` is strictly `True` (or `1.0`).
  - [ ] **Chronological Linkage Check:** Verify that every transaction entry in `spek_vault.json` successfully points to its ancestor block hash (`parent_hash` matching the previous signature).
  - [ ] **Signature Cryptographic Verification:** Re-run HMAC-SHA256 signature verification over the append-only `spek_vault.json` receipts to detect tampering.
  - [ ] **Discrepancy Remediation:** If any block linkage or signature mismatch is detected, immediately lock archive promotions, generate an isolated state checkpoint, and notify the Human Operator.

- [ ] ### 2.6. End-of-Window Audit Requirements
  - [ ] **14-Day Baseline Compile:** After 14 consecutive days of shadow operations, extract and compile all receipts inside `sage_data/evidence_capture/`.
  - [ ] **Volumetric Validation:** Ensure that at least 500 state transitions have been successfully captured and evaluated.
  - [ ] **ASI Stability Confirm:** Verify that the dynamic ASI remained $\ge 0.99$ over the final 100 consecutive transitions.
  - [ ] **False-Positive Assessment:** Verify that the overall false-positive rate across all classifications remains $< 0.5\%$.
  - [ ] **Staging Regression Audit:** Confirm that the staging environment operating in `"enforce"` mode has passed all integration and stress tests with 100% stability.
  - [ ] **Promotion Report Submission:** Generate the final Mission 0.7 Shadow Observation Report, sign it cryptographically, and submit it to the Human Operator for final promotion sign-off.

---

### Certification of Checklist Authority

By checking in this execution checklist, SAGE locks the operational guidelines for the Mission 0.7 observation process.

**Authored By:** Jules (SAGE Engineering Node)
**Reviewed By:** Claude (Adversarial Policy Node)
**Governance Approval:** `PENDING_HUMAN_SIGNATURE`
