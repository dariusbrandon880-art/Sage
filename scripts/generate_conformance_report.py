#!/usr/bin/env python3
"""CLI Script to generate a structured SAGE Governance Conformance Assessment report."""

import os
import sys
import json
from pathlib import Path

# Resolve project root dynamically to allow direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.experimental.governance_conformance import GovernanceConformanceAssessor


def main():
    print("==================================================================")
    print("      SAGE GOVERNANCE CONFORMANCE ASSESSMENT GENERATOR            ")
    print("==================================================================\n")

    base_dir = Path("evidence_capture")
    evidence_path = base_dir / "phase_4_controlled_evaluation_evidence.json"

    if not evidence_path.exists():
        print(f"[-] Error: Target evidence file {evidence_path} not found.")
        sys.exit(1)

    print(f"[+] Loading target evidence: {evidence_path}")
    with open(evidence_path, "r", encoding="utf-8") as f:
        evidence_data = json.load(f)

    # Instantiate Assessor
    assessor = GovernanceConformanceAssessor()
    out_path = assessor.assess_and_save_report(
        capability_id="CAP-PHASE-4-EVAL",
        run_id=evidence_data.get("run_identifier") or "run_phase4_eval",
        evidence_data=evidence_data,
        output_dir=str(base_dir),
        output_name="governance_conformance_assessment.json"
    )

    # Print high-fidelity diagnostic output
    with open(out_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"\n[+] Conformance Assessment completed successfully!")
    print(f"    - Capability:            {report['capability_id']}")
    print(f"    - Source Run ID:         {report['run_id']}")
    print(f"    - Overall Conformance:   {report['overall_conformance']}")
    print(f"    - Requirements Assessed:")
    for req_name, req in report["requirements"].items():
        print(f"      * {req_name}: [{req['assessment_status']}]")
        print(f"        Expected: {req['expected_invariant']}")
        print(f"        Observed: {req['observed_evidence']}\n")


if __name__ == "__main__":
    main()
