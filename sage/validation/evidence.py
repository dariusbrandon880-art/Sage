"""Evidence Records for SAGE Validation Framework."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    """Structured evidence object tracking validated artifacts and testing outcomes."""

    id: str = Field(default_factory=lambda: f"evidence_{uuid.uuid4().hex[:8]}")
    source: str  # e.g., "pytest", "manual", "ci_pipeline", "doc_checker"
    evidence_type: str  # e.g., "test_result", "architecture_adherence", "doc_coverage"
    related_component: str  # e.g., "sage/archive", "sage/api"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    supporting_references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
