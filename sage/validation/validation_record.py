"""Validation Records for SAGE Validation Framework."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ValidationOutcome(BaseModel):
    """Validation record capturing details of a validation execution."""

    id: str = Field(default_factory=lambda: f"val_rec_{uuid.uuid4().hex[:8]}")
    item_id: str  # ID of the item being validated (e.g., memory ID, component path, etc.)
    validation_method: str  # e.g., "pytest_suite", "markdown_lint", "dependency_check"
    result: bool  # True for passed/validated, False for failed
    validator: str = "ValidationSystem"
    confidence_impact: float = 0.0  # e.g., incremental impact to confidence level (e.g. +0.1)
    related_tests: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)
