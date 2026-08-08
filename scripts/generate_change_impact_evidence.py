#!/usr/bin/env python3
"""SAGE-CIRA Ingestion and Concrete Evidence Generation Runner.

Loads existing validated capability passport definitions, invokes SAGE-CIRA
to analyze cascading change impact, and serializes the structured revalidation
evidence trace to the durable capture workspace.
"""

import os
import sys
import json
from pathlib import Path

# Resolve runtime import path for sage source tree
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sage.experimental.act.capability_passport import CapabilityPassport
from sage.experimental.change_impact import SAGEChangeImpactAnalyzer


def generate_cira_evidence():
    print("==================================================================")
    print("        SAGE-CIRA CONCRETE EVIDENCE GENERATION RUNNER             ")
    print("==================================================================\n")

    # Define capability passports mapping existing repository capabilities
    p_core = CapabilityPassport(
        name="CAP-COGNITIVE-KERNEL",
        purpose="Simulates prefrontal cortex safety gates and operator constraints.",
        lifecycle_state="VALIDATED",
        validation_strategy="tests/experimental/test_cognitive_kernel.py",
        evidence_path="evidence_capture/cognitive_kernel_foundation_report.json",
        archive_location="Main Archive/INDEX.md",
        allowed_next_state="CANONICAL"
    )

    p_pml = CapabilityPassport(
        name="CAP-PML-RELIABILITY",
        purpose="Hardens PersistentMissionLedger with cryptographic hash chains.",
        dependencies=["CAP-COGNITIVE-KERNEL"],
        lifecycle_state="VALIDATED",
        validation_strategy="tests/experimental/test_ccl_orchestrator.py",
        evidence_path="evidence_capture/ccl_orchestrator_evidence.json",
        archive_location="Main Archive/INDEX.md",
        allowed_next_state="CANONICAL"
    )

    p_ccl = CapabilityPassport(
        name="CAP-CONTINUITY-CONTROL-LOOP",
        purpose="Automatically captures AI workflow events into structured records.",
        dependencies=["CAP-PML-RELIABILITY"],
        lifecycle_state="VALIDATED",
        validation_strategy="tests/experimental/test_continuity_control.py",
        evidence_path="evidence_capture/ccl_operational_feedback.json",
        archive_location="Main Archive/INDEX.md",
        allowed_next_state="CANONICAL"
    )

    p_unaffected = CapabilityPassport(
        name="CAP-DEMO-LAUNCHER",
        purpose="Loads dry-run scenario execution vectors in-memory.",
        dependencies=[],
        lifecycle_state="VALIDATED",
        validation_strategy="tests/experimental/test_demo_launcher.py",
        evidence_path="evidence_capture/demo_launcher_evidence.json",
        archive_location="Main Archive/INDEX.md",
        allowed_next_state="CANONICAL"
    )

    passports = [p_core, p_pml, p_ccl, p_unaffected]
    analyzer = SAGEChangeImpactAnalyzer(passports)

    # Analyze change impact of CAP-COGNITIVE-KERNEL
    print("[*] Analyzing cascading revalidation impact of change to: CAP-COGNITIVE-KERNEL")
    report = analyzer.analyze_impact("CAP-COGNITIVE-KERNEL")

    output_file = Path("evidence_capture/change_impact_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[+] Successfully serialized new CIRA evidence report to: {output_file}")


if __name__ == "__main__":
    generate_cira_evidence()
