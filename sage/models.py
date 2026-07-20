"""Core data models for SAGE - enums, schemas, and persistence objects."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """SAGE memory confidence levels."""
    HYPOTHESIS = "hypothesis"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class DecisionType(str, Enum):
    """SAGE decision types."""
    ARCHITECTURE = "architecture"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    DESIGN = "design"


class KnowledgeState(str, Enum):
    """SAGE knowledge states in master archive."""
    HYPOTHESIS = "hypothesis"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class MemoryObject(BaseModel):
    """Schema for a SAGE memory/knowledge object in the lab/memory store."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    object_type: str
    content: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HYPOTHESIS
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ArchiveEntry(BaseModel):
    """Schema for permanent knowledge stored in the Master Archive."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    validation_timestamp: Optional[datetime] = None
    knowledge_state: KnowledgeState = KnowledgeState.ARCHIVED
    decision_history: List[str] = Field(default_factory=list)
    lineage: Dict[str, Any] = Field(default_factory=dict)


class RuntimeState(BaseModel):
    """Schema for tracking current SAGE operational state."""
    current_objective: Optional[str] = None
    active_task: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class DecisionEntry(BaseModel):
    """Schema for tracking engineering and operational decisions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: DecisionType
    description: str
    rationale: str
    evidence: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    outcome: Optional[str] = None
    chain: List[str] = Field(default_factory=list)
    lessons: List[str] = Field(default_factory=list)
