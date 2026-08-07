"""Unit tests for the SAGE Governance Conformance Assessment framework."""

import json
from pathlib import Path
from sage.experimental.act.governance_conformance import (
    GovernanceConformanceAssessor,
    GovernanceConformanceAssessmentReport,
    ConformanceRequirement
)


def test_conformance_fully_conformant():
    """Verify that a fully compliant evidence package returns CONFORMANT on all dimensions."""
    evidence = {
        "boundary_integrity_verification": {
            "sage_runtime_untouched": True,
            "sage_core_untouched": True,
            "sage_acr_untouched": True,
            "sage_agents_untouched": True
        },
        "authentication_result": "BLOCKED_MISSING_CREDENTIALS",
        "artifact_hashes": {
            "sage/experimental/act/contracts.py": "abc123hash"
        },
        "agent_id": "executor_jules",
        "human_checkpoint": {
            "supervisor_id": "supervisor_darius",
            "signature": "sig_authorized_001",
            "decision": "AUTHORIZED"
        }
    }

    assessor = GovernanceConformanceAssessor()
    report = assessor.assess_conformance("CAP-DEPLOYMENT-RUN", "run_test_01", evidence)

    assert report.overall_conformance == "CONFORMANT"

    # Check dimensions
    assert report.requirements["protected-boundary-preservation"].assessment_status == "CONFORMANT"
    assert report.requirements["non-execution-requirements"].assessment_status == "CONFORMANT"
    assert report.requirements["evidence-provenance-integrity"].assessment_status == "CONFORMANT"
    assert report.requirements["authorization-separation"].assessment_status == "CONFORMANT"
    assert report.requirements["archive-promotion-separation"].assessment_status == "CONFORMANT"


def test_conformance_protected_boundary_violation():
    """Verify that a core namespace protection violation causes NON_CONFORMANT status."""
    evidence = {
        "protection_evaluation": {
            "status": "PROTECTION_VIOLATION_DETECTED",
            "violations": [
                {"file_path": "sage/core/spek.py", "reason": "Unauthorized modification"}
            ]
        },
        "decision_record": {
            "decision_state": "APPROVED"  # Violation was approved (illegal bypass!)
        }
    }

    assessor = GovernanceConformanceAssessor()
    report = assessor.assess_conformance("CAP-DEPLOYMENT-RUN", "run_test_01", evidence)

    assert report.requirements["protected-boundary-preservation"].assessment_status == "NON_CONFORMANT"
    assert report.overall_conformance == "NON_CONFORMANT"


def test_conformance_missing_evidence_and_not_applicable():
    """Verify that missing metadata causes INSUFFICIENT_EVIDENCE, while unrelated checks return NOT_APPLICABLE."""
    evidence = {
        # No boundary integrity or protection evaluation (Insufficient Evidence)
        # No artifact hashes or receipt lineages (Insufficient Evidence)
        # No model execution fields (Not Applicable)
    }

    assessor = GovernanceConformanceAssessor()
    report = assessor.assess_conformance("CAP-DEPLOYMENT-RUN", "run_test_01", evidence)

    assert report.overall_conformance == "INSUFFICIENT_EVIDENCE"
    assert report.requirements["protected-boundary-preservation"].assessment_status == "INSUFFICIENT_EVIDENCE"
    assert report.requirements["non-execution-requirements"].assessment_status == "NOT_APPLICABLE"


def test_conformance_authorization_separation_violation():
    """Verify that separation of duties is violated (NON_CONFORMANT) if agent_id matches supervisor_id."""
    evidence = {
        "agent_id": "supervisor_jules",
        "human_checkpoint": {
            "supervisor_id": "supervisor_jules",  # Self-approval!
            "signature": "sig_self_approved",
            "decision": "AUTHORIZED"
        }
    }

    assessor = GovernanceConformanceAssessor()
    report = assessor.assess_conformance("CAP-DEPLOYMENT-RUN", "run_test_01", evidence)

    assert report.requirements["authorization-separation"].assessment_status == "NON_CONFORMANT"
    assert report.overall_conformance == "NON_CONFORMANT"


def test_conformance_no_mutation_and_provenance(tmp_path):
    """Verify that assessor never mutates incoming data, and preserves provenance and saves accurately."""
    evidence = {
        "boundary_integrity_verification": {
            "sage_runtime_untouched": True
        },
        "artifact_hashes": {
            "sage/experimental/act/contracts.py": "abc123hash"
        }
    }
    evidence_copy = json.loads(json.dumps(evidence))

    assessor = GovernanceConformanceAssessor()
    report_path = assessor.assess_and_save_report(
        "CAP-EVAL", "run_test_01", evidence, output_dir=str(tmp_path), output_name="conformance_test.json"
    )

    # Check original dict was not mutated
    assert evidence == evidence_copy

    # Check saved report
    saved_file = Path(report_path)
    assert saved_file.exists()

    with open(saved_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["capability_id"] == "CAP-EVAL"
    assert data["run_id"] == "run_test_01"
    assert "protected-boundary-preservation" in data["requirements"]
    assert data["requirements"]["protected-boundary-preservation"]["supporting_provenance"]["boundary_integrity_verification"]["sage_runtime_untouched"] is True
