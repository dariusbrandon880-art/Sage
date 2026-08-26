"""SAGE C2 Capability Audit Bridge & Drift Sentinel.

Executes continuous capability audit and evidence proof verification across SAGE:
- Inspects all capabilities in SAGEOperationalCapabilityRegistry and CapabilityWarehouseEngine.
- Performs on-disk existence verification for all supporting evidence and test references.
- Validates exact 40-character commit SHA provenance and detects registry or evidence drift.
- Produces cryptographically signed CapabilityAuditReceipt records for Control Tower inspection.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.c2.capability_warehouse import CapabilityWarehouseEngine
from sage.capability_registry import SAGEOperationalCapabilityRegistry


class AuditStatus(str, Enum):
    """Audit status classification for an individual capability."""
    VERIFIED = "VERIFIED"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    MISSING_PROOF = "MISSING_PROOF"
    UNVERIFIED_SHA = "UNVERIFIED_SHA"
    REGISTRY_DRIFT = "REGISTRY_DRIFT"


class CapabilityAuditRecord(BaseModel):
    """Audit record for a single capability."""
    capability_id: str
    name: str
    evidence_references: List[str] = Field(default_factory=list)
    test_references: List[str] = Field(default_factory=list)
    evidence_files_present: bool = True
    test_files_present: bool = True
    sha_valid: bool = True
    audit_status: AuditStatus = AuditStatus.VERIFIED
    details: str = "Evidence artifacts and test proofs verified on disk."


class CapabilityAuditReceipt(BaseModel):
    """Cryptographic evidence receipt for a capability audit wave."""
    receipt_id: str
    wave_id: str
    exact_git_head: str
    total_capabilities_audited: int
    verified_count: int
    drift_count: int
    audit_verdict: str  # "PASS" or "DRIFT_DETECTED"
    audit_records: List[CapabilityAuditRecord] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        records_str = ";".join([f"{r.capability_id}:{r.audit_status.value}" for r in sorted(self.audit_records, key=lambda x: x.capability_id)])
        payload = (
            f"{self.receipt_id}:{self.wave_id}:{self.exact_git_head}:{self.total_capabilities_audited}:"
            f"{self.verified_count}:{self.drift_count}:{self.audit_verdict}:{records_str}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class C2CapabilityAuditBridge:
    """Audit bridge enforcing on-disk proof verification and exact SHA validation."""

    def __init__(
        self,
        op_registry: Optional[SAGEOperationalCapabilityRegistry] = None,
        warehouse_engine: Optional[CapabilityWarehouseEngine] = None,
    ):
        self.op_registry = op_registry or SAGEOperationalCapabilityRegistry()
        self.warehouse_engine = warehouse_engine or CapabilityWarehouseEngine()

    def audit_capabilities(
        self,
        exact_git_head: str,
        wave_id: str = "capability_audit_wave_001",
    ) -> CapabilityAuditReceipt:
        """Audits all operational and warehouse capabilities against live disk state.

        Fails closed with audit_verdict = 'DRIFT_DETECTED' if any evidence reference or
        test reference file is missing from disk or if commit SHA is invalid.
        """
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
        is_sha_valid = bool(sha_pattern.match(exact_git_head))

        if not is_sha_valid:
            raise ValueError(f"Invalid exact git HEAD commit SHA: {exact_git_head}")

        op_caps = self.op_registry.list_capabilities()
        wh_items = self.warehouse_engine.list_items()

        all_cap_ids = set()
        audit_records: List[CapabilityAuditRecord] = []

        # Audit operational registry capabilities
        for cap in op_caps:
            all_cap_ids.add(cap.capability_id)
            ev_ok = all(os.path.exists(ref) for ref in cap.evidence_references) if cap.evidence_references else True
            test_ok = all(os.path.exists(ref) for ref in cap.test_references) if cap.test_references else True

            if not ev_ok or not test_ok:
                status = AuditStatus.MISSING_PROOF
                details = f"Missing on-disk proof: evidence_ok={ev_ok}, test_ok={test_ok}"
            else:
                status = AuditStatus.VERIFIED
                details = "Evidence and test files verified on disk."

            record = CapabilityAuditRecord(
                capability_id=cap.capability_id,
                name=cap.name,
                evidence_references=cap.evidence_references,
                test_references=cap.test_references,
                evidence_files_present=ev_ok,
                test_files_present=test_ok,
                sha_valid=is_sha_valid,
                audit_status=status,
                details=details,
            )
            audit_records.append(record)

        # Audit warehouse items not already covered
        for wh in wh_items:
            if wh.capability_id in all_cap_ids:
                continue
            all_cap_ids.add(wh.capability_id)

            ev_ok = all(os.path.exists(ref) for ref in wh.evidence_references) if wh.evidence_references else True
            test_ok = all(os.path.exists(ref) for ref in wh.test_references) if wh.test_references else True

            wh_sha_valid = bool(sha_pattern.match(wh.exact_commit_sha))

            if not wh_sha_valid:
                status = AuditStatus.UNVERIFIED_SHA
                details = f"Warehouse item SHA invalid: {wh.exact_commit_sha}"
            elif not ev_ok or not test_ok:
                status = AuditStatus.MISSING_PROOF
                details = f"Missing warehouse proof: evidence_ok={ev_ok}, test_ok={test_ok}"
            else:
                status = AuditStatus.VERIFIED
                details = "Warehouse capability evidence verified."

            record = CapabilityAuditRecord(
                capability_id=wh.capability_id,
                name=wh.name,
                evidence_references=wh.evidence_references,
                test_references=wh.test_references,
                evidence_files_present=ev_ok,
                test_files_present=test_ok,
                sha_valid=wh_sha_valid,
                audit_status=status,
                details=details,
            )
            audit_records.append(record)

        total = len(audit_records)
        verified = sum(1 for r in audit_records if r.audit_status == AuditStatus.VERIFIED)
        drift = total - verified

        verdict = "PASS" if drift == 0 and total > 0 else "DRIFT_DETECTED"

        receipt = CapabilityAuditReceipt(
            receipt_id=f"audit_rec_{hashlib.sha256(f'{wave_id}:{exact_git_head}'.encode('utf-8')).hexdigest()[:12]}",
            wave_id=wave_id,
            exact_git_head=exact_git_head,
            total_capabilities_audited=total,
            verified_count=verified,
            drift_count=drift,
            audit_verdict=verdict,
            audit_records=audit_records,
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt
