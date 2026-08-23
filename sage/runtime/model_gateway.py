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
class SAGEActionProposal:
    """Action proposed by a model under SAGE governance."""

    action_type: str
    target: str
    parameters: dict[str, Any]
    justification: str


@dataclass(frozen=True)
class SAGEEpistemicState:
    """Epistemic state representation returned by a model."""

    confidence_level: str  # HIGH, MEDIUM, LOW, UNCERTAIN
    validated_facts: tuple[str, ...] = ()
    unverified_hypotheses: tuple[str, ...] = ()
    known_unknowns: tuple[str, ...] = ()


@dataclass(frozen=True)
class SAGEStructuredResponse:
    """Canonical structured response payload for SAGE governed models."""

    station: str
    reasoning_chain: tuple[str, ...]
    proposed_actions: tuple[SAGEActionProposal, ...]
    epistemic_state: SAGEEpistemicState
    evidence_refs: tuple[str, ...] = ()
    is_roleplay: bool = False
    violations: tuple[str, ...] = ()


class SAGEProtocolGovernor:
    """Enforces SAGE protocol compliance and anti-roleplay governance on model outputs."""

    ROLEPLAY_INDICATORS = (
        "as an ai",
        "in roleplay mode",
        "pretend that",
        "pretend you",
        "let's pretend",
        "imagine i am",
        "i will act as",
        "simulation mode",
        "virtual assistant persona",
        "character mode",
        "*nods*",
        "*smiles*",
        "*chuckles*",
    )

    AUTHORITY_CLAIM_INDICATORS = (
        "i hereby authorize",
        "i have updated canonical state",
        "update canonical state",
        "state mutated directly",
        "granting execution permissions",
        "bypassing preflight check",
        "overriding spek governance",
    )

    EVIDENCE_BYPASS_INDICATORS = (
        "ignore the evidence requirement",
        "ignore evidence requirement",
        "bypass evidence requirement",
        "without evidence requirement",
        "skip evidence validation",
    )

    UNVERIFIED_REPOSITORY_INDICATORS = (
        "claim a github change happened",
        "commit pushed to origin",
        "pushed commit to github",
        "github change happened",
    )

    @classmethod
    def validate_and_parse(cls, raw_output: str, required_station: str = "[SAGE::C2::CHATGPT]") -> SAGEStructuredResponse:
        """Parse raw model output and enforce anti-roleplay + authority boundaries."""
        violations: list[str] = []
        lower_output = raw_output.lower()

        # 1. Anti-roleplay checks
        is_roleplay = any(indicator in lower_output for indicator in cls.ROLEPLAY_INDICATORS)
        if is_roleplay:
            violations.append("Model output contains conversational roleplay indicators.")

        # 2. Authority claim checks
        if any(indicator in lower_output for indicator in cls.AUTHORITY_CLAIM_INDICATORS):
            violations.append("Model output falsely claims authority to authorize or mutate canonical state.")

        # 3. Evidence bypass checks
        if any(indicator in lower_output for indicator in cls.EVIDENCE_BYPASS_INDICATORS):
            violations.append("Model output attempts to ignore or bypass evidence requirement.")

        # 4. Unverified repository claim checks
        if any(indicator in lower_output for indicator in cls.UNVERIFIED_REPOSITORY_INDICATORS):
            violations.append("Model output claims repository or GitHub state change without verification receipt.")

        # 3. Structured JSON parsing attempt
        parsed_data: dict[str, Any] = {}
        reasoning_chain: list[str] = []
        proposed_actions: list[SAGEActionProposal] = []
        evidence_refs: list[str] = []
        epistemic = SAGEEpistemicState(confidence_level="UNKNOWN")

        try:
            # Check for JSON block or raw JSON
            json_str = raw_output
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()

            parsed_data = json.loads(json_str)
            if isinstance(parsed_data, dict):
                station = parsed_data.get("station", required_station)
                reasoning_chain = list(parsed_data.get("reasoning_chain", []))

                raw_actions = parsed_data.get("proposed_actions", [])
                for act in raw_actions:
                    if isinstance(act, dict):
                        proposed_actions.append(
                            SAGEActionProposal(
                                action_type=str(act.get("action_type", "UNKNOWN")),
                                target=str(act.get("target", "UNKNOWN")),
                                parameters=dict(act.get("parameters", {})),
                                justification=str(act.get("justification", "")),
                            )
                        )

                evidence_refs = list(parsed_data.get("evidence_refs", []))

                # Check for completion actions without evidence receipts
                completion_action_types = {"deployment", "mutation", "completion", "execution"}
                has_completion_action = any(act.action_type.lower() in completion_action_types for act in proposed_actions)
                if has_completion_action and not evidence_refs:
                    violations.append("Completion or deployment claim has no verification receipt in evidence_refs.")

                raw_ep = parsed_data.get("epistemic_state", {})
                if isinstance(raw_ep, dict):
                    epistemic = SAGEEpistemicState(
                        confidence_level=str(raw_ep.get("confidence_level", "UNKNOWN")),
                        validated_facts=tuple(raw_ep.get("validated_facts", [])),
                        unverified_hypotheses=tuple(raw_ep.get("unverified_hypotheses", [])),
                        known_unknowns=tuple(raw_ep.get("known_unknowns", [])),
                    )
        except Exception:
            # Output is non-JSON or unstructured text
            reasoning_chain = [raw_output.strip()]

        if not reasoning_chain and not proposed_actions:
            violations.append("Model output lacks structured SAGE reasoning or proposed actions.")

        return SAGEStructuredResponse(
            station=required_station,
            reasoning_chain=tuple(reasoning_chain),
            proposed_actions=tuple(proposed_actions),
            epistemic_state=epistemic,
            evidence_refs=tuple(evidence_refs),
            is_roleplay=is_roleplay,
            violations=tuple(violations),
        )


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
    structured_response: SAGEStructuredResponse | None = None


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
