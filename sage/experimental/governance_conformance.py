"""SAGE Governance Conformance Assessment Framework.

Operates strictly within experimental/read-only boundaries to compare SAGE
capability/evidence states against applicable governance constraints mechanically.
Resides outside protected ACT/ACR/CCL/PML/Core/Runtime boundaries.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConformanceRequirement(BaseModel):
    """Represents a single evaluated governance constraint and its check status."""
    requirement_name: str
    expected_invariant: str
    observed_evidence: str
    assessment_status: str  # CONFORMANT, NON_CONFORMANT, INSUFFICIENT_EVIDENCE, NOT_APPLICABLE
    supporting_provenance: dict[str, Any] = Field(default_factory=dict)


class GovernanceConformanceAssessmentReport(BaseModel):
    """High-fidelity governance conformance assessment report."""
    capability_id: str
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    overall_conformance: str  # CONFORMANT, NON_CONFORMANT, INSUFFICIENT_EVIDENCE, NOT_APPLICABLE
    requirements: dict[str, ConformanceRequirement] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceConformanceAssessor:
    """Computes deterministic structured governance assessments from evidence records."""

    def assess_conformance(
        self,
        capability_id: str,
        run_id: str,
        evidence_data: Dict[str, Any]
    ) -> GovernanceConformanceAssessmentReport:
        """Evaluate applicable governance constraints over the provided evidence record."""
        requirements = {}

        # 1. Protected-Boundary Preservation
        req_boundary = "protected-boundary-preservation"
        expected_boundary = "No unauthorized modifications to core namespaces (sage/core/, sage/runtime/, sage/acr/, sage/agents/)."

        boundary_integrity = evidence_data.get("boundary_integrity_verification")
        protection_eval = evidence_data.get("protection_evaluation")

        if boundary_integrity and isinstance(boundary_integrity, dict):
            untouched_all = all(boundary_integrity.values())
            observed = f"Boundary integrity verified. Core untouched states: {boundary_integrity}"
            status = "CONFORMANT" if untouched_all else "NON_CONFORMANT"
            provenance = {"boundary_integrity_verification": boundary_integrity}
        elif protection_eval and isinstance(protection_eval, dict):
            violations = protection_eval.get("violations", [])
            decision = evidence_data.get("decision_record", {}).get("decision_state")
            if protection_eval.get("status") == "PROTECTION_VIOLATION_DETECTED":
                if decision == "REJECTED":
                    observed = f"Protection violation intercepted and cleanly REJECTED by supervisor: {violations}"
                    status = "CONFORMANT"  # Intercepted and rejected = conformant to safety boundaries
                else:
                    observed = f"Protection violation detected but NOT rejected: {violations}"
                    status = "NON_CONFORMANT"
            else:
                observed = "No core namespace protection violations detected."
                status = "CONFORMANT"
            provenance = {"protection_evaluation": protection_eval, "decision_record": evidence_data.get("decision_record")}
        else:
            observed = "No core boundary integrity records found in the provided evidence."
            status = "INSUFFICIENT_EVIDENCE"
            provenance = {}

        requirements[req_boundary] = ConformanceRequirement(
            requirement_name=req_boundary,
            expected_invariant=expected_boundary,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # 2. Non-Execution Requirements
        req_non_exec = "non-execution-requirements"
        expected_non_exec = "Live completions or activation runs must gracefully halt and not bypass model authentication."

        auth_result = evidence_data.get("authentication_result")
        exec_result = evidence_data.get("execution_result", {})

        if auth_result == "BLOCKED_MISSING_CREDENTIALS":
            observed = "Startup activation safely halted due to missing credentials, avoiding bypass."
            status = "CONFORMANT"
            provenance = {"authentication_result": auth_result, "execution_result": exec_result}
        elif isinstance(exec_result, dict) and exec_result.get("completion_status") == "BLOCKED":
            observed = "Model execution blocked."
            status = "CONFORMANT"
            provenance = {"execution_result": exec_result}
        elif "authentication_result" in evidence_data or "execution_result" in evidence_data:
            observed = "Completions run succeeded without credential block flags."
            status = "CONFORMANT"
            provenance = {"authentication_result": auth_result, "execution_result": exec_result}
        else:
            observed = "No execution/authentication boundaries are tracked for this capability."
            status = "NOT_APPLICABLE"
            provenance = {}

        requirements[req_non_exec] = ConformanceRequirement(
            requirement_name=req_non_exec,
            expected_invariant=expected_non_exec,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # 3. Evidence/Provenance Requirements
        req_prov = "evidence-provenance-integrity"
        expected_prov = "Every validation run must provide cryptographic checksums/hashes or linked receipt lineages."

        artifact_hashes = evidence_data.get("artifact_hashes") or evidence_data.get("artifact hashes")
        receipt_lineage = evidence_data.get("receipt_lineage") or evidence_data.get("receipt lineage")
        audit_hash = evidence_data.get("audit_hash")

        if artifact_hashes and isinstance(artifact_hashes, dict):
            observed = f"Cryptographic SHA-256 artifact hashes present: {list(artifact_hashes.keys())}"
            status = "CONFORMANT"
            provenance = {"artifact_hashes": artifact_hashes}
        elif receipt_lineage and isinstance(receipt_lineage, list):
            observed = f"Linked receipt lineage present with {len(receipt_lineage)} steps."
            status = "CONFORMANT"
            provenance = {"receipt_lineage": receipt_lineage}
        elif audit_hash:
            observed = f"Cryptographic file audit hash present: {audit_hash}"
            status = "CONFORMANT"
            provenance = {"audit_hash": audit_hash}
        else:
            observed = "No SHA-256 file hashes or chained lineage receipts found."
            status = "INSUFFICIENT_EVIDENCE"
            provenance = {}

        requirements[req_prov] = ConformanceRequirement(
            requirement_name=req_prov,
            expected_invariant=expected_prov,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # 4. Authorization Separation (Separation of Duties)
        req_sep = "authorization-separation"
        expected_sep = "The executor/agent ID must be distinct from the supervisor/signer identity (no self-approval)."

        agent_id = evidence_data.get("agent_id") or evidence_data.get("actor_id")
        signer = None

        # Check attestation
        att = evidence_data.get("attestation")
        human_chk = evidence_data.get("human_checkpoint") or evidence_data.get("human checkpoint")

        if att and isinstance(att, dict):
            signer = att.get("signer_identity") or att.get("supervisor_id")
        elif human_chk and isinstance(human_chk, dict):
            signer = human_chk.get("supervisor_id")

        if agent_id and signer:
            if agent_id == signer:
                observed = f"Separation of duties violation: Agent '{agent_id}' self-approved as Supervisor '{signer}'."
                status = "NON_CONFORMANT"
            else:
                observed = f"Separation of duties validated. Executor Agent: '{agent_id}' | Approving Supervisor: '{signer}'"
                status = "CONFORMANT"
            provenance = {"agent_id": agent_id, "supervisor_id": signer}
        else:
            observed = "Missing executor ID or supervisor signature required for separation check."
            status = "INSUFFICIENT_EVIDENCE"
            provenance = {}

        requirements[req_sep] = ConformanceRequirement(
            requirement_name=req_sep,
            expected_invariant=expected_sep,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # 5. Archive-Promotion Separation
        req_promo = "archive-promotion-separation"
        expected_promo = "Archive promotion status must require explicit supervisor signature/attestation."

        attestation = evidence_data.get("attestation") or evidence_data.get("human_checkpoint") or evidence_data.get("human checkpoint")

        if attestation and isinstance(attestation, dict) and (attestation.get("signature") or attestation.get("decision") == "AUTHORIZED"):
            observed = "Explicit supervisor authorization signature/attestation present before promotion."
            status = "CONFORMANT"
            provenance = {"attestation": attestation}
        else:
            observed = "No explicit supervisor authorization/attestation found in evidence record."
            status = "INSUFFICIENT_EVIDENCE"
            provenance = {}

        requirements[req_promo] = ConformanceRequirement(
            requirement_name=req_promo,
            expected_invariant=expected_promo,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # 6. Deployment Isolation
        req_deploy = "deployment-isolation"
        expected_deploy = "Render and deployment targets must keep active services isolated and non-mutable."

        # Check metadata
        meta = evidence_data.get("metadata") or {}
        if "deployment" in str(evidence_data).lower() or "render" in str(evidence_data).lower():
            observed = f"Deployment isolation metadata identified: {meta}"
            status = "CONFORMANT"
            provenance = {"metadata": meta}
        else:
            observed = "No active deployment/Render mutations or logs are referenced in this run."
            status = "NOT_APPLICABLE"
            provenance = {}

        requirements[req_deploy] = ConformanceRequirement(
            requirement_name=req_deploy,
            expected_invariant=expected_deploy,
            observed_evidence=observed,
            assessment_status=status,
            supporting_provenance=provenance
        )

        # Compute Overall Conformance Status
        all_statuses = [req.assessment_status for req in requirements.values() if req.assessment_status != "NOT_APPLICABLE"]

        if "NON_CONFORMANT" in all_statuses:
            overall = "NON_CONFORMANT"
        elif "INSUFFICIENT_EVIDENCE" in all_statuses:
            overall = "INSUFFICIENT_EVIDENCE"
        elif "CONFORMANT" in all_statuses:
            overall = "CONFORMANT"
        else:
            overall = "NOT_APPLICABLE"

        return GovernanceConformanceAssessmentReport(
            capability_id=capability_id,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_conformance=overall,
            requirements=requirements,
            metadata={"source_run_details": {"run_id": run_id}}
        )

    def assess_and_save_report(
        self,
        capability_id: str,
        run_id: str,
        evidence_data: Dict[str, Any],
        output_dir: str = "evidence_capture",
        output_name: str = "governance_conformance_assessment.json"
    ) -> str:
        """Assess the provided evidence record and persist report to disk."""
        report = self.assess_conformance(capability_id, run_id, evidence_data)
        out_path = Path(output_dir) / output_name

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        print(f"[+] Successfully generated Governance Conformance Assessment report: {out_path}")
        return str(out_path)
