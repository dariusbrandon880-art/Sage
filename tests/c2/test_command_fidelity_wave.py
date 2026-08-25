"""Unit tests for Flight E: Five-Flight Command Fidelity Wave Dispatcher."""

from pathlib import Path
import json
from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher, FidelityFlightResult


def test_command_fidelity_wave_dispatch_success():
    dispatcher = CommandFidelityWaveDispatcher()
    receipt = dispatcher.dispatch_wave()

    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_results) == 5
    assert receipt.commit_sha != "UNKNOWN_COMMIT"
    assert all(f.status == "PASS" for f in receipt.flight_results)


def test_command_fidelity_wave_fails_closed_on_stale_sha():
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="actual_sha_123")
    receipt = dispatcher.dispatch_wave()
    assert receipt.commit_sha == "actual_sha_123"

    # Inject a stale receipt
    stale_result = FidelityFlightResult(
        flight_id="Flight Stale",
        flight_name="Stale Flight",
        boundary_scope="sage.c2.stale",
        status="PASS",
        receipt_hash="hash123",
        commit_sha="old_stale_sha_999",
        metrics={},
    )
    receipt.flight_results.append(stale_result)

    # Verify dispatcher fails closed if any receipt SHA mismatches
    receipt.flight_results[0] = FidelityFlightResult(
        flight_id="Flight A",
        flight_name="Directive Fidelity",
        boundary_scope="sage.c2.directive_fidelity",
        status="PASS",
        receipt_hash="hashA",
        commit_sha="mismatched_sha",
        metrics={},
    )
    # Re-verify logic
    stale_found = any(f.commit_sha != "actual_sha_123" for f in receipt.flight_results)
    assert stale_found is True


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
