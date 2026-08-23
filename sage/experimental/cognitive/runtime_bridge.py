"""SAGE Runtime + Cognitive Integration Bridge.

Unifies C2 Operating Contract, runtime governance, persistent cognitive state,
and canonical progression receipts into one continuous execution loop.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from sage.c2.progression_receipt_serializer import MissionProgressionReceiptSerializer
from sage.experimental.cognitive.persistence import (
    CognitivePersistenceError,
    persist,
    rehydrate,
)
from sage.experimental.cognitive.prefrontal_cortex import (
    DecisionGateOutcome,
    PFCDecisionReport,
    PrefrontalCortexSimulator,
)
from sage.experimental.cognitive.state_schema import (
    CognitiveActiveMission,
    CognitiveAgentIdentity,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
    CognitiveState,
)
from sage.models import (
    ArchiveEntry,
    ArchiveIntelligence,
    ConfidenceTracker,
    ExternalSessionPayload,
    KnowledgeLineage,
    KnowledgeState,
    ValidationRecord,
)

CANONICAL_AUTHORIZED_AGENTS = [
    "MISSION_CONTROL",
    "MISSION_DIRECTOR",
    "INTEL_STATION",
    "ENGINEERING_FLIGHT",
]


class CognitiveProgressionReceipt(BaseModel):
    """Data model for canonical cognitive progression receipt serialization."""

    receipt_id: str = Field(default_factory=lambda: f"rcpt_cog_{uuid.uuid4().hex[:8]}")
    action_id: str
    mission_id: str
    pfc_outcome: str
    cognitive_digest: str
    c2_identity: str = "SAGE_C2_COMMAND_CENTER"
    c2_status: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CognitiveCycleResult(BaseModel):
    """Structured report returned from a governed runtime cognitive cycle."""

    success: bool
    action_id: str
    mission_id: str
    pfc_outcome: DecisionGateOutcome
    pfc_reason: str
    cognitive_state_digest: str | None = None
    progression_receipt_digest: str | None = None
    archive_entry_id: str | None = None
    c2_context: dict[str, Any] = Field(default_factory=dict)


class RuntimeCognitiveBridge:
    """Continuous execution loop connecting runtime governance and cognitive executive control."""

    def __init__(self, runtime: Any):
        self.runtime = runtime
        self.pfc_simulator = PrefrontalCortexSimulator()
        self.receipt_serializer = MissionProgressionReceiptSerializer()

    def get_c2_context(self, session_id: str | None = None) -> dict[str, Any]:
        """Rehydrate complete C2 operating context for multi-model AI adapters."""
        status = self.runtime.get_status()
        team_ctx = {}
        try:
            from sage.agent_presence import get_team_context
            team_ctx = get_team_context()
        except Exception:
            pass

        return {
            "c2_identity": "SAGE_C2_COMMAND_CENTER",
            "session_id": session_id or (self.runtime.context.session_id if getattr(self.runtime, "context", None) else None),
            "rehydrated": getattr(getattr(self.runtime, "c2_boot_result", None), "rehydrated", True),
            "master_archive_authority": True,
            "active_objective": status.get("current_objective"),
            "active_task": status.get("active_task"),
            "blockers": status.get("blockers", []),
            "c2_status": status.get("c2_status", {}),
            "team_context": team_ctx,
            "governance_status": "ACTIVE",
        }

    def execute_cognitive_cycle(
        self,
        action_id: str,
        description: str,
        target: str = "workspace",
        parameters: dict[str, Any] | None = None,
        required_evidence: list[str] | None = None,
        agent_id: str = "MISSION_CONTROL",
        agent_name: str = "C2 Mission Control",
        authority_level: str = "TIER_1_COORDINATOR",
        governance_tier: str = "GOVERNED",
    ) -> CognitiveCycleResult:
        """Execute one continuous governed cognitive loop.

        Sequence:
        1. Rehydrate C2 Operating Contract context.
        2. Rehydrate / construct persistent CognitiveState with proposed action.
        3. Evaluate action against Prefrontal Cortex (PFC) executive gates.
        4. Halt on BLOCK and record runtime blocker; otherwise proceed to runtime governance.
        5. Persist digest-verified CognitiveState to disk.
        6. Produce canonical MissionProgressionReceipt and store in Master Archive & Memory.
        """
        # 1. Rehydrate C2 Operating Contract
        session_id = f"session_cog_{uuid.uuid4().hex[:8]}"
        c2_context = self.get_c2_context(session_id)

        mission_id = f"mission_{action_id}"
        active_objective = (
            self.runtime.current_state.current_objective
            or description
        )

        # 2. Rehydrate or construct persistent CognitiveState
        cognitive_dir = Path(self.runtime.workspace_path) / "cognitive"
        cognitive_state_path = cognitive_dir / "active_state.json"

        cognitive_state: CognitiveState | None = None
        if cognitive_state_path.exists():
            try:
                cognitive_state = rehydrate(cognitive_state_path)
            except CognitivePersistenceError:
                cognitive_state = None

        proposed_action = CognitiveNextAction(
            action_id=action_id,
            description=description,
            assigned_agent=agent_id,
            required_evidence=required_evidence or [],
        )

        now_ts = datetime.now(timezone.utc).timestamp()

        if cognitive_state is None:
            agent = CognitiveAgentIdentity(
                agent_id=agent_id,
                name=agent_name,
                role="COORDINATOR",
                authority_level=authority_level,
                governance_tier=governance_tier,
            )
            mission = CognitiveActiveMission(
                mission_id=mission_id,
                objective=active_objective,
                status="RUNNING",
            )
            cognitive_state = CognitiveState(
                agent_identity=agent,
                active_mission=mission,
                next_action=proposed_action,
                confidence_state=CognitiveConfidenceState(
                    overall_confidence=0.9,
                    last_updated=now_ts,
                ),
                operator_constraints=CognitiveOperatorConstraints(
                    authorized_agents=list(CANONICAL_AUTHORIZED_AGENTS),
                ),
            )
        else:
            cognitive_state.next_action = proposed_action
            cognitive_state.agent_identity = CognitiveAgentIdentity(
                agent_id=agent_id,
                name=agent_name,
                role="COORDINATOR",
                authority_level=authority_level,
                governance_tier=governance_tier,
            )
            cognitive_state.active_mission.objective = active_objective

        # 3. PFC Executive Gate Evaluation
        pfc_report: PFCDecisionReport = self.pfc_simulator.evaluate_decision(cognitive_state)

        if pfc_report.outcome == DecisionGateOutcome.BLOCK:
            blocker_msg = f"PFC_BLOCK [{action_id}]: {pfc_report.reason}"
            self.runtime.add_blocker(blocker_msg)
            return CognitiveCycleResult(
                success=False,
                action_id=action_id,
                mission_id=mission_id,
                pfc_outcome=pfc_report.outcome,
                pfc_reason=pfc_report.reason,
                c2_context=c2_context,
            )

        # 4. Runtime Governance Gate Check (CognitiveHypervisor / ExternalAuthorityGate)
        if hasattr(self.runtime, "authority_gate"):
            try:
                auth_ok = self.runtime.authority_gate.verify_authority(
                    agent_id=agent_id,
                    governance_tier=governance_tier,
                )
                if not auth_ok:
                    reason = f"Authority gate rejected agent '{agent_id}' with governance tier '{governance_tier}'"
                    self.runtime.add_blocker(f"AUTH_GATE_BLOCK: {reason}")
                    return CognitiveCycleResult(
                        success=False,
                        action_id=action_id,
                        mission_id=mission_id,
                        pfc_outcome=DecisionGateOutcome.BLOCK,
                        pfc_reason=reason,
                        c2_context=c2_context,
                    )
            except Exception:
                pass

        # 5. Persist Digest-Verified CognitiveState
        cognitive_state_digest = persist(cognitive_state_path, cognitive_state)

        # 6. Canonical Progression Receipt Serialization & Master Archive Storage
        receipt = CognitiveProgressionReceipt(
            action_id=action_id,
            mission_id=mission_id,
            pfc_outcome=pfc_report.outcome.value,
            cognitive_digest=cognitive_state_digest,
            c2_status=c2_context.get("c2_status", {}),
        )
        receipt_digest = self.receipt_serializer.digest(receipt)

        archive_entry_id = f"ARCHIVE-COG-{action_id}"
        val_record = ValidationRecord(
            validated_by="RuntimeCognitiveBridge",
            rules_applied=[
                "c2_rehydration_check",
                "prefrontal_cortex_executive_gate",
                "cognitive_state_digest_verification",
                "canonical_progression_receipt_serialization",
            ],
            success=True,
        )
        lineage = KnowledgeLineage(
            source=f"cognitive_cycle_{action_id}",
            validation_record=val_record,
            metadata={
                "action_id": action_id,
                "mission_id": mission_id,
                "pfc_outcome": pfc_report.outcome.value,
                "cognitive_state_digest": cognitive_state_digest,
                "progression_receipt_digest": receipt_digest,
            },
        )
        confidence = ConfidenceTracker(
            confidence_level=1.0,
            validation_status="archived",
            evidence_references=[str(cognitive_state_path)],
        )

        archive_entry = ArchiveEntry(
            id=archive_entry_id,
            title=f"Cognitive Execution Progression Receipt: {action_id}",
            tags=["c2_progression", "cognitive_cycle", "pfc_verified", "runtime_bridge"],
            knowledge_state=KnowledgeState.ARCHIVED,
            content={
                "receipt": receipt.model_dump(),
                "receipt_digest": receipt_digest,
                "cognitive_digest": cognitive_state_digest,
                "pfc_checks": pfc_report.checks_performed,
                "pfc_reason": pfc_report.reason,
                "c2_context": c2_context,
            },
            intelligence=ArchiveIntelligence(lineage=lineage, confidence=confidence),
        )
        self.runtime.archive.promote_to_archive(archive_entry)

        # Ingest into runtime continuity bridge for memory tracking
        payload = ExternalSessionPayload(
            session_id=session_id,
            objective=active_objective,
            task=f"Cognitive Cycle Execution: {description[:50]}...",
            memories=[
                {
                    "id": f"cog_cycle_{uuid.uuid4().hex[:8]}",
                    "object_type": "cognitive_cycle_execution",
                    "content": {
                        "action_id": action_id,
                        "description": description,
                        "pfc_outcome": pfc_report.outcome.value,
                        "pfc_reason": pfc_report.reason,
                        "cognitive_digest": cognitive_state_digest,
                        "receipt_digest": receipt_digest,
                        "archive_entry_id": archive_entry_id,
                    },
                    "tags": ["cognitive_cycle", "c2_immersion", "pfc_verified"],
                    "confidence": "validated",
                }
            ],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)

        return CognitiveCycleResult(
            success=True,
            action_id=action_id,
            mission_id=mission_id,
            pfc_outcome=pfc_report.outcome,
            pfc_reason=pfc_report.reason,
            cognitive_state_digest=cognitive_state_digest,
            progression_receipt_digest=receipt_digest,
            archive_entry_id=archive_entry_id,
            c2_context=c2_context,
        )
