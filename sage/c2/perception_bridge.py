"""Governed bridge for native multimodal perception events.

This module does not capture device input. The ChatGPT/native multimodal
interface is an upstream perception gateway. SAGE accepts only explicitly
supplied observations and keeps observed, inferred, searched, and verified
claims separate so downstream governance cannot silently promote inference
into fact.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvidenceStage(str, Enum):
    """Epistemic stage for a perception-derived claim."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    SEARCHED = "searched"
    VERIFIED = "verified"


class PerceptionClaim(BaseModel):
    """A single claim with an explicit epistemic boundary."""

    text: str = Field(..., min_length=1)
    stage: EvidenceStage
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_ref: Optional[str] = None
    provenance_ref: Optional[str] = None


class PerceptionEvent(BaseModel):
    """Immutable-style record of multimodal context presented to SAGE."""

    event_id: str = Field(..., min_length=1)
    timestamp: float = Field(..., gt=0)
    source: str = Field(..., min_length=1)
    user_intent: str = Field(..., min_length=1)
    modality: List[str] = Field(default_factory=list)
    claims: List[PerceptionClaim] = Field(default_factory=list)
    session_context_ref: Optional[str] = None
    input_provenance: Optional[str] = None


class PerceptionBridge:
    """Validate and normalize multimodal observations without inventing input."""

    ALLOWED_SOURCES = {
        "native_multimodal_interface",
        "camera",
        "screen_share",
        "user_attached_image",
        "user_attached_audio",
    }

    def ingest(self, event: PerceptionEvent) -> PerceptionEvent:
        """Fail closed unless the upstream source is explicitly recognized."""
        if event.source not in self.ALLOWED_SOURCES:
            raise ValueError(f"Unsupported perception source: {event.source}")
        if not event.claims:
            raise ValueError("Perception event must contain at least one explicit claim")
        return event

    @staticmethod
    def canonical_digest(event: PerceptionEvent) -> str:
        """Return a deterministic SHA-256 digest for evidence binding."""
        payload: Dict[str, Any] = event.model_dump(mode="json", exclude_none=True)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def claims_at_stage(event: PerceptionEvent, stage: EvidenceStage) -> List[PerceptionClaim]:
        """Return only claims explicitly recorded at the requested stage."""
        return [claim for claim in event.claims if claim.stage == stage]

    @staticmethod
    def acceptance_summary(event: PerceptionEvent) -> Dict[str, Any]:
        """Produce a governance-safe summary; never upgrades claim stages."""
        return {
            "event_id": event.event_id,
            "source": event.source,
            "observed_count": len(PerceptionBridge.claims_at_stage(event, EvidenceStage.OBSERVED)),
            "inferred_count": len(PerceptionBridge.claims_at_stage(event, EvidenceStage.INFERRED)),
            "searched_count": len(PerceptionBridge.claims_at_stage(event, EvidenceStage.SEARCHED)),
            "verified_count": len(PerceptionBridge.claims_at_stage(event, EvidenceStage.VERIFIED)),
            "evidence_sha256": PerceptionBridge.canonical_digest(event),
            "fail_closed": True,
        }
