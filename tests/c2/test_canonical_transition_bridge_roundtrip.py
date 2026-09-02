from __future__ import annotations

from types import SimpleNamespace

from sage.c2.canonical_transition_bridge import CanonicalC2TransitionBridge
from sage.c2.immersion_rehydration import build_chatgpt_immersion_state
from sage.runtime.engine import SageRuntime


def _response(task: str) -> SimpleNamespace:
    proposal = SimpleNamespace(
        action_type="SET_TASK",
        target="canonical_runtime_state",
        parameters={"task": task},
        justification="verified C2 round-trip integration test",
    )
    return SimpleNamespace(
        station="[SAGE::C2::CHATGPT]",
        proposed_actions=[proposal],
        evidence_refs=("evidence:integration-roundtrip",),
    )


def test_real_runtime_transition_persists_and_rehydrates(tmp_path):
    workspace = tmp_path / "sage-runtime"
    runtime = SageRuntime(workspace_path=str(workspace))
    runtime.set_objective("C2 transition bridge integration")

    result = CanonicalC2TransitionBridge(runtime).apply(
        _response("prove real runtime state survives the next turn")
    )

    assert result.accepted is True
    assert runtime.current_state.active_task == "prove real runtime state survives the next turn"
    assert result.before_state_digest != result.after_state_digest

    fresh_runtime = SageRuntime(workspace_path=str(workspace))
    assert fresh_runtime.current_state.current_objective == "C2 transition bridge integration"
    assert fresh_runtime.current_state.active_task == "prove real runtime state survives the next turn"

    immersion = build_chatgpt_immersion_state(
        fresh_runtime,
        session_id="roundtrip-session",
        evidence_refs=result.evidence_refs,
    )
    assert immersion.mission == "C2 transition bridge integration"
    assert immersion.next_move == "prove real runtime state survives the next turn"
    assert "checkpoint:" in " ".join(immersion.evidence_refs)
