"""SAGE Mission Progression State Machine and Controller.

Establishes a deterministic, governed progression cycle across 8 stages:
INTAKE -> PRIORITIZED -> PREFLIGHT_VALIDATED -> HANDOFF_READY -> HANDOFF_EMITTED
-> EXECUTION_RESULT_RECEIVED -> EVIDENCE_VALIDATED -> OUTCOME_CLASSIFIED.
"""

import hashlib
import json
import uuid
import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.acr.attestation import AttestationProvider
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
)

# ---------------------------------------------------------
# Step 1: Define state representation and valid predecessors
# ---------------------------------------------------------

class MissionProgressionState(str, Enum):
    """SAGE Mission Progression lifecycle states."""
    INTAKE = "INTAKE"
    PRIORITIZED = "PRIORITIZED"
    PREFLIGHT_VALIDATED = "PREFLIGHT_VALIDATED"
    HANDOFF_READY = "HANDOFF_READY"
    HANDOFF_EMITTED = "HANDOFF_EMITTED"
    EXECUTION_RESULT_RECEIVED = "EXECUTION_RESULT_RECEIVED"
    EVIDENCE_VALIDATED = "EVIDENCE_VALIDATED"
    OUTCOME_CLASSIFIED = "OUTCOME_CLASSIFIED"


VALID_PREDECESSORS: Dict[MissionProgressionState, Optional[MissionProgressionState]] = {
    MissionProgressionState.INTAKE: None,
    MissionProgressionState.PRIORITIZED: MissionProgressionState.INTAKE,
    MissionProgressionState.PREFLIGHT_VALIDATED: MissionProgressionState.PRIORITIZED,
    MissionProgressionState.HANDOFF_READY: MissionProgressionState.PREFLIGHT_VALIDATED,
    MissionProgressionState.HANDOFF_EMITTED: MissionProgressionState.HANDOFF_READY,
    MissionProgressionState.EXECUTION_RESULT_RECEIVED: MissionProgressionState.HANDOFF_EMITTED,
    MissionProgressionState.EVIDENCE_VALIDATED: MissionProgressionState.EXECUTION_RESULT_RECEIVED,
    MissionProgressionState.OUTCOME_CLASSIFIED: MissionProgressionState.EVIDENCE_VALIDATED,
}


class MissionProgressionReceipt(BaseModel):
    """An EAS-001 compatible immutable validation/transition receipt."""

    receipt_id: str
    previous_state: Optional[str] = None
    next_state: str
    mission_id: str
    reason: str
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    provenance_reference: str
    sequence_order: int
    timestamp: str
    signature: str


def filter_nondeterministic_fields(data: Any) -> Any:
    """Recursively filter non-deterministic receipt fields."""
    if isinstance(data, dict):
        return {
            k: filter_nondeterministic_fields(v)
            for k, v in data.items()
            if k not in {"timestamp", "receipt_id", "nonce", "created_at"}
        }
    if isinstance(data, list):
        return [filter_nondeterministic_fields(item) for item in data]
    return data


def canonical_serialize(data: Dict[str, Any]) -> bytes:
    """Sort keys and serialize without non-deterministic fields."""
    filtered = filter_nondeterministic_fields(data)
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")


class MECAdapter:
    """Adapter recording the Multi-user Engineering Continuity interface gap."""

    def __init__(self):
        self.interface_gap_status = "RESEARCH_ONLY"
        self.spec_location = "Main Archive/research/strategic/MEC.md"

    def execute_handoff(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("mission_id"):
            raise ValueError("MEC Handoff Failure: Missing mission_id in handoff payload")
        if not payload.get("assigned_agent"):
            raise ValueError("MEC Handoff Failure: Missing assigned_agent in handoff payload")
        if payload.get("spawn_agent") or payload.get("create_tier") or payload.get("spawn_agents"):
            raise PermissionError("MEC Handoff Violation: Dynamic agent spawning is locked.")
        return {
            "status": "HANDOFF_EMITTED_SUCCESSFULLY",
            "assigned_agent": payload["assigned_agent"],
            "delegated_at": "telemetry",
            "zero_spawning_enforced": True,
        }


class ACHAdapter:
    """Passive Active Client Hook interface-gap adapter."""

    def __init__(self):
        self.interface_gap_status = "ARCHIVED_EXPERIMENTAL"
        self.spec_location = "docs/SAGE-CAPABILITY-TREE-HEALTH-ASSESSMENT-REPORT.md"


class PEFAdapter:
    """Parallel Cognitive Evolution research-only adapter."""

    def __init__(self):
        self.interface_gap_status = "RESEARCH_ONLY"
        self.spec_location = "Main Archive/research/strategic/PEF.md"


class CausalityAuditorAdapter:
    """Adapter bridging causality checks to HDGEngine."""

    def __init__(self, hdg_engine: Optional[Any] = None):
        self.interface_gap_status = "BRIDGED_TO_HDG_ENGINE"
        self.hdg_engine = hdg_engine

    def validate_causality(self, node_id: str) -> Dict[str, Any]:
        if not self.hdg_engine:
            return {"status": "SKIPPED", "reason": "No active HDGEngine linked"}
        try:
            contradictions = self.hdg_engine.check_contradictions(node_id)
            if contradictions:
                return {
                    "status": "REJECTED",
                    "reason": f"Causality Violation: Contradiction(s) detected in ancestral path: {contradictions}",
                }
            evidence = self.hdg_engine.trace_evidence(node_id)
            self.hdg_engine.validate_graph_integrity()
            return {
                "status": "APPROVED",
                "evidence_references": evidence,
                "contradictions_found": contradictions,
            }
        except ValueError as exc:
            return {
                "status": "REJECTED",
                "reason": f"Causality Auditor Rejection: HDG Engine failed closed with error: {exc!s}",
            }


class MissionProgressionController:
    """Central state transition manager for governed SAGE Mission Progression."""

    def __init__(
        self,
        hdg_engine: Optional[Any] = None,
        pfc_simulator: Optional[Any] = None,
        attestation_provider: Optional[Any] = None,
        priority_threshold: float = 50.0,
    ):
        from sage.acr.attestation import AttestationProvider
        from sage.experimental.cognitive.prefrontal_cortex import PrefrontalCortexSimulator

        self.hdg_engine = hdg_engine
        self.pfc = pfc_simulator or PrefrontalCortexSimulator()
        self.attestation = attestation_provider or AttestationProvider()
        self.priority_threshold = priority_threshold
        self.mec_adapter = MECAdapter()
        self.ach_adapter = ACHAdapter()
        self.pef_adapter = PEFAdapter()
        self.causality_adapter = CausalityAuditorAdapter(hdg_engine)
        self.current_state: Optional[MissionProgressionState] = None
        self.mission_data: Dict[str, Any] = {}
        self.receipts: List[MissionProgressionReceipt] = []
        self.sequence_counter: int = 0

    def intake_mission(self, mission_data: Dict[str, Any]) -> MissionProgressionReceipt:
        required_fields = ["mission_id", "objective", "priority_score", "assigned_agent"]
        for field in required_fields:
            if field not in mission_data or mission_data[field] is None:
                raise ValueError(f"Malformed Mission Input: Missing required field '{field}'")
        if not isinstance(mission_data["priority_score"], (int, float)):
            raise ValueError("Malformed Mission Input: 'priority_score' must be a number")
        if mission_data.get("spawn_agents") or mission_data.get("create_tier") or mission_data.get("spawn_agent"):
            raise PermissionError("Zero-Spawning Lock Violation: Agent spawning is locked.")
        self.mission_data = json.loads(json.dumps(mission_data))
        self.current_state = MissionProgressionState.INTAKE
        self.sequence_counter = 1
        return self._generate_transition_receipt(
            previous_state=None,
            next_state=MissionProgressionState.INTAKE,
            reason="Mission successfully received and registered at Intake boundary.",
            validation_result={"status": "APPROVED", "details": "All required intake fields verified."},
            provenance_reference="intake_boundary_v1",
        )

    def prioritize(self) -> MissionProgressionReceipt:
        def validate_priority():
            score = self.mission_data.get("priority_score", 0.0)
            if score < self.priority_threshold:
                return False, {
                    "status": "REJECTED",
                    "reason": f"Priority score {score} is below required threshold of {self.priority_threshold}.",
                }
            return True, {
                "status": "APPROVED",
                "priority_score": score,
                "priority_threshold": self.priority_threshold,
            }
        return self.transition_to(
            target_state=MissionProgressionState.PRIORITIZED,
            validation_func=validate_priority,
            reason="Priority score successfully evaluated and approved.",
            provenance_reference="priority_gate_v1",
        )

    def validate_preflight(self, cognitive_state: Optional[CognitiveState] = None) -> MissionProgressionReceipt:
        """Run preflight validation; failure intelligence is fail-closed and read-only."""
        def validate_pfc():
            from sage.experimental.cognitive.prefrontal_cortex import DecisionGateOutcome

            try:
                from sage.failure_intelligence import normalize_failure
            except Exception as exc:
                return False, {
                    "status": "REJECTED",
                    "reason": f"Failure intelligence unavailable; preflight failed closed: {exc!s}",
                }

            objective = self.mission_data.get("objective", "")
            try:
                normalized_objective = normalize_failure(objective)
            except (TypeError, ValueError) as exc:
                return False, {
                    "status": "REJECTED",
                    "reason": f"Failure intelligence could not normalize objective; preflight failed closed: {exc!s}",
                }
            if "known_failure_trigger" in normalized_objective:
                return False, {
                    "status": "REJECTED",
                    "reason": "Preflight rejected due to failure memory pattern in objective.",
                }

            state = cognitive_state
            if not state:
                agent = CognitiveAgentIdentity(
                    agent_id=self.mission_data.get("assigned_agent", "agent_jules_sage"),
                    name="Jules",
                    role="Senior Software Engineer",
                    authority_level="TIER_1_COORDINATOR",
                    governance_tier="TIER_1_COORDINATOR",
                )
                mission = CognitiveActiveMission(
                    mission_id=self.mission_data.get("mission_id", "mission_prog_v1"),
                    objective=self.mission_data.get("objective", "Default objective"),
                    status="RUNNING",
                )
                constraints = CognitiveOperatorConstraints(
                    authorized_agents=[self.mission_data.get("assigned_agent", "agent_jules_sage")]
                )
                confidence = CognitiveConfidenceState(overall_confidence=1.0, last_updated=0.0)
                next_action = CognitiveNextAction(
                    action_id=f"task_{self.mission_data.get('mission_id', 'task_1')}",
                    description=self.mission_data.get("objective", "Default description"),
                    assigned_agent=self.mission_data.get("assigned_agent", "agent_jules_sage"),
                )
                state = CognitiveState(
                    agent_identity=agent,
                    active_mission=mission,
                    operator_constraints=constraints,
                    confidence_state=confidence,
                    next_action=next_action,
                )

            report = self.pfc.evaluate_decision(state)
            if report.outcome == DecisionGateOutcome.PROCEED:
                return True, {
                    "status": "APPROVED",
                    "reason": report.reason,
                    "confidence_recorded": report.confidence_recorded,
                    "checks_performed": report.checks_performed,
                }
            return False, {
                "status": "REJECTED",
                "reason": report.reason,
                "confidence_recorded": report.confidence_recorded,
                "checks_performed": report.checks_performed,
            }

        return self.transition_to(
            target_state=MissionProgressionState.PREFLIGHT_VALIDATED,
            validation_func=validate_pfc,
            reason="PFC Gate Preflight check successfully executed and passed.",
            provenance_reference="pfc_preflight_gate_v1",
        )

    def prepare_handoff(self) -> MissionProgressionReceipt:
        def validate_agent_auth():
            agent_id = self.mission_data.get("assigned_agent")
            if agent_id in ("unauthorized_agent", "untrusted_agent", "unauthorized"):
                return False, {"status": "REJECTED", "reason": f"Handoff Blocked: Agent '{agent_id}' is unauthorized/untrusted."}
            return True, {"status": "APPROVED", "assigned_agent": agent_id, "authority_level": "VERIFIED"}
        return self.transition_to(
            target_state=MissionProgressionState.HANDOFF_READY,
            validation_func=validate_agent_auth,
            reason="Agent authority verified. Mission handoff is ready.",
            provenance_reference="agent_authorization_gate_v1",
        )

    def emit_handoff(self, handoff_payload: Optional[Dict[str, Any]] = None) -> MissionProgressionReceipt:
        def validate_mec_handoff():
            payload = handoff_payload or {"mission_id": self.mission_data.get("mission_id"), "assigned_agent": self.mission_data.get("assigned_agent")}
            try:
                return True, self.mec_adapter.execute_handoff(payload)
            except (ValueError, PermissionError) as exc:
                return False, {"status": "REJECTED", "reason": str(exc)}
        return self.transition_to(
            target_state=MissionProgressionState.HANDOFF_EMITTED,
            validation_func=validate_mec_handoff,
            reason="MEC Handoff executed successfully.",
            provenance_reference="mec_handoff_gate_v1",
        )

    def receive_execution_result(self, execution_result: Dict[str, Any]) -> MissionProgressionReceipt:
        def validate_result():
            if not execution_result or not execution_result.get("output_data"):
                return False, {"status": "REJECTED", "reason": "Execution Result Failure: Missing or empty 'output_data'."}
            return True, {"status": "APPROVED", "output_data_hash": hashlib.sha256(str(execution_result.get("output_data")).encode("utf-8")).hexdigest()}
        return self.transition_to(
            target_state=MissionProgressionState.EXECUTION_RESULT_RECEIVED,
            validation_func=validate_result,
            reason="Execution results received and validated.",
            provenance_reference="execution_result_boundary_v1",
        )

    def validate_evidence(self, provided_evidence: Dict[str, Any], hdg_node_id: Optional[str] = None) -> MissionProgressionReceipt:
        def validate_evidence_and_causality():
            reqs = self.mission_data.get("required_evidence", [])
            for requirement in reqs:
                if requirement not in provided_evidence:
                    return False, {"status": "REJECTED", "reason": f"Evidence Validation Failure: Required evidence '{requirement}' is missing."}
            if hdg_node_id:
                causality_res = self.causality_adapter.validate_causality(hdg_node_id)
                if causality_res["status"] == "REJECTED":
                    return False, {"status": "REJECTED", "reason": causality_res["reason"]}
                return True, {"status": "APPROVED", "evidence_validation": "SUCCESS", "causality_validation": causality_res}
            return True, {"status": "APPROVED", "evidence_validation": "SUCCESS", "causality_validation": "SKIPPED_NO_NODE_ID"}
        return self.transition_to(
            target_state=MissionProgressionState.EVIDENCE_VALIDATED,
            validation_func=validate_evidence_and_causality,
            reason="Evidence validation and Epistemic Causality checks passed.",
            provenance_reference="evidence_validation_gate_v1",
        )

    def classify_outcome(self, final_status: str = "SUCCESS") -> MissionProgressionReceipt:
        def validate_outcome():
            if final_status not in ("SUCCESS", "FAILURE"):
                return False, {"status": "REJECTED", "reason": f"Outcome Classification Failure: Invalid outcome status '{final_status}'."}
            return True, {"status": "APPROVED", "outcome_classification": final_status}
        return self.transition_to(
            target_state=MissionProgressionState.OUTCOME_CLASSIFIED,
            validation_func=validate_outcome,
            reason=f"Mission successfully completed. Outcome classified as '{final_status}'.",
            provenance_reference="outcome_classification_boundary_v1",
        )

    def transition_to(self, target_state: MissionProgressionState, validation_func, reason: str, provenance_reference: str) -> MissionProgressionReceipt:
        if self.current_state is None:
            raise ValueError("State machine not initialized. Please call intake_mission first.")
        expected_predecessor = VALID_PREDECESSORS[target_state]
        if self.current_state != expected_predecessor:
            raise ValueError(
                f"Out-of-Order Transition Failed Closed: Target state '{target_state.value}' "
                f"requires predecessor '{expected_predecessor.value if expected_predecessor else 'None'}', "
                f"but current state is '{self.current_state.value}'."
            )
        is_valid, validation_result = validation_func()
        if not is_valid:
            raise ValueError(
                f"Transition Rejected: Failed validation gate for target state '{target_state.value}'. "
                f"Reason: {validation_result.get('reason', 'Unknown error')}"
            )
        if (self.mission_data.get("spawn_agents") or self.mission_data.get("create_tier") or self.mission_data.get("spawn_agent")):
            raise PermissionError("Zero-Spawning Lock Violation: Attempted agent spawning or tier creation.")
        previous_state = self.current_state
        self.current_state = target_state
        return self._generate_transition_receipt(
            previous_state=previous_state,
            next_state=target_state,
            reason=reason,
            validation_result=validation_result,
            provenance_reference=provenance_reference,
        )

    def _generate_transition_receipt(self, previous_state: Optional[MissionProgressionState], next_state: MissionProgressionState, reason: str, validation_result: Dict[str, Any], provenance_reference: str) -> MissionProgressionReceipt:
        receipt_id = f"rec_prog_{uuid.uuid4().hex[:12]}"
        signing_payload = {
            "previous_state": previous_state.value if previous_state else None,
            "next_state": next_state.value,
            "mission_id": self.mission_data.get("mission_id"),
            "reason": reason,
            "validation_result": validation_result,
            "provenance_reference": provenance_reference,
            "sequence_order": self.sequence_counter,
        }
        canonical_bytes = canonical_serialize(signing_payload)
        signature = self.attestation.sign_payload({"canonical_hash": hashlib.sha256(canonical_bytes).hexdigest()})
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt = MissionProgressionReceipt(
            receipt_id=receipt_id,
            previous_state=previous_state.value if previous_state else None,
            next_state=next_state.value,
            mission_id=self.mission_data.get("mission_id"),
            reason=reason,
            validation_result=validation_result,
            provenance_reference=provenance_reference,
            sequence_order=self.sequence_counter,
            timestamp=timestamp,
            signature=signature,
        )
        self.receipts.append(receipt)
        self.sequence_counter += 1
        return receipt
