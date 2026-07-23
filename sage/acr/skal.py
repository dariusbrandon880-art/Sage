"""SAGE-SKAL (Semantic Knowledge Association Layer) intake boundary and validation schemas."""

import json
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sage.models import MemoryObject, ConfidenceLevel


class SKALPayload(BaseModel):
    """Structured input payload for SAGE-SKAL deterministic intake."""

    object_type: str = Field(
        ..., description="Target category of the payload (e.g., fact, rule, decision)."
    )
    content: Dict[str, Any] = Field(..., description="JSON payload data.")
    tags: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    evidence_references: List[str] = Field(default_factory=list)


class SKALValidationReport(BaseModel):
    """Represents the results of SAGE-SKAL schema and validation audits."""

    is_valid: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    payload_fingerprint: str
    suggested_confidence: ConfidenceLevel = ConfidenceLevel.HYPOTHESIS


class SKALIntakeBoundary:
    """Deterministic gateway enforcing strict schema audits, rejection paths, and evidence mapping."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    def process_incoming_payload(self, payload: SKALPayload) -> SKALValidationReport:
        """Process, validate, and index incoming platform payloads.

        Ensures that knowledge is placed under a strict verification gate before
        promotion (No automatic permanent promotion).
        """
        rejection_reasons = []

        # Calculate content fingerprint
        fingerprint_content = f"{payload.object_type}:{json.dumps(payload.content, sort_keys=True)}"
        fingerprint = hashlib.sha256(fingerprint_content.encode("utf-8")).hexdigest()[:16]

        # 1. Structure/Type validations
        valid_types = [
            "fact",
            "rule",
            "report",
            "architectural_spec",
            "general",
            "technical_decision",
        ]
        if payload.object_type not in valid_types:
            rejection_reasons.append(
                f"Invalid object_type '{payload.object_type}'. Must be one of {valid_types}."
            )

        # 2. Content validations
        if not payload.content:
            rejection_reasons.append("Content cannot be empty.")
        else:
            # Check for required content keys depending on object type
            if payload.object_type == "technical_decision" and "description" not in payload.content:
                rejection_reasons.append(
                    "Technical decision content must contain a 'description' field."
                )

        is_valid = len(rejection_reasons) == 0

        # Create memory object as a HYPOTHESIS by default (Strictly maintain: Human/Validation gate remains mandatory)
        if is_valid:
            mem_obj = MemoryObject(
                object_type=payload.object_type,
                content=payload.content,
                tags=payload.tags + ["skal_intake"],
                confidence=ConfidenceLevel.HYPOTHESIS,
            )
            self.runtime.memory.store(mem_obj)

        return SKALValidationReport(
            is_valid=is_valid,
            rejection_reasons=rejection_reasons,
            payload_fingerprint=fingerprint,
            suggested_confidence=ConfidenceLevel.HYPOTHESIS,
        )
