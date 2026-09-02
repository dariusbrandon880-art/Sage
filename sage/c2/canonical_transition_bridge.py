"""Thin governed bridge from validated ChatGPT proposals to canonical runtime state.

The bridge deliberately does not own state, authorization, or transition policy:
- SAGEProtocolGovernor validates the model envelope.
- BondManager validates the transition/evidence contract and emits its evidence.
- ExternalAuthorityGate authorizes the existing runtime mutator.
- SageRuntime remains the canonical operational state owner.
- Immersion rehydration remains a read-only projection of resulting state.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from sage.acr.bond import BondValidationError
from sage.core.boundary import BoundaryEnforcer
from sage.runtime.model_gateway import SAGEStructuredResponse


CANONICAL_TARGET = "canonical_runtime_state"


class C2TransitionAction(StrEnum):
    SET_OBJECTIVE = "SET_OBJECTIVE"
    SET_TASK = "SET_TASK"
    ADD_BLOCKER = "ADD_BLOCKER"
    RESOLVE_BLOCKER = "RESOLVE_BLOCKER"


_ACTIONS: dict[C2TransitionAction, tuple[str, str]] = {
    C2TransitionAction.SET_OBJECTIVE: ("objective", "set_objective"),
    C2TransitionAction.SET_TASK: ("task", "set_task"),
    C2TransitionAction.ADD_BLOCKER: ("blocker", "add_blocker"),
    C2TransitionAction.RESOLVE_BLOCKER: ("blocker", "resolve_blocker"),
}


@dataclass(frozen=True)
class C2TransitionResult:
    accepted: bool
    action_type: str
    runtime_action: str | None = None
    transition_id: str | None = None
    evidence_refs: tuple[str, ...] = ()
    before_state_digest: str = ""
    after_state_digest: str = ""


class CanonicalC2TransitionBridge:
    """Apply at most one validated model proposal through existing SAGE authority."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    @staticmethod
    def _digest(runtime: Any) -> str:
        state = runtime.current_state.model_dump()
        return sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _value(action: C2TransitionAction, parameters: dict[str, Any]) -> str:
        expected_key, _ = _ACTIONS[action]
        if set(parameters) != {expected_key}:
            raise ValueError(f"{action.value} requires exactly one parameter: {expected_key}")
        value = parameters[expected_key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{action.value} parameter {expected_key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _bond_flow(action: C2TransitionAction) -> tuple[str, str]:
        if action is C2TransitionAction.SET_TASK:
            return "Delta", "Evidence"
        return "S0", "Delta"

    def apply(self, response: SAGEStructuredResponse) -> C2TransitionResult:
        """Validate and, only when warranted, advance canonical operational state."""
        if response.station != "[SAGE::C2::CHATGPT]":
            raise ValueError("C2 transition bridge requires ChatGPT station identity")

        proposals = response.proposed_actions
        if not proposals:
            return C2TransitionResult(accepted=False, action_type="NOOP")
        if len(proposals) != 1:
            raise ValueError("C2 transition bridge accepts exactly one proposal per governed turn")
        if not response.evidence_refs:
            raise ValueError("C2 state mutation proposal requires evidence_refs")

        proposal = proposals[0]
        try:
            action = C2TransitionAction(str(proposal.action_type).upper())
        except ValueError as exc:
            raise ValueError(f"Unsupported C2 transition action: {proposal.action_type}") from exc
        if str(proposal.target) != CANONICAL_TARGET:
            raise ValueError("C2 transition target is outside canonical runtime state")

        value = self._value(action, dict(proposal.parameters))
        runtime_action = _ACTIONS[action][1]
        before = self._digest(self._runtime)
        transition_id = None
        old_value = ""
        if action is C2TransitionAction.SET_TASK:
            old_value = getattr(self._runtime.current_state, "active_task", None) or "None"
        elif action is C2TransitionAction.SET_OBJECTIVE:
            old_value = getattr(self._runtime.current_state, "current_objective", None) or "None"

        from_state, to_state = self._bond_flow(action)
        bond_state = {"current_project_state": from_state, "runtime_state_digest": before}
        bond_payload = {
            "from_state": from_state,
            "to_state": to_state,
            "description": str(proposal.justification or f"Governed C2 {action.value}"),
            "category": "c2_runtime_transition",
            "author": "chatgpt_governed",
            "validation_score": 1.0,
            "evidence_refs": list(response.evidence_refs),
            "parent_ids": [],
            "contradictions": [],
            "auth_token": BoundaryEnforcer.SYSTEM_TOKEN,
            "metadata": {
                "action_type": action.value,
                "runtime_action": runtime_action,
                "parameter": value,
                "target": CANONICAL_TARGET,
            },
        }

        try:
            validated_state = self._runtime.bond_manager.execute_transition(bond_state, bond_payload)
            transition_id = validated_state.get("last_applied_transition")
        except BondValidationError:
            raise

        mutator = getattr(self._runtime, "authority_gate", None)
        if mutator is None:
            raise ValueError("Canonical C2 transition bridge requires runtime authority_gate")
        mutator.request_mutation(self._runtime, runtime_action, value)

        if action is not C2TransitionAction.SET_OBJECTIVE:
            self._runtime.context_tracker.record_transition(
                from_state=f"{runtime_action}:{old_value}",
                to_state=f"{runtime_action}:{value}",
                reason="Canonical C2 transition bridge applied validated model proposal",
            )

        checkpoint_id = self._runtime.checkpoint()
        after = self._digest(self._runtime)
        refs = tuple(dict.fromkeys((*response.evidence_refs, f"bond:{transition_id or 'validated'}", f"checkpoint:{checkpoint_id}")))
        return C2TransitionResult(
            accepted=True,
            action_type=action.value,
            runtime_action=runtime_action,
            transition_id=transition_id,
            evidence_refs=refs,
            before_state_digest=before,
            after_state_digest=after,
        )


__all__ = ["C2TransitionAction", "C2TransitionResult", "CanonicalC2TransitionBridge", "CANONICAL_TARGET"]
