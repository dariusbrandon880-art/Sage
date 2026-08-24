"""Boundary tests for read-only, fail-closed failure-memory preflight."""

import builtins

import pytest

from sage.experimental.progression import MissionProgressionController, MissionProgressionState


def _controller_for_objective(objective: str) -> MissionProgressionController:
    controller = MissionProgressionController()
    controller.intake_mission(
        {
            "mission_id": "failure-memory-test",
            "objective": objective,
            "priority_score": 100.0,
            "assigned_agent": "agent_jules_sage",
        }
    )
    controller.prioritize()
    return controller


def test_known_failure_pattern_blocks_without_mutating_mission():
    controller = _controller_for_objective("Execute known_failure_trigger immediately")
    original = dict(controller.mission_data)

    with pytest.raises(ValueError, match="failure memory pattern"):
        controller.validate_preflight()

    assert controller.current_state == MissionProgressionState.PRIORITIZED
    assert controller.mission_data == original
    assert controller.receipts == controller.receipts[:2]


def test_failure_intelligence_import_error_fails_closed(monkeypatch):
    controller = _controller_for_objective("Normal bounded objective")
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "sage.failure_intelligence":
            raise ImportError("simulated failure intelligence outage")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    with pytest.raises(ValueError, match="failed closed"):
        controller.validate_preflight()

    assert controller.current_state == MissionProgressionState.PRIORITIZED
