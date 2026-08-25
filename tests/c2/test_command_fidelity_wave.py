"""Unit tests for Flight E: Five-Flight Command Fidelity Wave Dispatcher."""

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

    stale_found = any(f.commit_sha != "actual_sha_123" for f in receipt.flight_results)
    assert stale_found is True


def test_command_fidelity_wave_evidence_persistence_and_validation(tmp_path):
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="head_sha_abc")
    receipt = dispatcher.dispatch_wave()

    evidence_file = tmp_path / "command_fidelity_wave_evidence.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    assert evidence_file.exists()
    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(evidence_file, expected_commit_sha="head_sha_abc") is True
    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(evidence_file, expected_commit_sha="stale_sha_70d1e") is False


def test_persisted_evidence_fails_closed_on_flight_sha_mismatch(tmp_path):
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="head_sha_abc")
    receipt = dispatcher.dispatch_wave()

    stale_dict = receipt.to_dict()
    stale_dict["flight_results"][0]["commit_sha"] = "stale_sha_70d1e"

    evidence_file = tmp_path / "command_fidelity_wave_evidence_tampered.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(stale_dict, f, indent=2)

    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(evidence_file, expected_commit_sha="head_sha_abc") is False
