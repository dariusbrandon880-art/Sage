"""Core data models for SAGE Autonomous Continuity Runtime."""

import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence levels for memory objects."""

    HYPOTHESIS = "hypothesis"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class DecisionType(str, Enum):
    """Types of decisions tracked in SAGE."""

    ARCHITECTURAL = "architectural"
    TECHNICAL = "technical"
    PROCESS = "process"
    STRATEGIC = "strategic"


class KnowledgeState(str, Enum):
    """States of knowledge entry in master archive."""

    HYPOTHESIS = "hypothesis"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class MemoryObject(BaseModel):
    """A single memory object with content, confidence level and metadata."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    object_type: str
    content: Dict[str, Any]
    tags: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HYPOTHESIS
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArchiveEntry(BaseModel):
    """Master Archive Entry representing validated knowledge."""

    id: str
    title: str
    tags: List[str] = Field(default_factory=list)
    knowledge_state: KnowledgeState = KnowledgeState.ARCHIVED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validation_timestamp: Optional[datetime] = None
    decision_history: List[str] = Field(default_factory=list)
    lineage: List[str] = Field(default_factory=list)
    content: Dict[str, Any] = Field(default_factory=dict)


class DecisionEntry(BaseModel):
    """Decision record tracking the rationale and evidence for system choices."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: DecisionType
    description: str
    rationale: str
    evidence: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    outcome: Optional[str] = None


class RuntimeState(BaseModel):
    """Runtime state representation."""

    current_objective: Optional[str] = None
    active_task: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
