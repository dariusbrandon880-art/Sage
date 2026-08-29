"""Unit and integration tests for SAGI 15-Flight Concurrency Engine."""

import re
import pytest

from sage.experimental.sagi_15_flight_concurrency import (
    FlightExecutionDetail,
    SAGI15FlightConcurrencyEngine,
    SAGI15FlightConcurrencyReceipt,
    check_timing_concurrency,
    generate_default_15_candidates,
)
from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
)


@pytest.fixture
def concurrency_engine():
    return SAGI15FlightConcurrencyEngine(max_session_workers=3, max_flight_workers=15)


@pytest.fixture
def valid_git_head():
    return "a162dfd30fb3c933a50d067febd43095f27cb00d"


def test_default_15_candidates_generation():
    sessions = ["session-a", "session-b", "session-c"]
    candidates_map = generate_default_15_candidates(sessions)
    assert len(candidates_map) == 3
    for sess in sessions:
        assert sess in candidates_map
        cands = candidates_map[sess]
        assert len(cands) == 5
        roles = {c.role for c in cands}
        assert roles == set(FlightRole)


def test_15_flight_concurrency_wave_execution(concurrency_engine, valid_git_head):
    receipt: SAGI15FlightConcurrencyReceipt = concurrency_engine.execute_concurrency_wave(
        wave_id="test_sagi_15f_001",
        exact_git_head=valid_git_head,
    )
    assert receipt.wave_id == "test_sagi_15f_001"
    assert receipt.exact_git_head == valid_git_head
    assert len(receipt.active_sessions) == 3
    assert receipt.total_flights == 15
    assert receipt.successful_flights == 15
    assert receipt.total_advancement_cells == 60
    assert receipt.is_truly_concurrent is True
    assert receipt.rolls_royce_quality_passed is True
    assert receipt.reconvergence_verdict == "PASS"
    assert len(receipt.session_summaries) == 3
    assert re.fullmatch(r"[0-9a-fA-F]{64}", receipt.receipt_hash)


def test_concurrency_timing_overlap_assertion(concurrency_engine, valid_git_head):
    receipt: SAGI15FlightConcurrencyReceipt = concurrency_engine.execute_concurrency_wave(
        wave_id="test_sagi_15f_concurrency_timing",
        exact_git_head=valid_git_head,
    )
    all_flights: list[FlightExecutionDetail] = []
    for sess_summary in receipt.session_summaries.values():
        all_flights.extend(sess_summary.flights)

    assert len(all_flights) == 15
    distinct_threads = {f.worker_thread for f in all_flights}
    assert len(distinct_threads) > 1, "Execution must utilize multiple worker threads"
    assert check_timing_concurrency(all_flights) is True, "Timing intervals across threads must overlap"


def test_sequential_execution_fails_concurrency_check():
    # Construct artificial sequential details on same thread
    seq_details = [
        FlightExecutionDetail(
            session_id="sess_1",
            flight_id=f"F1{i}",
            role="role",
            candidate_id=f"cand_{i}",
            target_path="path.py",
            collision_namespace="ns",
            start_time=100.0 + i * 10,
            end_time=100.0 + i * 10 + 5,
            worker_thread="single-main-thread",
            lock_acquired=True,
            tests_passed=5,
            test_references=["test.py"],
            execution_result="PASS",
        )
        for i in range(1, 6)
    ]
    assert check_timing_concurrency(seq_details) is False


def test_invalid_sha_rejection(concurrency_engine):
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        concurrency_engine.execute_concurrency_wave(
            wave_id="invalid_sha_wave",
            exact_git_head="shortsha123",
        )


def test_invalid_session_count_rejection(concurrency_engine, valid_git_head):
    with pytest.raises(ValueError, match="requires exactly 3 active sessions"):
        concurrency_engine.execute_concurrency_wave(
            wave_id="invalid_session_count",
            exact_git_head=valid_git_head,
            session_ids=["sess-1", "sess-2"],
        )


def test_missing_session_candidates_rejection(concurrency_engine, valid_git_head):
    sessions = ["sess-1", "sess-2", "sess-3"]
    incomplete_candidates = {"sess-1": generate_default_15_candidates(["sess-1"])["sess-1"]}
    with pytest.raises(ValueError, match="Missing discovery candidates for session"):
        concurrency_engine.execute_concurrency_wave(
            wave_id="missing_candidates_wave",
            exact_git_head=valid_git_head,
            session_candidates=incomplete_candidates,
            session_ids=sessions,
        )


def test_unsafe_candidate_fails_closed(concurrency_engine, valid_git_head):
    sessions = ["sess-1", "sess-2", "sess-3"]
    candidates = generate_default_15_candidates(sessions)
    cand_list = list(candidates["sess-1"])
    cand_list[0] = DiscoveryCandidate(
        candidate_id="unsafe_cand",
        description="Unsafe candidate test",
        role=cand_list[0].role,
        consequentiality=0.9,
        information_gain=0.9,
        falsification_value=0.9,
        safety=0.0,
        evidence_gap=0.9,
        provenance_ref="unsafe-test",
    )
    candidates["sess-1"] = tuple(cand_list)

    with pytest.raises(ValueError, match="no safe candidate for required role"):
        concurrency_engine.execute_concurrency_wave(
            wave_id="unsafe_candidate_wave",
            exact_git_head=valid_git_head,
            session_candidates=candidates,
            session_ids=sessions,
        )


def test_receipt_hash_computation():
    receipt = SAGI15FlightConcurrencyReceipt(
        receipt_id="rec_test_15f",
        wave_id="wave_hash_test",
        exact_git_head="a162dfd30fb3c933a50d067febd43095f27cb00d",
        active_sessions=["s1", "s2", "s3"],
        successful_flights=15,
        rolls_royce_quality_passed=True,
        reconvergence_verdict="PASS",
        start_time=100.0,
        end_time=105.0,
        is_truly_concurrent=True,
        session_summaries={},
    )
    hash_1 = receipt.compute_hash()
    assert len(hash_1) == 64
    assert hash_1 == receipt.compute_hash()
