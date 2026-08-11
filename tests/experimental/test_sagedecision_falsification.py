"""Focused falsification test suite for SAGE-CRC-2.0 and SPEK Compliance Ledger."""

import json
from pathlib import Path
import pytest

from sage.core.compliance import ComplianceEngine
from sage.core.models import RuleState, SpekReceipt
from sage.core.attestation import CryptographicAttestationProvider


def test_spek_tamper_detection_falsification(tmp_path):
    """Real workload verifying that existing SPEK ComplianceEngine and AttestationProvider

    already possess mathematically non-repudiable and tamper-proof trace chaining,
    thus falsifying SAGE-CRC-2.0 as a necessary new primitive.
    """
    vault_file = tmp_path / "spek_vault.json"

    # 1. Initialize core cryptographic provider and compliance engine
    attestation = CryptographicAttestationProvider(provider_type="MOCK")
    compliance = ComplianceEngine(vault_path=str(vault_file))
    auth_token = "sage-default-key-2026"

    # 2. Append a clean, signed receipt
    hdg_trace = [{"node_id": "rule_root", "state": "VALIDATED"}]
    signing_payload = {
        "receipt_id": "rec_001",
        "proposal_id": "prop_001",
        "timestamp": "2026-08-11T12:00:00Z",
        "lifecycle_state": RuleState.VALIDATED.value,
        "execution_permission": True,
        "authority_integrity_score": 1.0,
        "hdg_trace": hdg_trace
    }
    sig = attestation.sign(signing_payload)

    compliance.append_receipt(
        receipt_id="rec_001",
        proposal_id="prop_001",
        state=RuleState.VALIDATED,
        execution_permission=True,
        authority_integrity_score=1.0,
        hdg_trace=hdg_trace,
        signature=sig,
        timestamp="2026-08-11T12:00:00Z",
        auth_token=auth_token
    )

    # 3. Verify original untampered vault integrity
    assert compliance.verify_vault_integrity(attestation) is True, "Original clean ledger must pass integrity check."

    # 4. Introduce an intentional bounded alteration (Tampering) on disk
    with open(vault_file, "r") as f:
        vault_data = json.load(f)

    # Modify the lifecycle state in the persisted receipt
    vault_data[0]["lifecycle_state"] = "APPROVED"

    with open(vault_file, "w") as f:
        json.dump(vault_data, f, indent=2)

    # 5. Reload and execute integrity check
    compromised_compliance = ComplianceEngine(vault_path=str(vault_file))

    # SAGE compliance engine must immediately detect the alteration and fail-closed (return False)
    assert compromised_compliance.verify_vault_integrity(attestation) is False, "Modified trace must fail integrity verification."
