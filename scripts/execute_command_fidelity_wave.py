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

    print(f"Command Fidelity Wave executed successfully. Verdict: {receipt.wave_verdict}")
    print(f"Evidence persisted to: {out_file}")


if __name__ == "__main__":
    main()
