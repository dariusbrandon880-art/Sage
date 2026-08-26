"""Capability Audit Bridge."""

from __future__ import annotations
import hashlib
import os
import time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from sage.capability_registry import SAGEOperationalCapabilityRegistry


class AuditStatus(str, Enum):
    VERIFIED = "VERIFIED"
    DEGRADED_MISSING_PROOF = "DEGRADED_MISSING_PROOF"
    FAILED_CLOSED = "FAILED_CLOSED"

class CapabilityAuditRecord(BaseModel):
    capability_id: str
    status: AuditStatus
    missing_evidence: List[str] = Field(default_factory=list)
    missing_tests: List[str] = Field(default_factory=list)

class CapabilityAuditReceipt(BaseModel):
    receipt_id: str; exact_git_head: str; total_capabilities_audited: int; verified_capabilities_count: int
    degraded_capabilities_count: int; overall_status: AuditStatus; audit_records: List[CapabilityAuditRecord]
    timestamp: float = Field(default_factory=time.time); receipt_hash: str = ""
    def compute_hash(self) -> str:
        records_str = ";".join(f"{r.capability_id}:{r.status.value}" for r in self.audit_records)
        payload = f"{self.receipt_id}:{self.exact_git_head}:{self.total_capabilities_audited}:{self.verified_capabilities_count}:{self.overall_status.value}:{records_str}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class CapabilityAuditBridge:
    def __init__(self, registry: Optional[SAGEOperationalCapabilityRegistry] = None):
        self.registry = registry or SAGEOperationalCapabilityRegistry(); self.audit_history: List[CapabilityAuditReceipt] = []
    def perform_capability_audit(self, exact_git_head: str, root_dir: str = ".") -> CapabilityAuditReceipt:
        rcpt_id = f"cap_audit_rcpt_{int(time.time() * 1000)}"; caps = self.registry.list_capabilities()
        records=[]; verified_count=0; degraded_count=0
        for cap in caps:
            missing_ev=[ref for ref in cap.evidence_references if not os.path.exists(os.path.join(root_dir, ref))]
            missing_ts=[ref for ref in cap.test_references if not os.path.exists(os.path.join(root_dir, ref))]
            status=AuditStatus.DEGRADED_MISSING_PROOF if (missing_ev or missing_ts) else AuditStatus.VERIFIED
            degraded_count += status == AuditStatus.DEGRADED_MISSING_PROOF; verified_count += status == AuditStatus.VERIFIED
            records.append(CapabilityAuditRecord(capability_id=cap.capability_id,status=status,missing_evidence=missing_ev,missing_tests=missing_ts))
        overall=AuditStatus.VERIFIED if degraded_count == 0 else AuditStatus.DEGRADED_MISSING_PROOF
        rcpt=CapabilityAuditReceipt(receipt_id=rcpt_id,exact_git_head=exact_git_head,total_capabilities_audited=len(caps),verified_capabilities_count=verified_count,degraded_capabilities_count=degraded_count,overall_status=overall,audit_records=records)
        rcpt.receipt_hash=rcpt.compute_hash(); self.audit_history.append(rcpt); return rcpt
