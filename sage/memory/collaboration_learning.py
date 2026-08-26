"""SAGE Governed Collaboration Memory Engine & Knowledge Scope Promotion Pipeline.

Implements governed human-agent collaboration learning primitives:
- Enforces strict knowledge scope classification (PERSONAL, ORGANIZATIONAL, COLLECTIVE, CANONICAL).
- Implements the 6-stage promotion pipeline: OBSERVED -> CANDIDATE -> TESTED -> VALIDATED -> PROMOTABLE -> CANONICAL.
- Enforces candidate pattern != validated knowledge != canonical truth distinction.
- Provides pattern falsification, confidence scoring, automatic retirement, and SHA-256 evidence receipt generation.
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeScope(str, Enum):
    """Scope classification separating individual preference from canonical truth."""
    PERSONAL = "PERSONAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    COLLECTIVE = "COLLECTIVE"
    CANONICAL = "CANONICAL"


class PromotionStage(str, Enum):
    """The 6-stage promotion pipeline governing candidate memory advancement."""
    OBSERVED = "OBSERVED"
    CANDIDATE = "CANDIDATE"
    TESTED = "TESTED"
    VALIDATED = "VALIDATED"
    PROMOTABLE = "PROMOTABLE"
    CANONICAL = "CANONICAL"


class PatternStatus(str, Enum):
    """Lifecycle status of a collaboration pattern."""
    ACTIVE = "ACTIVE"
    DECAYED = "DECAYED"
    CONTRADICTED = "CONTRADICTED"
    RETIRED = "RETIRED"


class CollaborationPattern(BaseModel):
    """A governed collaboration pattern extracted from human/agent interaction."""
    pattern_id: str
    operator_id: str
    scope: KnowledgeScope = KnowledgeScope.PERSONAL
    stage: PromotionStage = PromotionStage.OBSERVED
    status: PatternStatus = PatternStatus.ACTIVE
    observation: str
    hypothesis: str
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_score: float = 0.5  # 0.0 to 1.0
    falsification_tests: List[str] = Field(default_factory=list)
    created_utc: float = Field(default_factory=time.time)
    updated_utc: float = Field(default_factory=time.time)


class CollaborationMemoryReceipt(BaseModel):
    """Immutable SHA-256 evidence receipt for collaboration learning transitions."""
    receipt_id: str
    pattern_id: str
    scope: KnowledgeScope
    stage: PromotionStage
    status: PatternStatus
    exact_head_sha: str
    evidence_refs: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.receipt_id}:{self.pattern_id}:{self.scope.value}:{self.stage.value}:{self.status.value}:{self.exact_head_sha}:{','.join(sorted(self.evidence_refs))}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class GovernedCollaborationMemoryEngine:
    """Engine governing collaboration pattern learning, promotion, and memory retirement."""

    def __init__(self, canonical_head_sha: str, storage_path: str = "evidence_capture/collaboration_memory_ledger.json"):
        self.canonical_head_sha = canonical_head_sha
        self.storage_path = storage_path
        self.patterns: Dict[str, CollaborationPattern] = {}
        self.receipts: List[CollaborationMemoryReceipt] = []

    def observe_pattern(
        self,
        pattern_id: str,
        operator_id: str,
        observation: str,
        hypothesis: str,
        evidence_refs: Optional[List[str]] = None,
        scope: KnowledgeScope = KnowledgeScope.PERSONAL,
    ) -> CollaborationPattern:
        """Constructs an observed pattern in OBSERVED stage without canonical mutation authority."""
        refs = evidence_refs or []
        pattern = CollaborationPattern(
            pattern_id=pattern_id,
            operator_id=operator_id,
            scope=scope,
            stage=PromotionStage.OBSERVED,
            status=PatternStatus.ACTIVE,
            observation=observation,
            hypothesis=hypothesis,
            evidence_refs=refs,
            confidence_score=0.5,
        )
        self.patterns[pattern_id] = pattern
        self._record_receipt(pattern)
        return pattern

    def evaluate_and_advance(
        self,
        pattern_id: str,
        falsification_passed: bool,
        evidence_ref: str,
    ) -> CollaborationPattern:
        """Evaluates candidate pattern against falsification tests and advances promotion stage."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            raise KeyError(f"Pattern '{pattern_id}' not found.")

        if not falsification_passed:
            pattern.status = PatternStatus.CONTRADICTED
            pattern.stage = PromotionStage.OBSERVED
            pattern.confidence_score = 0.0
            pattern.updated_utc = time.time()
            self._record_receipt(pattern)
            return pattern

        # Advance stage step-by-step
        if pattern.stage == PromotionStage.OBSERVED:
            pattern.stage = PromotionStage.CANDIDATE
            pattern.confidence_score = 0.7
        elif pattern.stage == PromotionStage.CANDIDATE:
            pattern.stage = PromotionStage.TESTED
            pattern.confidence_score = 0.85
        elif pattern.stage == PromotionStage.TESTED:
            pattern.stage = PromotionStage.VALIDATED
            pattern.confidence_score = 0.95
        elif pattern.stage == PromotionStage.VALIDATED:
            pattern.stage = PromotionStage.PROMOTABLE
            pattern.confidence_score = 1.0

        if evidence_ref not in pattern.evidence_refs:
            pattern.evidence_refs.append(evidence_ref)
        pattern.updated_utc = time.time()
        self._record_receipt(pattern)
        return pattern

    def retire_pattern(self, pattern_id: str, reason: str) -> CollaborationPattern:
        """Retires a stale, contradicted, or temporary pattern."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            raise KeyError(f"Pattern '{pattern_id}' not found.")

        pattern.status = PatternStatus.RETIRED
        pattern.confidence_score = 0.0
        pattern.updated_utc = time.time()
        self._record_receipt(pattern)
        return pattern

    def _record_receipt(self, pattern: CollaborationPattern) -> CollaborationMemoryReceipt:
        receipt_id = f"receipt-collab-{pattern.pattern_id}-{int(time.time() * 1000)}"
        receipt = CollaborationMemoryReceipt(
            receipt_id=receipt_id,
            pattern_id=pattern.pattern_id,
            scope=pattern.scope,
            stage=pattern.stage,
            status=pattern.status,
            exact_head_sha=self.canonical_head_sha,
            evidence_refs=list(pattern.evidence_refs),
        )
        receipt.receipt_hash = receipt.compute_hash()
        self.receipts.append(receipt)
        return receipt
