"""Compile operational claims against verified source/live receipts."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple
from sage.c2.live_operation_receipt import LiveOperationReceipt
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt

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
    status: str
    reason: str

@dataclass(frozen=True)
class ClaimCompilationResult:
    is_valid: bool
    verified_claims: Tuple[VerifiedClaimReceipt, ...]
    unresolved_claims: Tuple[VerifiedClaimReceipt, ...]
    contradicted_claims: Tuple[VerifiedClaimReceipt, ...]

class ClaimProvenanceCompiler:
    @classmethod
    def traverse_causal_chain(cls, verified_claim: VerifiedClaimReceipt, available_receipts: Sequence[SourceReceipt | LiveOperationReceipt]) -> Optional[SourceReceipt | LiveOperationReceipt]:
        if verified_claim.status != "PERMITTED": return None
        for rec in available_receipts:
            if isinstance(rec, LiveOperationReceipt) and rec.receipt_hash == verified_claim.receipt_hash and rec.target_resource == verified_claim.target_resource: return rec
            if isinstance(rec, SourceReceipt) and rec.sha256_digest == verified_claim.receipt_hash and rec.resource_id == verified_claim.target_resource: return rec
        return None
    @classmethod
    def compile_claims(cls, claims: Sequence[OperationalClaim], receipts: Sequence[SourceReceipt | LiveOperationReceipt], active_execution_identity: Optional[str] = None) -> ClaimCompilationResult:
        verified=[]; unresolved=[]; contradicted=[]
        for claim in claims:
            gate = RealityGate.evaluate_claims([claim], receipts, active_execution_identity=active_execution_identity)
            if not gate.is_permitted:
                rec = VerifiedClaimReceipt(claim.claim_id, claim.statement, "BLOCKED", claim.required_source_type or "UNKNOWN", claim.target_resource or "UNKNOWN", claim.required_capability or "UNKNOWN", active_execution_identity or "UNKNOWN", "NONE", "UNRESOLVED", gate.violations[0] if gate.violations else "Reality Gate blocked claim")
                unresolved.append(rec); continue
            match = next((r for r in receipts if isinstance(r, SourceReceipt) and claim.target_resource and claim.target_resource in r.resource_id), None)
            if match:
                verified.append(VerifiedClaimReceipt(claim.claim_id, claim.statement, match.sha256_digest, match.source_type, match.resource_id, claim.required_capability or "READ_ONLY_OBSERVATION", match.execution_identity, match.sha256_digest, "PERMITTED", "Verified against SourceReceipt"))
                continue
            live = next((r for r in receipts if isinstance(r, LiveOperationReceipt) and claim.target_resource and claim.target_resource in r.target_resource), None)
            if live:
                verified.append(VerifiedClaimReceipt(claim.claim_id, claim.statement, live.receipt_hash, live.capability, live.target_resource, live.capability, "UNKNOWN", live.result_digest, "PERMITTED", "Verified against canonical LiveOperationReceipt"))
                continue
            unresolved.append(VerifiedClaimReceipt(claim.claim_id, claim.statement, "UNRESOLVED", claim.required_source_type or "UNKNOWN", claim.target_resource or "UNKNOWN", claim.required_capability or "UNKNOWN", active_execution_identity or "UNKNOWN", "NONE", "UNRESOLVED", "No exact matching receipt"))
        return ClaimCompilationResult(not unresolved and not contradicted, tuple(verified), tuple(unresolved), tuple(contradicted))
