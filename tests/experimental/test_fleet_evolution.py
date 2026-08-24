"""Unit and adversarial tests for SAGE Fleet Evolution Intelligence Layer."""
from __future__ import annotations

import pytest

from sage.experimental.airspace.fleet_evolution import (
    FleetEvolutionIntelligence,
    compute_evolution_provenance_hash,
)


def test_evaluate_growth_signal_accelerating_path():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_100")
    receipts = [
        {"receipt_id": "r1", "status": "PASS", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r2", "status": "PASS", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r3", "status": "PASS", "commit_sha": "commit_sha_100"},
    ]

    receipt = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0)

    assert receipt.commit_sha == "commit_sha_100"
    assert receipt.growth_signal == "ACCELERATING"
    assert receipt.growth_index >= 0.8
    assert "flight_quality" in receipt.metrics
    assert "regression_resistance" in receipt.metrics
    assert len(receipt.provenance_hash) == 64


def test_evaluate_growth_signal_blocked_on_protected_path_violations():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_100")
    receipts = [{"receipt_id": "r1", "status": "PASS"}]

    receipt = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0, protected_path_violations=1)

    assert receipt.growth_signal == "BLOCKED"
    assert receipt.growth_index == 0.0
    assert "protected_boundary" in receipt.metrics


def test_adversarial_quantity_over_quality_penalty():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_100")
    # 5 receipts, only 2 valid (40% valid ratio)
    receipts = [
        {"receipt_id": "r1", "status": "PASS", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r2", "status": "PASS", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r3", "status": "FAIL", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r4", "status": "FAIL", "commit_sha": "commit_sha_100"},
        {"receipt_id": "r5", "status": "FAIL", "commit_sha": "commit_sha_100"},
    ]

    receipt = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0)

    assert receipt.growth_signal == "DEGRADED"
    assert receipt.growth_index < 0.6  # Penalty applied


def test_stale_commit_sha_degrades_growth_signal():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_current")
    receipts = [
        {"receipt_id": "r1", "status": "PASS", "commit_sha": "commit_sha_stale_old"},
    ]

    receipt = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0)

    assert receipt.growth_signal == "DEGRADED"


def test_empty_receipts_returns_stable_baseline():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_100")
    receipt = engine.evaluate_growth_signal([], test_pass_rate=1.0)

    assert receipt.growth_signal == "STABLE"
    assert receipt.growth_index == 0.5


def test_provenance_hash_determinism():
    engine = FleetEvolutionIntelligence(commit_sha="commit_sha_100")
    receipts = [{"receipt_id": "r1", "status": "PASS", "commit_sha": "commit_sha_100"}]
    rcpt1 = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0)

    expected_hash = compute_evolution_provenance_hash(
        rcpt1.commit_sha, rcpt1.growth_signal, rcpt1.growth_index, rcpt1.metrics
    )
    assert rcpt1.provenance_hash == expected_hash
