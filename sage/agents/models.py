"""Pydantic models and Enums for SAGE Agent Workflow Layer v1."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AgentRole(str, Enum):
    """Governed SAGE agent roles defining default authorization tiers."""
    CONTRIBUTOR = "CONTRIBUTOR"
    OBSERVER = "OBSERVER"
    ENFORCER = "ENFORCER"
    VALIDATOR = "VALIDATOR"


class MemoryAccess(str, Enum):
    """Memory layer read/write capability limits."""
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    RESTRICTED = "RESTRICTED"


class ValidationAuthority(str, Enum):
    """Authorized validation capability levels for SPEK promotion gates."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AgentTaskState(str, Enum):
    """Lifecycle state tracking for governed agent executions."""
    PENDING = "PENDING"
    ROUTED = "ROUTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class AgentIdentity(BaseModel):
    """Schema representing a governed SAGE agent's identity and permissions."""

    agent_id: str
    name: str
    role: AgentRole = AgentRole.CONTRIBUTOR
    memory_access: MemoryAccess = MemoryAccess.READ_ONLY
    validation_authority: ValidationAuthority = ValidationAuthority.LOW
    signature_key: str = "sage_agent_unsigned_key"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PermissionBoundary(BaseModel):
    """Schema defining strict allowed/prohibited execution bounds for SAGE agents."""

    agent_id: str
    allowed_paths: List[str] = Field(default_factory=list)
    prohibited_paths: List[str] = Field(default_factory=list)
    prohibited_actions: List[str] = Field(default_factory=list)
    allowed_modules: List[str] = Field(default_factory=list)


class TaskEvent(BaseModel):
    """SAGE agent task execution history step."""

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str
    actor: str
    details: str
    status: AgentTaskState


class AgentTask(BaseModel):
    """Schema representing a structured, governed task within SAGE Agent workflows."""

    task_id: str
    objective_id: str
    title: str
    assigned_agent_id: Optional[str] = None
    state: AgentTaskState = AgentTaskState.PENDING
    history: List[TaskEvent] = Field(default_factory=list)
    validation_records: List[str] = Field(default_factory=list)  # Associated SPEK receipt hashes
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
