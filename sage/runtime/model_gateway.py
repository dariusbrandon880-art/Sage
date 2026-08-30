"""Model-agnostic SAGE runtime control plane.

Canonical state, identity, authority scope, and evidence remain SAGE-owned;
model adapters only transport proposals/evidence through an explicit envelope.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from typing import Any, Mapping, Protocol

from sage.c2.chatgpt_c2_contract import classify_directive, validate_report_claims
from sage.c2.live_operation_receipt import LiveCapability, LiveOperationReceipt, execute_live_capability


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
    """Deterministic, pinned governance context presented to every model adapter."""
    station: str
    model_role: str
    state: SAGEStateSnapshot
    required_output_contract: str
    policy_version: str
    state_digest: str
    agent_identity: str = ""
    policy_digest: str = ""
    provenance_digest: str = ""

    @staticmethod
    def _policy_digest(*, station: str, model_role: str, policy_version: str) -> str:
        payload = json.dumps({"station": station, "model_role": model_role, "policy_version": policy_version}, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _provenance_digest(state: SAGEStateSnapshot) -> str:
        payload = json.dumps({
            "evidence_refs": sorted(state.evidence_refs),
            "known_state_refs": sorted(state.known_state_refs),
            "candidate_state_refs": sorted(state.candidate_state_refs),
            "negative_memory_refs": sorted(state.negative_memory_refs),
        }, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def from_state(
        cls,
        state: SAGEStateSnapshot,
        *,
        model_role: str,
        station: str = "[SAGE::C2::CHATGPT]",
        required_output_contract: str = "structured_sage_response_v1",
        policy_version: str = "sage-runtime-v1",
        agent_identity: str | None = None,
    ) -> "SAGERuntimeEnvelope":
        if not station.strip() or not model_role.strip() or not policy_version.strip():
            raise ValueError("station, model_role, and policy_version are required")
        return cls(
            station=station,
            model_role=model_role,
            state=state,
            required_output_contract=required_output_contract,
            policy_version=policy_version,
            state_digest=state.digest(),
            agent_identity=agent_identity or station,
            policy_digest=cls._policy_digest(station=station, model_role=model_role, policy_version=policy_version),
            provenance_digest=cls._provenance_digest(state),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state_digest"] = self.state.digest()
        return payload


@dataclass(frozen=True)
class SAGEActionProposal:
    action_type: str
    target: str
    parameters: dict[str, Any]
    justification: str


@dataclass(frozen=True)
class SAGEEpistemicState:
    confidence_level: str
    validated_facts: tuple[str, ...] = ()
    unverified_hypotheses: tuple[str, ...] = ()
    known_unknowns: tuple[str, ...] = ()


@dataclass(frozen=True)
class SAGEStructuredResponse:
    station: str
    reasoning_chain: tuple[str, ...]
    proposed_actions: tuple[SAGEActionProposal, ...]
    epistemic_state: SAGEEpistemicState
    evidence_refs: tuple[str, ...] = ()
    is_roleplay: bool = False
    violations: tuple[str, ...] = ()


class SAGEProtocolGovernor:
    """Enforces SAGE protocol compliance and anti-roleplay governance on model outputs."""
    ROLEPLAY_INDICATORS = ("as an ai", "in roleplay mode", "pretend that", "pretend you", "let's pretend", "imagine i am", "i will act as", "simulation mode", "virtual assistant persona", "character mode", "*nods*", "*smiles*", "*chuckles*")
    AUTHORITY_CLAIM_INDICATORS = ("i hereby authorize", "i authorize", "i have updated canonical state", "update canonical state", "state mutated directly", "granting execution permissions", "bypassing preflight check", "overriding spek governance")
    EVIDENCE_BYPASS_INDICATORS = ("ignore the evidence requirement", "ignore evidence requirement", "bypass evidence requirement", "without evidence requirement", "skip evidence validation")
    UNVERIFIED_REPOSITORY_INDICATORS = ("claim a github change happened", "commit pushed to origin", "pushed commit to github", "github change happened")

    @classmethod
    def validate_and_parse(cls, raw_output: str, required_station: str = "[SAGE::C2::CHATGPT]") -> SAGEStructuredResponse:
        violations: list[str] = []
        lower_output = raw_output.lower()
        is_roleplay = any(indicator in lower_output for indicator in cls.ROLEPLAY_INDICATORS)
        if is_roleplay:
            violations.append("Model output contains conversational roleplay indicators.")
        if any(indicator in lower_output for indicator in cls.AUTHORITY_CLAIM_INDICATORS):
            violations.append("Model output falsely claims authority to authorize or mutate canonical state.")
        if any(indicator in lower_output for indicator in cls.EVIDENCE_BYPASS_INDICATORS):
            violations.append("Model output attempts to ignore or bypass evidence requirement.")
        if any(indicator in lower_output for indicator in cls.UNVERIFIED_REPOSITORY_INDICATORS):
            violations.append("Model output claims repository or GitHub state change without verification receipt.")
        import re
        for match in re.findall(r"\[SAGE::[^\]]+\]", raw_output):
            if match != required_station:
                violations.append(f"Model output station identity mismatch: expected {required_station}, got {match}.")
        reasoning_chain: list[str] = []
        proposed_actions: list[SAGEActionProposal] = []
        evidence_refs: list[str] = []
        epistemic = SAGEEpistemicState(confidence_level="UNKNOWN")
        try:
            json_str = raw_output
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            parsed_data = json.loads(json_str)
            if isinstance(parsed_data, dict):
                actual_station = parsed_data.get("station")
                if actual_station is None:
                    violations.append("Model output is missing required SAGE station identity.")
                elif str(actual_station) != required_station:
                    violations.append(f"Model output station identity mismatch: expected {required_station}, got {actual_station}.")
                reasoning_chain = list(parsed_data.get("reasoning_chain", []))
                resp_text = parsed_data.get("response_text")
                if resp_text and not reasoning_chain:
                    reasoning_chain = [str(resp_text)]
                for act in parsed_data.get("proposed_actions", []):
                    if isinstance(act, dict):
                        proposed_actions.append(SAGEActionProposal(action_type=str(act.get("action_type", "UNKNOWN")), target=str(act.get("target", "UNKNOWN")), parameters=dict(act.get("parameters", {})), justification=str(act.get("justification", ""))))
                evidence_refs = list(parsed_data.get("evidence_refs", []))
                if any(act.action_type.lower() in {"deployment", "mutation", "completion", "execution"} for act in proposed_actions) and not evidence_refs:
                    violations.append("Completion or deployment claim has no verification receipt in evidence_refs.")
                raw_ep = parsed_data.get("epistemic_state", {})
                if isinstance(raw_ep, dict):
                    epistemic = SAGEEpistemicState(confidence_level=str(raw_ep.get("confidence_level", "UNKNOWN")), validated_facts=tuple(raw_ep.get("validated_facts", [])), unverified_hypotheses=tuple(raw_ep.get("unverified_hypotheses", [])), known_unknowns=tuple(raw_ep.get("known_unknowns", [])))
        except Exception:
            reasoning_chain = [raw_output.strip()]
        if not reasoning_chain and not proposed_actions:
            violations.append("Model output lacks structured SAGE reasoning or proposed actions.")
        return SAGEStructuredResponse(station=required_station, reasoning_chain=tuple(reasoning_chain), proposed_actions=tuple(proposed_actions), epistemic_state=epistemic, evidence_refs=tuple(evidence_refs), is_roleplay=is_roleplay, violations=tuple(violations))


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
    live_operation_receipt: LiveOperationReceipt | None = None
    station: str = ""
    policy_version: str = ""
    policy_digest: str = ""
    provenance_digest: str = ""


class ModelAdapter(Protocol):
    model_id: str
    station: str
    def invoke(self, envelope: SAGERuntimeEnvelope, task: str) -> ModelResponse: ...


class SAGERuntime:
    """Owns state-envelope construction and response reconciliation boundaries."""
    def __init__(self, state: SAGEStateSnapshot, *, policy_version: str = "sage-runtime-v1"):
        self.state = state
        self.policy_version = policy_version

    def envelope(self, model_role: str, *, station: str = "[SAGE::C2::CHATGPT]") -> SAGERuntimeEnvelope:
        return SAGERuntimeEnvelope.from_state(self.state, model_role=model_role, station=station, policy_version=self.policy_version)

    def reconcile(self, response: ModelResponse, *, expected_station: str | None = None, model_role: str | None = None) -> None:
        """Reject cross-agent, cross-policy, cross-provenance, and stale-state responses."""
        if response.instance_id != self.state.instance_id:
            raise ValueError("SAGE instance identity mismatch")
        if response.mission_id != self.state.mission_id:
            raise ValueError("SAGE mission identity mismatch")
        if response.session_id != self.state.session_id:
            raise ValueError("SAGE session identity mismatch")
        if response.input_state_digest != self.state.digest():
            raise ValueError("SAGE input state digest mismatch")
        if expected_station is None or model_role is None:
            return
        if response.station != expected_station:
            raise ValueError("SAGE station identity mismatch")
        if response.policy_version != self.policy_version:
            raise ValueError("SAGE policy version mismatch")
        expected_policy_digest = SAGERuntimeEnvelope._policy_digest(station=expected_station, model_role=model_role, policy_version=self.policy_version)
        if response.policy_digest != expected_policy_digest:
            raise ValueError("SAGE policy context digest mismatch")
        if response.provenance_digest != SAGERuntimeEnvelope._provenance_digest(self.state):
            raise ValueError("SAGE provenance context digest mismatch")
        if response.structured_response is not None and response.structured_response.station != expected_station:
            raise ValueError("SAGE structured response station mismatch")

    def invoke(self, adapter: ModelAdapter, task: str, *, model_role: str, live_capability: LiveCapability | None = None) -> ModelResponse:
        decision = classify_directive(task)
        receipt: LiveOperationReceipt | None = None
        if decision.requires_live_verification:
            if live_capability is None:
                raise ValueError("C2 live verification required, but no connected live capability was provided.")
            receipt = execute_live_capability(live_capability, operation="live_verification", task=task)
        expected_station = getattr(adapter, "station", "")
        if not expected_station:
            raise ValueError("governed adapter must declare a station identity")
        response = adapter.invoke(self.envelope(model_role, station=expected_station), task)
        if receipt is not None:
            evidence_refs = tuple(dict.fromkeys((*response.evidence_refs, receipt.receipt_hash)))
            response = replace(response, evidence_refs=evidence_refs, live_operation_receipt=receipt)
            validate_report_claims(receipt=receipt, claim=str(response.raw_output), expected_target_resource=receipt.target_resource, evidence_refs=evidence_refs)
        self.reconcile(response, expected_station=expected_station, model_role=model_role)
        return response
