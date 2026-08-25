"""Unit tests for Flight E: Five-Flight Command Fidelity Wave Dispatcher."""

import json

from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.command_fidelity_wave import CommandFidelityWaveDispatcher, FidelityFlightResult
from sage.c2.reality_gate import OperationalClaim, SourceReceipt


def _operation_receipt(commit_sha: str) -> SourceReceipt:
    return SourceReceipt(
        source_type="github",
        resource_id=f"commit:{commit_sha}",
        sha256_digest=commit_sha,
        timestamp_utc=1.0,
        metadata={"origin": "operation_boundary", "operation": "github_commit_observation"},
    )


def test_command_fidelity_wave_dispatch_success():
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="actual_sha_123")
    receipt = dispatcher.dispatch_wave(_operation_receipt("actual_sha_123"))

    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_results) == 5
    assert receipt.commit_sha == "actual_sha_123"
    assert all(f.status == "PASS" for f in receipt.flight_results)


def test_command_fidelity_wave_fails_closed_without_operation_receipt():
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="actual_sha_123")
    receipt = dispatcher.dispatch_wave()

    assert receipt.wave_verdict == "HOLD"
    assert receipt.summary["operation_receipt_present"] is False
    assert receipt.flight_results[1].status == "HOLD"


def test_command_fidelity_wave_fails_closed_on_stale_sha():
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="actual_sha_123")
    receipt = dispatcher.dispatch_wave(_operation_receipt("actual_sha_123"))

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
    receipt = dispatcher.dispatch_wave(_operation_receipt("head_sha_abc"))

    evidence_file = tmp_path / "command_fidelity_wave_evidence.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    assert evidence_file.exists()
    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(
        evidence_file, expected_commit_sha="head_sha_abc"
    ) is True
    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(
        evidence_file, expected_commit_sha="stale_sha_70d1e"
    ) is False


def test_persisted_evidence_fails_closed_on_flight_sha_mismatch(tmp_path):
    dispatcher = CommandFidelityWaveDispatcher(commit_sha="head_sha_abc")
    receipt = dispatcher.dispatch_wave(_operation_receipt("head_sha_abc"))

    stale_dict = receipt.to_dict()
    stale_dict["flight_results"][0]["commit_sha"] = "stale_sha_70d1e"

    evidence_file = tmp_path / "command_fidelity_wave_evidence_tampered.json"
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(stale_dict, f, indent=2)

    assert CommandFidelityWaveDispatcher.validate_persisted_evidence(
        evidence_file, expected_commit_sha="head_sha_abc"
    ) is False


def test_claim_provenance_rejects_source_type_only_live_claim():
    claim = OperationalClaim(
        claim_id="repo-clean",
        statement="GitHub repo is completely clean.",
        required_source_type="github",
        target_resource=None,
    )
    receipt = SourceReceipt(
        source_type="github",
        resource_id="repo:any",
        sha256_digest="digest",
        timestamp_utc=1.0,
    )

    result = ClaimProvenanceCompiler.compile_claims([claim], [receipt])

    assert result.is_valid is False
    assert len(result.verified_claims) == 0
    assert len(result.unresolved_claims) == 1
    assert result.unresolved_claims[0].status == "UNRESOLVED"


def test_claim_provenance_requires_exact_resource_match():
    claim = OperationalClaim(
        claim_id="head",
        statement="GitHub main is at abc.",
        required_source_type="github",
        target_resource="commit:abc",
    )
    wrong_receipt = SourceReceipt(
        source_type="github",
        resource_id="commit:def",
        sha256_digest="def",
        timestamp_utc=1.0,
    )

    result = ClaimProvenanceCompiler.compile_claims([claim], [wrong_receipt])

    assert result.is_valid is False
    assert len(result.contradicted_claims) == 1
    assert result.contradicted_claims[0].status == "CONTRADICTED"
