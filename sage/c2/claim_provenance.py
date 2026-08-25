"""Flight C: Claim-to-Receipt Compiler & Factual Claim Verification for SAGE C2.

Classifies factual operational statements produced by C2 and checks whether
the required source receipt exists and matches fingerprint, SHA, or timestamp.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
    """Compiles operational text claims against reality source receipts."""

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
        receipt_by_source = {r.source_type: r for r in receipts}

        for claim in claims:
            if not RealityGate.is_live_state_claim(claim.statement) and not claim.required_source_type:
                # Non-live state claim
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash="NONE",
                    source_type="NONE",
                    status="PERMITTED",
                    reason="Conversational / non-operational claim requiring no reality receipt",
                )
                verified.append(rec)
                continue

            matching_receipt: Optional[SourceReceipt] = None
            if claim.target_resource and claim.target_resource in receipt_by_resource:
                matching_receipt = receipt_by_resource[claim.target_resource]
            elif claim.required_source_type and claim.required_source_type in receipt_by_source:
                # Same source type receipt exists, check if it contradicts the claimed resource/digest
                candidate = receipt_by_source[claim.required_source_type]
                if claim.target_resource and candidate.resource_id != claim.target_resource:
                    rec = VerifiedClaimReceipt(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        receipt_hash=candidate.sha256_digest,
                        source_type=candidate.source_type,
                        status="CONTRADICTED",
                        reason=f"Resource mismatch: claimed '{claim.target_resource}', found '{candidate.resource_id}'",
                    )
                    contradicted.append(rec)
                    continue

            # Generic receipt fallback (receipts[0]) removed per Repair C: No match => UNRESOLVED.
            if matching_receipt:
                # Validate digest match if specified
                if claim.target_resource and ":" in claim.target_resource:
                    expected_digest = claim.target_resource.split(":")[-1]
                    if expected_digest not in matching_receipt.resource_id and expected_digest != matching_receipt.sha256_digest:
                        rec = VerifiedClaimReceipt(
                            claim_id=claim.claim_id,
                            statement=claim.statement,
                            receipt_hash=matching_receipt.sha256_digest,
                            source_type=matching_receipt.source_type,
                            status="CONTRADICTED",
                            reason=f"Digest mismatch: expected '{expected_digest}', found '{matching_receipt.sha256_digest}'",
                        )
                        contradicted.append(rec)
                        continue

                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash=matching_receipt.sha256_digest,
                    source_type=matching_receipt.source_type,
                    status="PERMITTED",
                    reason="Verified against live source receipt",
                )
                verified.append(rec)
            else:
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash="UNRESOLVED",
                    source_type=claim.required_source_type or "UNKNOWN",
                    status="UNRESOLVED",
                    reason="No exact matching source receipt found for claim target resource",
                )
                unresolved.append(rec)

        is_valid = len(unresolved) == 0 and len(contradicted) == 0
        return ClaimCompilationResult(
            is_valid=is_valid,
            verified_claims=tuple(verified),
            unresolved_claims=tuple(unresolved),
            contradicted_claims=tuple(contradicted),
        )
