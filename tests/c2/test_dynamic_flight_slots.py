"""Governance tests preventing permanent F1-F5 mission pinning."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_single_wave_runner_has_no_permanent_mission_map():
    source = (ROOT / "scripts" / "execute_build_jump_wave.py").read_text(encoding="utf-8")
    assert "build_canonical_wave_missions" not in source
    assert "--mission-plan" in source
    assert "flight_id=f\"F{i}\"" not in source


def test_double_wave_runner_has_no_permanent_mission_map():
    source = (ROOT / "scripts" / "execute_double_big_jump_wave.py").read_text(encoding="utf-8")
    assert "targets_a" not in source
    assert "targets_b" not in source
    assert "--mission-plan" in source
    assert "flight_id=f\"F{i}\"" not in source


def test_operating_frame_does_not_pin_flights_to_permanent_roles():
    source = (ROOT / "docs" / "governance" / "BIG_JUMP_WAVE_C2_5X4_OPERATING_FRAME.md").read_text(encoding="utf-8")
    assert "F1 Foundation" not in source
    assert "F2 Intelligence" not in source
    assert "F3 Execution" not in source
    assert "F4 Verification" not in source
    assert "F5 Capability Warehouse" not in source
    assert "F1-F5 are **five reusable slots**" in source


def test_flight_assignment_contract_declares_dynamic_slots():
    source = (ROOT / "docs" / "governance" / "FLIGHT_ASSIGNMENT_CONTRACT.md").read_text(encoding="utf-8")
    assert "F1-F5 are reusable execution slots" in source
    assert "The dispatcher must not infer a mission from the flight number." in source
