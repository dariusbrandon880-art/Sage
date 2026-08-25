"""Flight B: Reality Gate & Source Receipt Verification for SAGE C2.

Enforces strict separation between the CONVERSATION PLANE (reports, claims, hypotheses)
and the REALITY PLANE (Git SHA, PR state, files, evidence receipts).

No operational live-state claim is permitted without a matching source receipt,
exact target resource, source type, and claim-specific fingerprint when one is encoded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SourceReceipt:
    source_type: str
    resource_id: str
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
    """Fail-closed live-state authorization using exact resource and fingerprint evidence."""

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

    @staticmethod
    def _fingerprint_matches(claim: OperationalClaim, receipt: SourceReceipt) -> bool:
        if not claim.target_resource:
            return False

        if claim.target_resource != receipt.resource_id:
            return False

        # For resource IDs of the form "kind:fingerprint", the fingerprint
        # must also match the receipt digest (or be represented by the receipt's
        # exact resource identifier). This prevents a valid resource label from
        # being paired with unrelated content.
        if ":" in claim.target_resource:
            expected_fingerprint = claim.target_resource.rsplit(":", 1)[1]
            if expected_fingerprint and expected_fingerprint != receipt.sha256_digest:
                return False

        return True

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
                permitted.append(claim)
                continue

            if not claim.target_resource:
                blocked.append(claim)
                violations.append(
                    f"Operational claim '{claim.statement}' BLOCKED: explicit target resource/fingerprint is required."
                )
                continue

            receipt = receipt_by_resource.get(claim.target_resource)
            if receipt is None:
                blocked.append(claim)
                violations.append(
                    f"Operational claim '{claim.statement}' BLOCKED: no exact receipt for '{claim.target_resource}'."
                )
                continue

            if claim.required_source_type and claim.required_source_type != receipt.source_type:
                blocked.append(claim)
                violations.append(
                    f"Operational claim '{claim.statement}' BLOCKED: source type mismatch."
                )
                continue

            if not cls._fingerprint_matches(claim, receipt):
                blocked.append(claim)
                violations.append(
                    f"Operational claim '{claim.statement}' BLOCKED: resource fingerprint mismatch."
                )
                continue

            permitted.append(claim)

        return RealityGateEvaluationResult(
            is_permitted=len(blocked) == 0,
            permitted_claims=tuple(permitted),
            blocked_claims=tuple(blocked),
            violations=tuple(violations),
        )
