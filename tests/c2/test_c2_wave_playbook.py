"""Tests for C2 Wave Playbook Engine."""

from sage.c2.c2_wave_playbook import C2WavePlaybookEngine, PlaybookExecutionReceipt


def test_receipt_hash_integrity():
    receipt = PlaybookExecutionReceipt(playbook_id="pb", wave_id="wave", flight_frontiers=["F1", "F2", "F3", "F4", "F5"], success_rate=1.0, first_pass_verification=True, execution_time_seconds=12.5)
    receipt.receipt_hash = receipt.compute_hash()
    assert len(receipt.receipt_hash) == 64
    assert receipt.receipt_hash == receipt.compute_hash()


def test_default_pattern_is_five_flight():
    pattern = C2WavePlaybookEngine().suggest_optimization_pattern()
    assert pattern.pattern_name == "DEFAULT_FIVE_FLIGHT_WAVE"
    assert pattern.optimal_flight_count == 5
    assert len(pattern.recommended_frontiers) == 5


def test_history_drives_optimization_pattern():
    engine = C2WavePlaybookEngine()
    engine.record_wave_execution("pb", "w1", ["F1", "F2", "F3"], 1.0, True, 10.0)
    engine.record_wave_execution("pb", "w2", ["F1", "F4", "F5"], 0.8, False, 15.0)
    pattern = engine.suggest_optimization_pattern()
    assert pattern.pattern_name == "OPTIMIZED_PARALLEL_WAVE"
    assert pattern.historical_first_pass_rate == 0.5
    assert "F1" in pattern.recommended_frontiers
