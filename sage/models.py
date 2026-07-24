"""Core data models for SAGE Autonomous Continuity Runtime."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

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
    content: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HYPOTHESIS
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# SAGE Archive Intelligence Models
class ValidationRecord(BaseModel):
    """Details about the validation process that promoted the knowledge."""

    validated_by: str = "ValidationSystem"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rules_applied: list[str] = Field(default_factory=list)
    success: bool = True


class KnowledgeLineage(BaseModel):
    """Lineage tracking the origin and history of archived knowledge."""

    source: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validation_record: ValidationRecord | None = None
    dependent_decisions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewHistoryItem(BaseModel):
    """A record of a review of this knowledge."""

    reviewer: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str
    notes: str | None = None


class ConfidenceTracker(BaseModel):
    """Tracking details of confidence, validation, and reviews."""

    confidence_level: float = 1.0  # Explicit assignment (0.0 to 1.0)
    validation_status: str = "archived"  # e.g., hypothesis, validated, archived
    evidence_references: list[str] = Field(default_factory=list)
    review_history: list[ReviewHistoryItem] = Field(default_factory=list)


class KnowledgeRelationship(BaseModel):
    """Represents a connection between two archive items."""

    source_id: str
    target_id: str
    relationship_type: (
        str  # e.g., "related_to", "depends_on", "derived_from", "replaces", "validated_by"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionConnection(BaseModel):
    """Connection between an architecture decision and archive records."""

    decision_id: str
    affected_components: list[str] = Field(default_factory=list)
    reasoning_reference: str | None = None
    validation_outcome: str | None = None
    successor_decisions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArchiveIntelligence(BaseModel):
    """SAGE Master Archive Intelligence bundle for an ArchiveEntry."""

    lineage: KnowledgeLineage | None = None
    confidence: ConfidenceTracker | None = None
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)
    decisions: list[DecisionConnection] = Field(default_factory=list)


class ArchiveEntry(BaseModel):
    """Master Archive Entry representing validated knowledge."""

    id: str
    title: str
    tags: list[str] = Field(default_factory=list)
    knowledge_state: KnowledgeState = KnowledgeState.ARCHIVED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validation_timestamp: datetime | None = None
    decision_history: list[str] = Field(default_factory=list)
    lineage: list[str] = Field(default_factory=list)
    content: dict[str, Any] = Field(default_factory=dict)
    intelligence: ArchiveIntelligence | None = None


class DecisionEntry(BaseModel):
    """Decision record tracking the rationale and evidence for system choices."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: DecisionType
    description: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    outcome: str | None = None


class RuntimeState(BaseModel):
    """Runtime state representation."""

    current_objective: str | None = None
    active_task: str | None = None
    blockers: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class ExternalSessionPayload(BaseModel):
    """Payload representing an external engineering session to ingest."""

    session_id: str | None = None
    objective: str
    task: str | None = None
    memories: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
