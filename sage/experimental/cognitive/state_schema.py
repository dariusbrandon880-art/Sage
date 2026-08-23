"""Cognitive State Schema for SAGE Cognitive Kernel."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CognitiveAgentIdentity(BaseModel):
    """Immutable representation of agent identity and role-based authority."""

    agent_id: str
    name: str
    role: str
    authority_level: str  # e.g., TIER_1_COORDINATOR, TIER_2_EXECUTION, TIER_3_REVIEW
    governance_tier: str


class CognitiveActiveMission(BaseModel):
    """Representation of the active mission objective."""

    mission_id: str
    objective: str
    milestones: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED


class CognitiveValidatedFact(BaseModel):
    """Validated facts supporting context rehydration and session continuity."""

    fact_id: str
    statement: str
    evidence_references: List[str] = Field(default_factory=list)
    confidence_score: float = 1.0


class CognitiveCompletedMilestone(BaseModel):
    """Completed milestones to protect against reopening or duplication."""

    milestone_id: str
    completed_at: float
    evidence_hash: str
    reopened_count: int = 0


class CognitiveForbiddenRegression(BaseModel):
    """Forbidden regressions preventing state loop repetition or unauthorized operations."""

    regression_id: str
    description: str
    restricted_actions: List[str] = Field(default_factory=list)
    blocked_states: List[str] = Field(default_factory=list)


class CognitiveOperatorConstraints(BaseModel):
    """Explicit boundaries and constraints defined by the operator."""

    permitted_paths: List[str] = Field(default_factory=list)
    forbidden_paths: List[str] = Field(default_factory=list)
    requires_approval: bool = True
    max_consecutive_failures: int = 3
    authorized_agents: List[str] = Field(default_factory=list)


class CognitiveConfidenceState(BaseModel):
    """Current confidence state of the kernel runtime."""

    overall_confidence: float = 1.0
    last_updated: float
    notes: Optional[str] = None


class CognitiveNextAction(BaseModel):
    """Proposed next action to evaluate."""

    action_id: str
    description: str
    assigned_agent: str
    required_evidence: List[str] = Field(default_factory=list)


class CognitiveState(BaseModel):
    """Aggregated high-fidelity Cognitive State representation."""

    agent_identity: CognitiveAgentIdentity
    active_mission: CognitiveActiveMission
    validated_facts: List[CognitiveValidatedFact] = Field(default_factory=list)
    completed_milestones: List[CognitiveCompletedMilestone] = Field(default_factory=list)
    forbidden_regressions: List[CognitiveForbiddenRegression] = Field(default_factory=list)
    operator_constraints: CognitiveOperatorConstraints
    confidence_state: CognitiveConfidenceState
    next_action: Optional[CognitiveNextAction] = None


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
    c2_status: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
