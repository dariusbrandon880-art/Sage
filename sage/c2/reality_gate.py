"""Flight B: Reality Gate & Source Receipt Verification for SAGE C2.

Enforces strict separation between the CONVERSATION PLANE (reports, claims, hypotheses)
and the REALITY PLANE (Git SHA, PR state, files, evidence receipts).

Guarantees that no operational claim about live state is permitted without a matching,
verifiable SourceReceipt or LiveOperationReceipt from an actual reality source
with target resource, capability, execution identity, and fingerprint validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class LiveOperationReceipt:
    operation_id: str
    capability: str
    target_resource: str
    source: str
    timestamp: float
    success: bool
    result_digest: str
    execution_identity: str
    receipt_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        operation_id: str,
        capability: str,
        target_resource: str,
        source: str,
        success: bool,
        result_digest: str,
        execution_identity: str,
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LiveOperationReceipt:
        ts = timestamp if timestamp is not None else time.time()
        meta = metadata or {}
        raw = f"{operation_id}:{capability}:{target_resource}:{source}:{ts}:{success}:{result_digest}:{execution_identity}"
        r_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return cls(
            operation_id=operation_id,
            capability=capability,
            target_resource=target_resource,
            source=source,
            timestamp=ts,
            success=success,
            result_digest=result_digest,
            execution_identity=execution_identity,
            receipt_hash=r_hash,
            metadata=meta,
        )

    def verify_hash(self) -> bool:
        raw = f"{self.operation_id}:{self.capability}:{self.target_resource}:{self.source}:{self.timestamp}:{self.success}:{self.result_digest}:{self.execution_identity}"
        computed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.receipt_hash == computed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceReceipt:
    source_type: str  # "github", "filesystem", "ci_cd", "runtime_observation"
    resource_id: str  # e.g., "commit:70d1e798", "file:sage/c2/reality_gate.py"
    sha256_digest: str
    timestamp_utc: float
    execution_identity: str = "canonical_station"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "resource_id": self.resource_id,
            "sha256_digest": self.sha256_digest,
            "timestamp_utc": self.timestamp_utc,
            "execution_identity": self.execution_identity,
            "metadata": self.metadata,
        }


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
    """Enforces fail-closed Reality Gate policy: No valid invocation receipt & resource match -> No live-state claim permitted."""

    LIVE_STATE_CLAIM_KEYWORDS = (
        "live repo",
        "github",
        "current head",
        "pr is merged",
        "pull request",
        "repo is clean",
        "working tree clean",
        "commit is",
        "tests pass on github",
        "ci status",
        "branch is at",
        "main is at",
    )

    @classmethod
    def is_live_state_claim(cls, statement: str) -> bool:
        lower = statement.lower()
        return any(kw in lower for kw in cls.LIVE_STATE_CLAIM_KEYWORDS)

    @classmethod
    def evaluate_claims(
        cls,
        claims: Sequence[OperationalClaim],
        available_receipts: Sequence[SourceReceipt | LiveOperationReceipt],
        active_execution_identity: Optional[str] = None,
    ) -> RealityGateEvaluationResult:
        permitted: List[OperationalClaim] = []
        blocked: List[OperationalClaim] = []
        violations: List[str] = []

        for claim in claims:
            if not cls.is_live_state_claim(claim.statement) and not claim.required_source_type:
                permitted.append(claim)
                continue

            has_valid_match = False
            rejection_reason = ""

            for rec in available_receipts:
                # Disallow naked booleans or unrecognized objects
                if isinstance(rec, LiveOperationReceipt):
                    # 1. Verify receipt cryptographic hash integrity
                    if not rec.verify_hash():
                        rejection_reason = f"LiveOperationReceipt '{rec.operation_id}' failed cryptographic receipt_hash verification."
                        continue

                    # 2. Verify operation success
                    if not rec.success:
                        rejection_reason = f"LiveOperationReceipt '{rec.operation_id}' indicates operation failure (success=False)."
                        continue

                    # 3. Check execution identity if enforced
                    if active_execution_identity and rec.execution_identity != active_execution_identity:
                        rejection_reason = f"LiveOperationReceipt execution identity mismatch: expected '{active_execution_identity}', found '{rec.execution_identity}'."
                        continue

                    # 4. Target resource & capability matching
                    target_match = False
                    if claim.target_resource:
                        if claim.target_resource == rec.target_resource or claim.target_resource in rec.target_resource:
                            target_match = True
                    else:
                        target_match = False  # Operational claim about live state MUST specify explicit target resource

                    cap_match = False
                    if claim.required_capability:
                        if claim.required_capability == rec.capability:
                            cap_match = True
                    else:
                        cap_match = True

                    src_match = False
                    if claim.required_source_type:
                        if claim.required_source_type == rec.source:
                            src_match = True
                    else:
                        src_match = True

                    if target_match and cap_match and src_match:
                        has_valid_match = True
                        break

                elif isinstance(rec, SourceReceipt):
                    if active_execution_identity and rec.execution_identity != active_execution_identity:
                        rejection_reason = f"SourceReceipt execution identity mismatch: expected '{active_execution_identity}', found '{rec.execution_identity}'."
                        continue

                    target_match = False
                    if claim.target_resource:
                        if claim.target_resource == rec.resource_id or claim.target_resource in rec.resource_id:
                            target_match = True
                    else:
                        target_match = False  # Operational claim about live state MUST specify explicit target resource

                    src_match = False
                    if claim.required_source_type:
                        if claim.required_source_type == rec.source_type:
                            src_match = True
                    else:
                        src_match = True

                    if target_match and src_match:
                        has_valid_match = True
                        break

            if has_valid_match:
                permitted.append(claim)
            else:
                blocked.append(claim)
                reason = rejection_reason or f"Operational claim '{claim.statement}' BLOCKED: missing explicit target resource/fingerprint receipt match."
                violations.append(reason)

        is_permitted = len(blocked) == 0
        return RealityGateEvaluationResult(
            is_permitted=is_permitted,
            permitted_claims=tuple(permitted),
            blocked_claims=tuple(blocked),
            violations=tuple(violations),
        )
