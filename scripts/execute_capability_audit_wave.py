#!/usr/bin/env python3
"""Runner script executing SAGE C2 Capability Audit Wave and persisting evidence."""

import json
import subprocess
import sys
from pathlib import Path

from sage.c2.capability_audit_bridge import C2CapabilityAuditBridge


def get_git_head() -> str:
    """Returns exact 40-character commit SHA for active HEAD."""
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def main() -> int:
    exact_head = get_git_head()
    print(f"[+] Active Git Commit HEAD: {exact_head}")

    bridge = C2CapabilityAuditBridge()

    wave_id = "capability_audit_wave_001"
    print(f"[+] Executing C2 Capability Audit Wave: {wave_id}")

    receipt = bridge.audit_capabilities(exact_git_head=exact_head, wave_id=wave_id)

    print(f"[+] Receipt Hash: {receipt.receipt_hash}")
    print(f"[+] Total Capabilities Audited: {receipt.total_capabilities_audited}")
    print(f"[+] Verified Count: {receipt.verified_count}")
    print(f"[+] Drift Count: {receipt.drift_count}")
    print(f"[+] Audit Verdict: {receipt.audit_verdict}")

    if receipt.audit_verdict != "PASS":
        print("[!] ERROR: Capability Audit Wave failed with drift detected!", file=sys.stderr)
        return 1

    evidence_path = Path("evidence_capture/capability_audit_wave_evidence.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(receipt.model_dump(), f, indent=2)

    print(f"[+] Successfully persisted evidence receipt to {evidence_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
