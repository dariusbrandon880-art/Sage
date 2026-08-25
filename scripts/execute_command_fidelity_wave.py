#!/usr/bin/env python3
"""Execute the five-flight Command Fidelity wave and persist structured evidence.

A live PASS requires an externally produced SourceReceipt supplied through
SAGE_OPERATION_RECEIPT_JSON. The runner never manufactures live-operation proof.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher
from sage.c2.reality_gate import SourceReceipt


def _load_operation_receipt():
    raw = os.environ.get("SAGE_OPERATION_RECEIPT_JSON")
    if not raw:
        return None
    payload = json.loads(raw)
    return SourceReceipt(
        source_type=payload["source_type"],
        resource_id=payload["resource_id"],
        sha256_digest=payload["sha256_digest"],
        timestamp_utc=float(payload["timestamp_utc"]),
        metadata=dict(payload.get("metadata", {})),
    )


def main():
    operation_receipt = _load_operation_receipt()
    dispatcher = CommandFidelityWaveDispatcher()
    receipt = dispatcher.dispatch_wave(operation_receipt=operation_receipt)

    out_dir = Path("evidence_capture")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "command_fidelity_wave_evidence.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    evidence_valid = CommandFidelityWaveDispatcher.validate_persisted_evidence(
        out_file,
        expected_commit_sha=receipt.commit_sha,
    )
    if receipt.wave_verdict != "PASS" or not evidence_valid:
        print(
            "Command Fidelity Wave HOLD: live operation receipt or exact persisted evidence validation failed.",
            file=sys.stderr,
        )
        print(f"Evidence persisted to: {out_file}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Command Fidelity Wave executed successfully. Verdict: {receipt.wave_verdict}")
    print(f"Execution SHA: {receipt.commit_sha}")
    print(f"Evidence persisted to: {out_file}")
    print("Persisted evidence validation: PASS")


if __name__ == "__main__":
    main()
