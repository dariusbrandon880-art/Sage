"""Unit tests for sage.c2.multi_frontier_dispatch."""

from __future__ import annotations

import json

from sage.c2.multi_frontier_dispatch import (
    FLIGHT_MISSIONS,
    MultiFrontierDispatcher,
    compute_receipt_hash,
)


def test_flight_missions_contract():
    assert len(FLIGHT_MISSIONS) == 5
    flight_ids = {m.flight_id for m in FLIGHT_MISSIONS}
    assert flight_ids == {"Flight A", "Flight B", "Flight C", "Flight D", "Flight E"}

    mission_ids = {m.mission_id for m in FLIGHT_MISSIONS}
    assert len(mission_ids) == 5

    boundary_scopes = {m.boundary_scope for m in FLIGHT_MISSIONS}
    assert len(boundary_scopes) == 5


def test_multi_frontier_dispatch_success():
    dispatcher = MultiFrontierDispatcher(commit_sha="test_commit_sha_123")
    receipt = dispatcher.dispatch_all()

    assert receipt.commit_sha == "test_commit_sha_123"
    assert receipt.collision_count == 0
    assert not receipt.collisions_detected
    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_receipts) == 5

    proof_types = [fr.proof_type for fr in receipt.flight_receipts]
    assert proof_types == [
        "mission_objective_output_receipt",
        "independent_execution_boundary",
        "independent_capability_result",
        "architecture_guard_result",
        "evidence_warehouse_receipt",
    ]

    for fr in receipt.flight_receipts:
        expected_hash = compute_receipt_hash(
            fr.flight_id, fr.mission_id, fr.boundary_scope, fr.proof_type, "test_commit_sha_123"
        )
        assert fr.receipt_hash == expected_hash
        assert fr.status == "PASS"


def test_receipt_hash_determinism():
    hash1 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash2 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash3 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_2")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 hex string length


def test_serialization():
    dispatcher = MultiFrontierDispatcher(commit_sha="abc1234")
    receipt = dispatcher.dispatch_all()
    as_dict = receipt.to_dict()

    assert as_dict["commit_sha"] == "abc1234"
    assert as_dict["wave_verdict"] == "PASS"
    assert len(as_dict["flight_receipts"]) == 5

    # Confirm JSON serializable
    json_str = json.dumps(as_dict)
    assert "Flight A" in json_str
    assert "architecture_guard_result" in json_str
