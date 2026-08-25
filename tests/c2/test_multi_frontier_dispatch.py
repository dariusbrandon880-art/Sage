"""Unit and concurrency tests for sage.c2.multi_frontier_dispatch."""

from __future__ import annotations

import json
import threading

from sage.c2.multi_frontier_dispatch import FLIGHT_MISSIONS, MultiFrontierDispatcher, compute_receipt_hash


def test_flight_missions_contract():
    assert len(FLIGHT_MISSIONS) == 5
    assert {m.flight_id for m in FLIGHT_MISSIONS} == {"Flight A", "Flight B", "Flight C", "Flight D", "Flight E"}
    assert len({m.mission_id for m in FLIGHT_MISSIONS}) == 5
    assert len({m.boundary_scope for m in FLIGHT_MISSIONS}) == 5


def test_multi_frontier_dispatch_success():
    receipt = MultiFrontierDispatcher(commit_sha="test_commit_sha_123").dispatch_all()
    assert receipt.commit_sha == "test_commit_sha_123"
    assert receipt.collision_count == 0
    assert not receipt.collisions_detected
    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_receipts) == 5
    assert receipt.summary["execution_mode"] == "concurrent"
    assert receipt.summary["max_workers"] == 5

    assert [fr.proof_type for fr in receipt.flight_receipts] == [
        "mission_objective_output_receipt", "independent_execution_boundary",
        "independent_capability_result", "architecture_guard_result",
        "evidence_warehouse_receipt",
    ]
    for fr in receipt.flight_receipts:
        assert fr.receipt_hash == compute_receipt_hash(
            fr.flight_id, fr.mission_id, fr.boundary_scope, fr.proof_type, "test_commit_sha_123"
        )
        assert fr.status == "PASS"


def test_five_flights_execute_concurrently(monkeypatch):
    """Prove all five handlers overlap, rather than merely producing five receipts."""
    dispatcher = MultiFrontierDispatcher(commit_sha="concurrency_test_sha")
    barrier = threading.Barrier(5)
    active = 0
    max_active = 0
    lock = threading.Lock()

    originals = {
        "a": dispatcher._execute_flight_a,
        "b": dispatcher._execute_flight_b,
        "c": dispatcher._execute_flight_c,
        "d": dispatcher._execute_flight_d,
        "e": dispatcher._execute_flight_e,
    }

    def wrap(handler):
        def wrapped(mission):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                barrier.wait(timeout=2)
                return handler(mission)
            finally:
                with lock:
                    active -= 1
        return wrapped

    for suffix, handler in originals.items():
        monkeypatch.setattr(dispatcher, f"_execute_flight_{suffix}", wrap(handler))

    receipt = dispatcher.dispatch_all()
    assert receipt.wave_verdict == "PASS"
    assert len(receipt.flight_receipts) == 5
    assert max_active == 5


def test_receipt_hash_determinism():
    hash1 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash2 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash3 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_2")
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_serialization():
    receipt = MultiFrontierDispatcher(commit_sha="abc1234").dispatch_all()
    as_dict = receipt.to_dict()
    assert as_dict["commit_sha"] == "abc1234"
    assert as_dict["wave_verdict"] == "PASS"
    assert len(as_dict["flight_receipts"]) == 5
    json_str = json.dumps(as_dict)
    assert "Flight A" in json_str
    assert "architecture_guard_result" in json_str
