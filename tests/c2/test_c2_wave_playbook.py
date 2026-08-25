"""Tests for C2 Wave Playbook Engine & Execution Pattern Optimizer."""

import pytest
from sage.c2.c2_wave_playbook import (
    C2WavePlaybookEngine,
    PlaybookExecutionReceipt,
    WaveOptimizationPattern,
)


def test_playbook_execution_receipt_hash_integrity():
    receipt = PlaybookExecutionReceipt(
        playbook_id="pb-001",
        wave_id="wave-001",
        flight_frontiers=["F1", "F2", "F3", "F4", "F5"],
        success_rate=1.0,
        first_pass_verification=True,
        execution_time_seconds=12.5,
    )
    receipt.receipt_hash = receipt.compute_hash()
    assert len(receipt.receipt_hash) == 64
    assert receipt.receipt_hash == receipt.compute_hash()


def test_wave_playbook_engine_default_suggestion():
    engine = C2WavePlaybookEngine()
    pattern = engine.suggest_optimization_pattern()
    assert pattern.pattern_name == "DEFAULT_FIVE_FLIGHT_WAVE"
    assert pattern.optimal_flight_count == 5
    assert len(pattern.recommended_frontiers) == 5


def test_wave_playbook_engine_recording_and_optimization():
    engine = C2WavePlaybookEngine()

    engine.record_wave_execution(
        playbook_id="pb-001",
        wave_id="w-1",
        flight_frontiers=["F1", "F2", "F3"],
        success_rate=1.0,
        first_pass_verification=True,
        execution_time_seconds=10.0,
    )
    engine.record_wave_execution(
        playbook_id="pb-001",
        wave_id="w-2",
        flight_frontiers=["F1", "F4", "F5"],
        success_rate=0.8,
        first_pass_verification=False,
        execution_time_seconds=15.0,
    )

    pattern = engine.suggest_optimization_pattern()
    assert pattern.pattern_name == "OPTIMIZED_PARALLEL_WAVE"
    assert pattern.historical_first_pass_rate == 0.5
    assert "F1" in pattern.recommended_frontiers
    assert len(pattern.recommended_frontiers) == 5
