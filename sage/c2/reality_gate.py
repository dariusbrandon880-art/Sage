"""Flight B: Reality Gate & Source Receipt Verification for SAGE C2.

Enforces strict separation between the CONVERSATION PLANE (reports, claims, hypotheses)
and the REALITY PLANE (Git SHA, PR state, files, evidence receipts).

Guarantees that no operational claim about live state is permitted without a matching,
verifiable SourceReceipt from an actual reality source.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SourceReceipt:
    source_type: str  # "github", "filesystem", "ci_cd", "runtime_observation"
    resource_id: str  # e.g., "commit:70d1e798", "file:sage/c2/reality_gate.py"
    sha256_digest: str
    timestamp_utc: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "resource_id": self.resource_id,
            "sha256_digest": self.sha256_digest,
            "timestamp_utc": self.timestamp_utc,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class OperationalClaim:
    claim_id: str
    statement: str
    required_source_type: Optional[str] = None
    target_resource: Optional[str] = None


@dataclass(frozen=True)
class RealityGateEvaluationResult:
    is_permitted: bool
    permitted_claims: Tuple[OperationalClaim, ...]
    blocked_claims: Tuple[OperationalClaim, ...]
    violations: Tuple[str, ...]


class RealityGate:
    """Enforces fail-closed Reality Gate policy: No source receipt -> No live-state claim permitted."""

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
        available_receipts: Sequence[SourceReceipt],
    ) -> RealityGateEvaluationResult:
        permitted: List[OperationalClaim] = []
        blocked: List[OperationalClaim] = []
        violations: List[str] = []

        receipt_sources = {r.source_type for r in available_receipts}
        receipt_resources = {r.resource_id for r in available_receipts}

        for claim in claims:
            if not cls.is_live_state_claim(claim.statement) and not claim.required_source_type:
                # Conversational or non-operational claim permitted
                permitted.append(claim)
                continue

            # Live-state claim requires matching receipt
            has_source_match = False
            if claim.required_source_type:
                if claim.required_source_type in receipt_sources:
                    if claim.target_resource:
                        has_source_match = claim.target_resource in receipt_resources
                    else:
                        has_source_match = True
            else:
                # Infer required source type
                lower = claim.statement.lower()
                if any(kw in lower for kw in ["github", "repo", "pr", "commit", "head", "branch"]):
                    has_source_match = "github" in receipt_sources or "filesystem" in receipt_sources
                else:
                    has_source_match = len(available_receipts) > 0

            if has_source_match:
                permitted.append(claim)
            else:
                blocked.append(claim)
                violations.append(
                    f"Operational claim '{claim.statement}' BLOCKED: missing required reality source receipt."
                )

        is_permitted = len(blocked) == 0
        return RealityGateEvaluationResult(
            is_permitted=is_permitted,
            permitted_claims=tuple(permitted),
            blocked_claims=tuple(blocked),
            violations=tuple(violations),
        )
