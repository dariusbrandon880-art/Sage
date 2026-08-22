"""Model-agnostic SAGE runtime control plane.

Canonical state, identity, authority scope, and evidence remain SAGE-owned;
model adapters only transport proposals/evidence through an explicit envelope.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class SAGEStateSnapshot:
    """Canonical state supplied by the SAGE authority layer."""

    state_version: str
    instance_id: str
    mission_id: str
    session_id: str
    authority_scope: str
    active_frontier: str
    stop_boundary: str
    evidence_refs: tuple[str, ...] = ()
    known_state_refs: tuple[str, ...] = ()
    candidate_state_refs: tuple[str, ...] = ()
    negative_memory_refs: tuple[str, ...] = ()

    def digest(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SAGERuntimeEnvelope:
    """Deterministic state envelope presented to any model adapter."""

    station: str
    model_role: str
    state: SAGEStateSnapshot
    required_output_contract: str
    policy_version: str
    state_digest: str

    @classmethod
    def from_state(
        cls,
        state: SAGEStateSnapshot,
        *,
        model_role: str,
        station: str = "[SAGE::C2::CHATGPT]",
        required_output_contract: str = "structured_sage_response_v1",
        policy_version: str = "sage-runtime-v1",
    ) -> "SAGERuntimeEnvelope":
        return cls(
            station=station,
            model_role=model_role,
            state=state,
            required_output_contract=required_output_contract,
            policy_version=policy_version,
            state_digest=state.digest(),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state_digest"] = self.state.digest()
        return payload


@dataclass(frozen=True)
class ModelResponse:
    """Model output returned to SAGE for reconciliation, not direct authority."""

    model_id: str
    instance_id: str
    mission_id: str
    session_id: str
    input_state_digest: str
    proposed_actions: tuple[Mapping[str, Any], ...] = ()
    evidence_refs: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    output_state_digest: str | None = None
    raw_output: Any = None


class ModelAdapter(Protocol):
    """Transport contract implemented by OpenAI/Gemini/other model adapters."""

    model_id: str

    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse:
        """Execute one model call under an explicit SAGE envelope."""
        ...


class SAGERuntime:
    """Owns state-envelope construction and response reconciliation boundaries."""

    def __init__(self, state: SAGEStateSnapshot):
        self.state = state

    def envelope(
        self,
        model_role: str,
        *,
        station: str = "[SAGE::C2::CHATGPT]",
    ) -> SAGERuntimeEnvelope:
        return SAGERuntimeEnvelope.from_state(
            self.state,
            model_role=model_role,
            station=station,
        )

    def reconcile(self, response: ModelResponse) -> None:
        """Reject cross-mission/session/state responses before authority use."""
        if response.instance_id != self.state.instance_id:
            raise ValueError("SAGE instance identity mismatch")
        if response.mission_id != self.state.mission_id:
            raise ValueError("SAGE mission identity mismatch")
        if response.session_id != self.state.session_id:
            raise ValueError("SAGE session identity mismatch")
        if response.input_state_digest != self.state.digest():
            raise ValueError("SAGE input state digest mismatch")

    def invoke(self, adapter: ModelAdapter, task: str, *, model_role: str) -> ModelResponse:
        """Invoke a replaceable model and reconcile its response before returning it."""
        response = adapter.invoke(
            self.envelope(
                model_role,
                station=getattr(adapter, "station", "[SAGE::C2::CHATGPT]"),
            ),
            task,
        )
        self.reconcile(response)
        return response
