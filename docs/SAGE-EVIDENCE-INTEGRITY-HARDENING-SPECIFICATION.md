# SAGE EVIDENCE INTEGRITY HARDENING SPECIFICATION

## 1. Purpose & Scope
The **SAGE Evidence Integrity Hardening** capability is an experimental, non-mutating validation tool designed to audit, hash, and verify the immutable state of SAGE's evidence package artifacts. It ensures that trace captures cannot be modified, replayed, or deleted unnoticed. It runs strictly under the **Experimental Layer**, with zero access or imports to active core production processes.

---

## 2. Audited Evidence Artifacts & Schema Mappings
The verifier monitors five designated experimental evidence files:

| Artifact Path | Expected Key Fields | Purpose |
|---|---|---|
| `evidence_capture/sdr_crc_evidence_package.json` | `experiment_id`, `blocks`, `verification` | Traces SAGE-CRC block verification. |
| `evidence_capture/sdr_gal_evidence_package.json` | `gal_run_id`, `changed_files`, `boundary_status`, `test_results` | Traces SAGE-GAL automated pipeline results. |
| `evidence_capture/sdr_exp_001_evidence_package.json` | `experiment_id`, `blocks`, `human_review_status` | Traces SDR-001 experimental results. |
| `evidence_capture/sdr_exp_002_evidence_package.json` | `experiment_id`, `handoff_sequence`, `verification_results` | Traces SDR-002 sequential agent transitions. |
| `evidence_capture/multi_agent_handoff_envelope.json` | `sender_id`, `receiver_id`, `capability_id` | Traces initial mock multi-agent handoff. |

---

## 3. Cryptographic Validation Protocol
The verifier enforces three primary checks on each monitored artifact:

1. **Existence Verification:** Detects if any audited file has been moved, renamed, or deleted. Missing files are flagged as `"MISSING"`.
2. **SHA-256 Checksum Matching:** Computes the current physical SHA-256 hash of each file and compares it to a registered baseline to detect tampering.
3. **Internal Schema Auditing:** Parses each JSON artifact to confirm all required schema attributes are fully populated, valid, and contain expected human review and validation states.

---

## 4. Fail-Closed Verification Behavior
If any audited file is found to have a mismatched hash, modified schema attributes, or unauthorized state changes, the verifier fails-closed immediately:
* Throws a descriptive `ValueError` during active verification processes.
* Aborts further trace continuity recovery or rehydration pipelines.
* Recommends `"FAILED"` readiness status in final compiled reports.
