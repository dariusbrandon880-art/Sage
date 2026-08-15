#!/usr/bin/env python3
"""SAGE Pre-Commit Governance Hook Script.

Scans active git staged/modified workspace changes against SAGE protected change boundaries
and cryptographically verifies EAS-001 attestation receipt chain integrity prior to commit.
Exits with code 0 on validation success, or code 1 on governance failure.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Resolve repo root reliably whether executed from scripts/ or .git/hooks/
try:
    repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
except Exception:
    repo_root = Path(__file__).resolve().parent.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Auto-re-exec under Poetry virtualenv if pydantic/sage dependencies are not in current python environment
try:
    import pydantic
except ImportError:
    poetry_bin = Path.home() / ".local/bin/poetry"
    python_bin = sys.executable
    if poetry_bin.exists():
        os.execv(str(poetry_bin), [str(poetry_bin), "run", "python", __file__] + sys.argv[1:])

from sage.experimental.act.context_guard import ProtectedChangeDetector
from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
from sage.acr.attestation import AttestationProvider
from sage.acr.eas_receipts import EASReceiptChain


def run_precommit_governance_check(
    workspace_path: Path = repo_root,
    eas_vault_path: Path = repo_root / "sage_data/flight_execution_proof/eas_vault/eas_receipts.json"
) -> bool:
    """Execute complete SAGE pre-commit governance validation.

    Returns:
        True if all governance and attestation checks pass cleanly, False otherwise.
    """
    print("======================================================================")
    print("            SAGE PRE-COMMIT GOVERNANCE HOOK - ACTIVE CHECK            ")
    print("======================================================================")

    # 1. Scan active git workspace changes
    orchestrator = DeveloperWorkflowOrchestrator(session_id="session_precommit_hook_check")
    workspace = orchestrator.scan_git_workspace()
    modified_files = workspace.get("modified_files", [])

    print(f"[*] Scanning {len(modified_files)} modified file(s)...")
    for f in modified_files:
        print(f"    - {f}")

    # 2. Audit protected core namespaces
    detector = ProtectedChangeDetector()
    protection_report = detector.audit_changes({"modified_files": modified_files})

    if protection_report.get("is_violation_found", False):
        print("\n[!] GOVERNANCE REJECTED: Protected core namespace mutation detected!")
        for violation in protection_report.get("violations", []):
            print(f"    - [{violation.get('severity', 'HIGH').upper()}] {violation.get('reason')}")
        return False

    print("[+] Workspace Scan: Safe (No unauthorized core namespace violations)")

    # 3. Verify EAS-001 attestation receipt chain integrity
    if eas_vault_path.exists():
        attestation = AttestationProvider(provider_type="TPM", key_seed="sage_attestation_seed_2026")
        chain = EASReceiptChain(storage_path=eas_vault_path, attestation=attestation)

        if not chain.verify_chain_integrity():
            print("\n[!] GOVERNANCE REJECTED: EAS-001 Attestation Receipt Chain Integrity Check Failed!")
            return False

        print(f"[+] Attestation Chain: Validated ({len(chain.receipts)} receipts intact)")
    else:
        print("[+] Attestation Chain: Vault not found (Bypassed in isolated environment)")

    print("----------------------------------------------------------------------")
    print("[+] PRE-COMMIT GOVERNANCE PASSED CLEANLY")
    print("======================================================================")
    return True


if __name__ == "__main__":
    success = run_precommit_governance_check()
    sys.exit(0 if success else 1)
