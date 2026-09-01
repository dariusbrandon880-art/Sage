"""Governance tests preventing permanent F1-F5 mission pinning."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_big_jump_wave_dispatcher_requires_explicit_dynamic_missions():
    source = (ROOT / "scripts" / "execute_build_jump_wave.py").read_text(encoding="utf-8")
    forbidden = (
        "execution_intelligence.py",
        "governance_intelligence.py",
        "build_jump_wave.py",
        "multi_frontier_dispatch.py",
        "double_big_jump_contract.py",
    )
    assert "build_canonical_wave_missions" not in source
    assert not any(name in source for name in forbidden)


def test_operating_frame_does_not_pin_flights_to_permanent_roles():
    source = (ROOT / "docs" / "governance" / "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md").read_text(encoding="utf-8")
    assert "F1 Foundation" not in source
    assert "F2 Intelligence" not in source
    assert "F3 Execution" not in source
    assert "F4 Verification" not in source
    assert "F5 Capability Warehouse" not in source
    assert "F1-F5 are reusable execution slots" in source
