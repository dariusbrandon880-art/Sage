#!/usr/bin/env python3
"""Runner script to execute Five-Flight Command Fidelity Wave and persist structured evidence."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher


def main():
    dispatcher = CommandFidelityWaveDispatcher()
    receipt = dispatcher.dispatch_wave()

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
            "Command Fidelity Wave HOLD: persisted evidence failed exact-head validation.",
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
