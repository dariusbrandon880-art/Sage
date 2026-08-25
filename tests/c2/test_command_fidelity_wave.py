"""Unit tests for Flight E: Five-Flight Command Fidelity Wave Dispatcher."""

from pathlib import Path
import json
from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher


def test_command_fidelity_wave_dispatch_success():
    dispatcher = CommandFidelityWaveDispatcher()
    receipt = dispatcher.dispatch_wave()

    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_results) == 5
    assert all(f.status == "PASS" for f in receipt.flight_results)


def test_command_fidelity_wave_evidence_persistence(tmp_path):
    dispatcher = CommandFidelityWaveDispatcher()
    receipt = dispatcher.dispatch_wave()

    evidence_file = tmp_path / "command_fidelity_wave_evidence.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    assert evidence_file.exists()
    data = json.loads(evidence_file.read_text())
    assert data["wave_verdict"] == "PASS"
    assert len(data["flight_results"]) == 5
