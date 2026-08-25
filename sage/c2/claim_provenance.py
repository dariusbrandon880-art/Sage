"""Flight C: Claim-to-Receipt Compiler & Factual Claim Verification for SAGE C2.

Classifies factual operational statements produced by C2 and checks whether
the required source receipt exists and matches the claim's exact resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt


@dataclass(frozen=True)
class VerifiedClaimReceipt:
    claim_id: str
    statement: str
    receipt_hash: str
    source_type: str
    status: str  # PERMITTED, CONTRADICTED, UNRESOLVED
    reason: str


@dataclass(frozen=True)
class ClaimCompilationResult:
    is_valid: bool
    verified_claims: Tuple[VerifiedClaimReceipt, ...]
    unresolved_claims: Tuple[VerifiedClaimReceipt, ...]
    contradicted_claims: Tuple[VerifiedClaimReceipt, ...]


class ClaimProvenanceCompiler:
    """Compiles operational text claims against exact live-source receipts."""

    @classmethod
    def compile_claims(
        cls,
        claims: Sequence[OperationalClaim],
        receipts: Sequence[SourceReceipt],
    ) -> ClaimCompilationResult:
        verified: List[VerifiedClaimReceipt] = []
        unresolved: List[VerifiedClaimReceipt] = []
        contradicted: List[VerifiedClaimReceipt] = []

        receipt_by_resource = {r.resource_id: r for r in receipts}

        for claim in claims:
            requires_receipt = RealityGate.is_live_state_claim(claim.statement) or bool(claim.required_source_type)

            if not requires_receipt:
                verified.append(
                    VerifiedClaimReceipt(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        receipt_hash="NONE",
                        source_type="NONE",
                        status="PERMITTED",
                        reason="Conversational / non-operational claim requiring no reality receipt",
                    )
                )
                continue

            if not claim.target_resource:
                unresolved.append(
                    VerifiedClaimReceipt(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        receipt_hash="UNRESOLVED",
                        source_type=claim.required_source_type or "UNKNOWN",
                        status="UNRESOLVED",
                        reason="Operational claim has no explicit target resource; source-type-only matching is forbidden",
                    )
                )
                continue

            matching_receipt: Optional[SourceReceipt] = receipt_by_resource.get(claim.target_resource)
            if matching_receipt is None:
                unresolved.append(
                    VerifiedClaimReceipt(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        receipt_hash="UNRESOLVED",
                        source_type=claim.required_source_type or "UNKNOWN",
                        status="UNRESOLVED",
                        reason="No exact matching source receipt found for claim target resource",
                    )
                )
                continue

            if claim.required_source_type and claim.required_source_type != matching_receipt.source_type:
                contradicted.append(
                    VerifiedClaimReceipt(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        receipt_hash=matching_receipt.sha256_digest,
                        source_type=matching_receipt.source_type,
                        status="CONTRADICTED",
                        reason=f"Source mismatch: required '{claim.required_source_type}', found '{matching_receipt.source_type}'",
                    )
                )
                continue

            if ":" in claim.target_resource:
                expected_digest = claim.target_resource.split(":")[-1]
                if expected_digest and expected_digest != matching_receipt.sha256_digest and expected_digest not in matching_receipt.resource_id:
                    contradicted.append(
                        VerifiedClaimReceipt(
                            claim_id=claim.claim_id,
                            statement=claim.statement,
                            receipt_hash=matching_receipt.sha256_digest,
                            source_type=matching_receipt.source_type,
                            status="CONTRADICTED",
                            reason=f"Fingerprint mismatch: expected '{expected_digest}', found '{matching_receipt.sha256_digest}'",
                        )
                    )
                    continue

            verified.append(
                VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash=matching_receipt.sha256_digest,
                    source_type=matching_receipt.source_type,
                    status="PERMITTED",
                    reason="Verified against exact live source receipt",
                )
            )

        return ClaimCompilationResult(
            is_valid=len(unresolved) == 0 and len(contradicted) == 0,
            verified_claims=tuple(verified),
            unresolved_claims=tuple(unresolved),
            contradicted_claims=tuple(contradicted),
        )
