from __future__ import annotations

from types import SimpleNamespace

import pytest

from sage.c2.canonical_transition_bridge import CanonicalC2TransitionBridge


def _response(action_type="SET_TASK", target="canonical_runtime_state", parameters=None, evidence_refs=("evidence:turn-1",)):
    proposal = SimpleNamespace(
        action_type=action_type,
        target=target,
        parameters=parameters or {"task": "advance governed transition"},
        justification="validated governed turn",
    )
    return SimpleNamespace(
        station="[SAGE::C2::CHATGPT]",
        proposed_actions=[proposal] if action_type is not None else [],
        evidence_refs=evidence_refs,
    )


class _Runtime:
    def __init__(self):
        self.current_state = SimpleNamespace(current_objective="objective", active_task="old task")
        self.current_state.model_dump = lambda: {
            "current_objective": self.current_state.current_objective,
            "active_task": self.current_state.active_task,
        }
        self.bond_manager = SimpleNamespace(execute_transition=lambda state, payload: {"last_applied_transition": "bond-1"})
        self.authority_gate = SimpleNamespace(request_mutation=self._mutate)
        self.context_tracker = SimpleNamespace(record_transition=self._record)
        self.transitions = []
        self.checkpoints = 0

    def _mutate(self, runtime, action, value):
        self.transitions.append((action, value))
        if action == "set_task":
            self.current_state.active_task = value
        elif action == "set_objective":
            self.current_state.current_objective = value

    def _record(self, **kwargs):
        self.transitions.append(("continuity", kwargs))

    def checkpoint(self):
        self.checkpoints += 1
        return "checkpoint-1"


def test_valid_proposal_uses_fixed_runtime_mapping_and_checkpoint():
    runtime = _Runtime()
    result = CanonicalC2TransitionBridge(runtime).apply(_response())

    assert result.accepted is True
    assert result.runtime_action == "set_task"
    assert runtime.transitions[0] == ("set_task", "advance governed transition")
    assert runtime.checkpoints == 1
    assert result.before_state_digest != result.after_state_digest
    assert "bond:bond-1" in result.evidence_refs


def test_unknown_action_is_rejected_before_runtime_mutation():
    runtime = _Runtime()
    with pytest.raises(ValueError, match="Unsupported C2 transition action"):
        CanonicalC2TransitionBridge(runtime).apply(_response(action_type="EXECUTE_ARBITRARY_METHOD", parameters={"method": "set_task"}))
    assert runtime.transitions == []
    assert runtime.checkpoints == 0


def test_noncanonical_target_is_rejected_before_runtime_mutation():
    runtime = _Runtime()
    with pytest.raises(ValueError, match="outside canonical runtime state"):
        CanonicalC2TransitionBridge(runtime).apply(_response(target="model_output"))
    assert runtime.transitions == []


def test_mutation_requires_evidence():
    runtime = _Runtime()
    with pytest.raises(ValueError, match="requires evidence_refs"):
        CanonicalC2TransitionBridge(runtime).apply(_response(evidence_refs=()))
    assert runtime.transitions == []
