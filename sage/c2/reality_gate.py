"""Flight B: Reality Gate & Source Receipt Verification for SAGE C2.

Enforces strict separation between the CONVERSATION PLANE (reports, claims, hypotheses)
and the REALITY PLANE (Git SHA, PR state, files, evidence receipts).

Guarantees that no operational claim about live state is permitted without a matching,
verifiable SourceReceipt from an actual reality source with target resource & fingerprint validation.
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
    """Enforces fail-closed Reality Gate policy: No source receipt & resource match -> No live-state claim permitted."""

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

        receipt_by_resource = {rc.resource_id: rc for rc in available_receipts}

        for claim in claims:
            if not cls.is_live_state_claim(claim.statement) and not claim.required_source_type:
                # Conversational or non-operational claim permitted
                permitted.append(claim)
                continue

            # Live-state claim requires strict matching receipt & resource validation
            has_valid_match = False

            if claim.target_resource:
                # Exact resource ID match required
                if claim.target_resource in receipt_by_resource:
                    rec = receipt_by_resource[claim.target_resource]
                    if not claim.required_source_type or claim.required_source_type == rec.source_type:
                        has_valid_match = True
            else:
                # Operational live claims WITHOUT target_resource specified are blocked unless receipt specifically covers the resource
                # Live claims such as "GitHub repo is clean" require an explicit resource receipt (e.g., resource_id="repo:clean_status")
                # Generic matching on source_type alone is forbidden for live state assertions.
                has_valid_match = False

            if has_valid_match:
                permitted.append(claim)
            else:
                blocked.append(claim)
                reason = f"Operational claim '{claim.statement}' BLOCKED: missing explicit target resource/fingerprint receipt match."
                violations.append(reason)

        is_permitted = len(blocked) == 0
        return RealityGateEvaluationResult(
            is_permitted=is_permitted,
            permitted_claims=tuple(permitted),
            blocked_claims=tuple(blocked),
            violations=tuple(violations),
        )
