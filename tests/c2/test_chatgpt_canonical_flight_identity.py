from types import SimpleNamespace

import pytest

from sage.c2.immersion_rehydration import build_chatgpt_immersion_state

def test_chatgpt_flight_identity_is_runtime_bound_not_synthetic():
    runtime = SimpleNamespace(
        current_state=SimpleNamespace(
            current_objective="objective",
            active_task="task",
            blockers=[],
            dependencies=[],
        ),
        get_status=lambda: {"c2_status": {"rehydrated": True}},
    )
    state = build_chatgpt_immersion_state(runtime, session_id="session_123")
    assert state.flight_id == "C2:session_123"
    assert state.flight_id != "FLIGHT_001"
    assert state.provenance_head

def test_chatgpt_immersion_fails_closed_without_canonical_runtime_state():
    with pytest.raises(ValueError, match="canonical runtime state"):
        build_chatgpt_immersion_state(SimpleNamespace(), session_id="session_123")
