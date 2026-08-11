#!/usr/bin/env python3
"""SAGE Cryptographic Preflight Tamper-Block Runner.

Demonstrates that the revalidation bridge successfully halts and blocks any
workload execution (failing closed at MISSION_PROPOSED) when on-disk ledger
tampering is detected inside the SPEK compliance ledger.
"""

import json
from pathlib import Path

from sage.core.compliance import ComplianceEngine
from sage.core.models import RuleState
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge


def main():
    print("[*] Launching SAGE Cryptographic Preflight Tamper-Block Runner...")

    vault_file = Path("evidence_capture/spek_vault_compromised.json")

    # 1. Create a simulated clean compliance ledger on disk
    compliance = ComplianceEngine(vault_path=str(vault_file))
    compliance.append_receipt(
        receipt_id="rec_001",
        proposal_id="prop_001",
        state=RuleState.VALIDATED,
        execution_permission=True,
        authority_integrity_score=1.0,
        hdg_trace=[],
        signature="mock_sig",
        timestamp="2026-08-11T12:00:00Z",
        auth_token="sage-default-key-2026"
    )

    # 2. Tamper with the ledger on disk to corrupt the signatures
    with open(vault_file, "r") as f:
        vault_data = json.load(f)
    vault_data[0]["attestation_signature"] = "corrupted_hacked_signature_999"
    with open(vault_file, "w") as f:
        json.dump(vault_data, f, indent=2)

    # 3. Instantiate the revalidation bridge pointing to the compromised ledger
    bridge = SAGEMissionExecutionBridge(vault_path=str(vault_file))

    # 4. Attempt execution of revalidation workload
    result = bridge.execute_revalidation_workload(
        mission_id="mission_cryptographic_preflight_fail",
        target_files=["sage/change_impact.py"],
        run_real_lint=False
    )

    print(f"[+] Final State reached: {result['final_state']}")
    print(f"[+] Tamper Block Active:  {result.get('cryptographic_tamper_detected', False)}")

    # Clean up temporary test file safely
    if vault_file.exists():
        vault_file.unlink()

    output_path = Path("evidence_capture/cryptographic_preflight_block_evidence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[+] Cryptographic preflight block evidence written to {output_path}")


if __name__ == "__main__":
    main()
