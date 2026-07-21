"""Pydantic models for SAGE Capability Registry."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Capability(BaseModel):
    """Schema representing a registered capability."""

    id: str
    name: str
    description: str
    permissions: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True
