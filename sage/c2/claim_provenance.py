"""Flight C: Claim-to-Receipt Compiler & Factual Claim Verification for SAGE C2.

Classifies factual operational statements produced by C2 and checks whether
the required source receipt exists and matches fingerprint, SHA, or timestamp.
Supports backward causal traversal from OperationalClaim -> VerifiedClaimReceipt -> LiveOperationReceipt / SourceReceipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sage.c2.reality_gate import LiveOperationReceipt, OperationalClaim, RealityGate, SourceReceipt


@dataclass(frozen=True)
class VerifiedClaimReceipt:
    claim_id: str
    statement: str
    receipt_hash: str
    source_type: str
    target_resource: str
    capability: str
    execution_identity: str
    parent_evidence_hash: str
    status: str  # PERMITTED, CONTRADICTED, UNRESOLVED
    reason: str


@dataclass(frozen=True)
class ClaimCompilationResult:
    is_valid: bool
    verified_claims: Tuple[VerifiedClaimReceipt, ...]
    unresolved_claims: Tuple[VerifiedClaimReceipt, ...]
    contradicted_claims: Tuple[VerifiedClaimReceipt, ...]


class ClaimProvenanceCompiler:
    """Compiles operational text claims against reality source receipts and live operation receipts."""

    @classmethod
    def traverse_causal_chain(
        cls,
        verified_claim: VerifiedClaimReceipt,
        available_receipts: Sequence[SourceReceipt | LiveOperationReceipt],
    ) -> Optional[SourceReceipt | LiveOperationReceipt]:
        """Traverses backward from VerifiedClaimReceipt to the underlying execution receipt."""
        if verified_claim.status != "PERMITTED" or verified_claim.receipt_hash in ("NONE", "BLOCKED", "UNRESOLVED"):
            return None

        for rec in available_receipts:
            if isinstance(rec, LiveOperationReceipt):
                if rec.receipt_hash == verified_claim.receipt_hash and rec.target_resource == verified_claim.target_resource:
                    return rec
            elif isinstance(rec, SourceReceipt):
                if rec.sha256_digest == verified_claim.receipt_hash and rec.resource_id == verified_claim.target_resource:
                    return rec
        return None

    @classmethod
    def compile_claims(
        cls,
        claims: Sequence[OperationalClaim],
        receipts: Sequence[SourceReceipt | LiveOperationReceipt],
        active_execution_identity: Optional[str] = None,
    ) -> ClaimCompilationResult:
        verified: List[VerifiedClaimReceipt] = []
        unresolved: List[VerifiedClaimReceipt] = []
        contradicted: List[VerifiedClaimReceipt] = []

        # Index receipts
        live_op_by_resource: Dict[str, LiveOperationReceipt] = {}
        source_rec_by_resource: Dict[str, SourceReceipt] = {}
        source_rec_by_type: Dict[str, List[SourceReceipt]] = {}
        live_op_by_type: Dict[str, List[LiveOperationReceipt]] = {}

        for r in receipts:
            if isinstance(r, LiveOperationReceipt):
                live_op_by_resource[r.target_resource] = r
                live_op_by_type.setdefault(r.source, []).append(r)
            elif isinstance(r, SourceReceipt):
                source_rec_by_resource[r.resource_id] = r
                source_rec_by_type.setdefault(r.source_type, []).append(r)

        for claim in claims:
            if not RealityGate.is_live_state_claim(claim.statement) and not claim.required_source_type:
                # Conversational or non-operational claim
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash="NONE",
                    source_type="NONE",
                    target_resource="NONE",
                    capability="NONE",
                    execution_identity="NONE",
                    parent_evidence_hash="NONE",
                    status="PERMITTED",
                    reason="Conversational / non-operational claim requiring no reality receipt",
                )
                verified.append(rec)
                continue

            # First evaluate via RealityGate policy to check permissions/failures
            eval_gate = RealityGate.evaluate_claims([claim], receipts, active_execution_identity=active_execution_identity)
            if not eval_gate.is_permitted:
                violation = eval_gate.violations[0] if eval_gate.violations else "Reality Gate blocked claim"

                # Check if a receipt of the same source type exists with a differing target resource (contradiction)
                is_contradiction = "failed" in violation.lower() or "mismatch" in violation.lower()
                candidate_receipt_hash = "NONE"
                candidate_resource = claim.target_resource or "UNKNOWN"

                if claim.required_source_type:
                    same_type_sources = source_rec_by_type.get(claim.required_source_type, [])
                    same_type_ops = live_op_by_type.get(claim.required_source_type, [])
                    if same_type_sources:
                        is_contradiction = True
                        candidate_receipt_hash = same_type_sources[0].sha256_digest
                        candidate_resource = same_type_sources[0].resource_id
                        violation = f"Contradictory resource found for source '{claim.required_source_type}': expected '{claim.target_resource}', found '{candidate_resource}'"
                    elif same_type_ops:
                        is_contradiction = True
                        candidate_receipt_hash = same_type_ops[0].receipt_hash
                        candidate_resource = same_type_ops[0].target_resource
                        violation = f"Contradictory resource found for source '{claim.required_source_type}': expected '{claim.target_resource}', found '{candidate_resource}'"

                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash=candidate_receipt_hash if is_contradiction else "BLOCKED",
                    source_type=claim.required_source_type or "UNKNOWN",
                    target_resource=candidate_resource,
                    capability=claim.required_capability or "UNKNOWN",
                    execution_identity=active_execution_identity or "UNKNOWN",
                    parent_evidence_hash="NONE",
                    status="CONTRADICTED" if is_contradiction else "UNRESOLVED",
                    reason=violation,
                )
                if is_contradiction:
                    contradicted.append(rec)
                else:
                    unresolved.append(rec)
                continue

            # Find matching receipt for claim
            matching_op: Optional[LiveOperationReceipt] = None
            matching_source: Optional[SourceReceipt] = None

            if claim.target_resource:
                if claim.target_resource in live_op_by_resource:
                    matching_op = live_op_by_resource[claim.target_resource]
                elif claim.target_resource in source_rec_by_resource:
                    matching_source = source_rec_by_resource[claim.target_resource]

            if matching_op:
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash=matching_op.receipt_hash,
                    source_type=matching_op.source,
                    target_resource=matching_op.target_resource,
                    capability=matching_op.capability,
                    execution_identity=matching_op.execution_identity,
                    parent_evidence_hash=matching_op.result_digest,
                    status="PERMITTED",
                    reason="Verified against LiveOperationReceipt with backward causal lineage",
                )
                verified.append(rec)
            elif matching_source:
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash=matching_source.sha256_digest,
                    source_type=matching_source.source_type,
                    target_resource=matching_source.resource_id,
                    capability=claim.required_capability or "READ_ONLY_OBSERVATION",
                    execution_identity=matching_source.execution_identity,
                    parent_evidence_hash=matching_source.sha256_digest,
                    status="PERMITTED",
                    reason="Verified against SourceReceipt",
                )
                verified.append(rec)
            else:
                rec = VerifiedClaimReceipt(
                    claim_id=claim.claim_id,
                    statement=claim.statement,
                    receipt_hash="UNRESOLVED",
                    source_type=claim.required_source_type or "UNKNOWN",
                    target_resource=claim.target_resource or "UNKNOWN",
                    capability=claim.required_capability or "UNKNOWN",
                    execution_identity=active_execution_identity or "UNKNOWN",
                    parent_evidence_hash="NONE",
                    status="UNRESOLVED",
                    reason="No exact matching source or operation receipt found for claim target resource",
                )
                unresolved.append(rec)

        is_valid = len(unresolved) == 0 and len(contradicted) == 0
        return ClaimCompilationResult(
            is_valid=is_valid,
            verified_claims=tuple(verified),
            unresolved_claims=tuple(unresolved),
            contradicted_claims=tuple(contradicted),
        )
