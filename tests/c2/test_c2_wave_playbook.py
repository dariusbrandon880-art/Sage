"""Unit and adversarial tests for SAGE C2 Wave Playbook & Capability Growth Engine."""
import pytest
from sage.c2.c2_wave_playbook import (
    C2WavePlaybookEngine,
    WaveOptimizationPattern,
    PlaybookExecutionReceipt,
)


def test_wave_optimization_pattern_digest():
    """Verify WaveOptimizationPattern computes a valid deterministic SHA-256 digest."""
    pattern = WaveOptimizationPattern(
        pattern_id="pb-001",
        name="Parallel 5-Front Strike",
        description="Optimized pattern for 5 isolated flight frontiers",
        target_frontiers=["research_intelligence", "continuity_context"],
        namespace_isolation_rules=["sage.c2.flight_a", "sage.c2.flight_b"],
        recommended_concurrency=5,
        historical_first_pass_rate=0.95,
    )
    digest = pattern.digest()
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_engine_registers_and_retrieves_matching_patterns():
    """Verify pattern registration and matching pattern retrieval ordered by first-pass rate."""
    engine = C2WavePlaybookEngine()

    p1 = WaveOptimizationPattern(
        pattern_id="pb-alpha",
        name="Alpha Playbook",
        description="High pass rate",
        target_frontiers=["research_intelligence"],
        historical_first_pass_rate=0.98,
    )
    p2 = WaveOptimizationPattern(
        pattern_id="pb-beta",
        name="Beta Playbook",
        description="Standard pass rate",
        target_frontiers=["research_intelligence"],
        historical_first_pass_rate=0.85,
    )

    digest_1 = engine.register_pattern(p1)
    digest_2 = engine.register_pattern(p2)

    assert digest_1 is not None
    assert digest_2 is not None

    matches = engine.find_matching_patterns(["research_intelligence"])
    assert len(matches) == 2
    # Alpha (0.98) must be sorted before Beta (0.85)
    assert matches[0].pattern_id == "pb-alpha"
    assert matches[1].pattern_id == "pb-beta"


def test_record_wave_execution_updates_rolling_first_pass_rate():
    """Verify execution outcome updating and rolling average first-pass rate calculations."""
    engine = C2WavePlaybookEngine()
    p1 = WaveOptimizationPattern(
        pattern_id="pb-gamma",
        name="Gamma Playbook",
        description="Initial 1.0 pass rate",
        target_frontiers=["execution_substrate"],
        historical_first_pass_rate=1.0,
    )
    engine.register_pattern(p1)

    # First run fails
    receipt1 = engine.record_wave_execution(
        pattern_id="pb-gamma",
        wave_id="wave-001",
        flights_executed=5,
        zero_collision=True,
        first_pass_success=False,
    )
    assert receipt1.first_pass_success is False
    assert engine.patterns["pb-gamma"].historical_first_pass_rate == 0.5

    # Second run succeeds
    receipt2 = engine.record_wave_execution(
        pattern_id="pb-gamma",
        wave_id="wave-002",
        flights_executed=5,
        zero_collision=True,
        first_pass_success=True,
    )
    assert receipt2.first_pass_success is True
    assert engine.patterns["pb-gamma"].historical_first_pass_rate == 0.75
    assert len(engine.execution_receipts) == 2


def test_unknown_pattern_recording_raises_value_error():
    """Verify that recording execution against an unregistered pattern raises ValueError."""
    engine = C2WavePlaybookEngine()
    with pytest.raises(ValueError, match="Unknown pattern_id: pb-missing"):
        engine.record_wave_execution(
            pattern_id="pb-missing",
            wave_id="wave-001",
            flights_executed=5,
            zero_collision=True,
            first_pass_success=True,
        )


def test_empty_pattern_id_registration_raises_value_error():
    """Verify that registering a pattern with empty pattern_id raises ValueError."""
    engine = C2WavePlaybookEngine()
    pattern = WaveOptimizationPattern(
        pattern_id="   ",
        name="Empty ID",
        description="Invalid ID",
    )
    with pytest.raises(ValueError, match="pattern_id is required"):
        engine.register_pattern(pattern)
