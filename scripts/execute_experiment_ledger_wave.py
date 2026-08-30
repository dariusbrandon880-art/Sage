#!/usr/bin/env python3
"""Runner script for SAGE Big Jump Wave with concurrent Experiment Ledger recording."""

import json
from pathlib import Path
import time
from sage.c2.build_jump_wave import BuildJumpWaveEngine
from sage.c2.experiment_ledger import ExperimentLedger, ValidationStatus


def main():
    storage_dir = Path("evidence_capture")
    storage_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = storage_dir / "experiment_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_path))

    engine = BuildJumpWaveEngine(storage_dir=str(storage_dir), experiment_ledger=ledger)
    head_sha = engine.get_current_head_sha()

    wave_id = f"wave-experiment-ledger-{int(time.time())}"
    print(f"Executing Big Jump Wave {wave_id} at HEAD SHA {head_sha} with Experiment Ledger...")

    reconvergence_pkg = engine.execute_wave(wave_id=wave_id)

    # Re-read experiments from ledger
    experiments = ledger.list_experiments()

    evidence_summary = {
        "wave_id": wave_id,
        "head_sha": head_sha,
        "overall_verdict": reconvergence_pkg.reconvergence_verdict,
        "timestamp": time.time(),
        "total_experiments_recorded": len(experiments),
        "promoted_count": sum(1 for e in experiments if e.status == ValidationStatus.PROMOTED),
        "hold_count": sum(1 for e in experiments if e.status == ValidationStatus.HOLD),
        "rejected_count": sum(1 for e in experiments if e.status == ValidationStatus.REJECTED),
        "ledger_file": str(ledger_path),
    }

    out_file = storage_dir / "experiment_ledger_wave_evidence.json"
    out_file.write_text(json.dumps(evidence_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wave execution complete. Verdict: {reconvergence_pkg.reconvergence_verdict}")
    print(f"Recorded {len(experiments)} experiments in {ledger_path}")
    print(f"Evidence receipt saved to {out_file}")


if __name__ == "__main__":
    main()
