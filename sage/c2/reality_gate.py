"""Fail-closed reality/source gate for operational C2 claims.

Uses the canonical live-operation receipt from ``sage.c2.live_operation_receipt``;
this module intentionally does not define a second receipt authority.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sage.c2.live_operation_receipt import LiveOperationReceipt

@dataclass(frozen=True)
class SourceReceipt:
    source_type: str
    resource_id: str
    sha256_digest: str
    timestamp_utc: float
    execution_identity: str = "canonical_station"
    metadata: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return {"source_type": self.source_type, "resource_id": self.resource_id, "sha256_digest": self.sha256_digest, "timestamp_utc": self.timestamp_utc, "execution_identity": self.execution_identity, "metadata": self.metadata}

@dataclass(frozen=True)
class OperationalClaim:
    claim_id: str
    statement: str
    required_source_type: Optional[str] = None
    target_resource: Optional[str] = None
    required_capability: Optional[str] = None

@dataclass(frozen=True)
class RealityGateEvaluationResult:
    is_permitted: bool
    permitted_claims: Tuple[OperationalClaim, ...]
    blocked_claims: Tuple[OperationalClaim, ...]
    violations: Tuple[str, ...]

class RealityGate:
    LIVE_STATE_CLAIM_KEYWORDS = ("live repo", "github", "current head", "pr is merged", "pull request", "repo is clean", "working tree clean", "commit is", "tests pass on github", "ci status", "branch is at", "main is at")
    @classmethod
    def is_live_state_claim(cls, statement: str) -> bool:
        lower = statement.lower()
        return any(keyword in lower for keyword in cls.LIVE_STATE_CLAIM_KEYWORDS)
    @classmethod
    def evaluate_claims(cls, claims: Sequence[OperationalClaim], available_receipts: Sequence[SourceReceipt | LiveOperationReceipt], active_execution_identity: Optional[str] = None) -> RealityGateEvaluationResult:
        permitted: List[OperationalClaim] = []
        blocked: List[OperationalClaim] = []
        violations: List[str] = []
        for claim in claims:
            if not cls.is_live_state_claim(claim.statement) and not claim.required_source_type:
                permitted.append(claim); continue
            matched = False; reason = ""
            for rec in available_receipts:
                if isinstance(rec, LiveOperationReceipt):
                    if not rec.verify(): reason = "LiveOperationReceipt failed cryptographic verification"; continue
                    if not rec.success: reason = "LiveOperationReceipt indicates operation failure"; continue
                    if claim.target_resource and claim.target_resource in rec.target_resource:
                        matched = True; break
                elif isinstance(rec, SourceReceipt):
                    if active_execution_identity and rec.execution_identity != active_execution_identity: continue
                    if claim.target_resource and claim.target_resource in rec.resource_id and (not claim.required_source_type or claim.required_source_type == rec.source_type):
                        matched = True; break
            if matched:
                permitted.append(claim)
            else:
                blocked.append(claim)
                violations.append(reason or f"Operational claim '{claim.statement}' BLOCKED: missing explicit target resource/fingerprint receipt match.")
        return RealityGateEvaluationResult(not blocked, tuple(permitted), tuple(blocked), tuple(violations))
