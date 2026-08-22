"""Deterministic, zero-storage audit receipt for SAGE DecisionRecord v0.1.

This module is a read-only composition layer. It turns independently supplied
DecisionRecord integrity facts into a replayable public receipt without
persisting state, granting authority, or performing external I/O.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

AUDIT_RECEIPT_VERSION = "decision-audit-receipt-v0.1"
_ALLOWED_STATUSES = {"PASS", "HOLD", "FAIL"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _ref(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ch.isspace() for ch in value):
        raise ValueError(f"{field} must be a non-empty reference without whitespace")
    return value


@dataclass(frozen=True)
class AuditCheck:
    """One deterministic audit assertion over an already-produced decision."""

    check_id: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        _ref(self.check_id, "check_id")
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError("status must be PASS, HOLD, or FAIL")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("detail must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"check_id": self.check_id, "status": self.status, "detail": self.detail}


class DecisionAuditReceipt:
    """Pure audit projection bound to one immutable DecisionRecord hash.

    The receipt does not call the DecisionRecord, read files, inspect the
    network, or mutate the decision. Callers provide the verified facts and
    this class canonicalizes and hashes them for deterministic replay.
    """

    __slots__ = (
        "_decision_id",
        "_decision_hash",
        "_context_id",
        "_authority_ref",
        "_evidence_refs",
        "_checks",
        "_resolution_status",
        "_receipt_hash",
    )

    def __init__(
        self,
        *,
        decision_id: str,
        decision_hash: str,
        context_id: str,
        authority_ref: str,
        evidence_refs: Sequence[str],
        checks: Sequence[AuditCheck],
        resolution_status: str = "UNRESOLVED",
    ) -> None:
        self._decision_id = _ref(decision_id, "decision_id")
        self._decision_hash = _ref(decision_hash, "decision_hash")
        if len(self._decision_hash) != 64 or any(c not in "0123456789abcdefABCDEF" for c in self._decision_hash):
            raise ValueError("decision_hash must be a SHA-256 hexadecimal digest")
        self._context_id = _ref(context_id, "context_id")
        self._authority_ref = _ref(authority_ref, "authority_ref")
        refs = tuple(sorted({_ref(ref, "evidence_ref") for ref in evidence_refs}))
        if not refs:
            raise ValueError("at least one evidence_ref is required")
        self._evidence_refs = refs
        normalized_checks = tuple(sorted(tuple(checks), key=lambda item: item.check_id))
        if not normalized_checks:
            raise ValueError("at least one audit check is required")
        if len({check.check_id for check in normalized_checks}) != len(normalized_checks):
            raise ValueError("duplicate check_id is not allowed")
        self._checks = normalized_checks
        if not isinstance(resolution_status, str) or not resolution_status.strip():
            raise ValueError("resolution_status is required")
        self._resolution_status = resolution_status
        self._receipt_hash = self._compute_hash()

    def _body(self) -> dict[str, Any]:
        return {
            "audit_receipt_version": AUDIT_RECEIPT_VERSION,
            "decision_id": self._decision_id,
            "decision_hash": self._decision_hash.lower(),
            "context_id": self._context_id,
            "authority_ref": self._authority_ref,
            "evidence_refs": list(self._evidence_refs),
            "checks": [check.to_dict() for check in self._checks],
            "resolution_status": self._resolution_status,
        }

    def _compute_hash(self) -> str:
        return hashlib.sha256(_canonical(self._body()).encode("utf-8")).hexdigest()

    @property
    def receipt_hash(self) -> str:
        return self._receipt_hash

    @property
    def status(self) -> str:
        statuses = {check.status for check in self._checks}
        if "FAIL" in statuses:
            return "FAIL"
        if "HOLD" in statuses or self._resolution_status in {"PENDING", "UNRESOLVED"}:
            return "HOLD"
        return "PASS"

    def verify_integrity(self) -> bool:
        return self._receipt_hash == self._compute_hash()

    def to_dict(self) -> dict[str, Any]:
        if not self.verify_integrity():
            raise ValueError("audit receipt integrity check failed")
        return {**self._body(), "status": self.status, "receipt_hash": self._receipt_hash}

    def serialize(self) -> str:
        return _canonical(self.to_dict())

    def replay(self) -> "DecisionAuditReceipt":
        payload = json.loads(self.serialize())
        checks = tuple(AuditCheck(**item) for item in payload["checks"])
        replayed = DecisionAuditReceipt(
            decision_id=payload["decision_id"],
            decision_hash=payload["decision_hash"],
            context_id=payload["context_id"],
            authority_ref=payload["authority_ref"],
            evidence_refs=payload["evidence_refs"],
            checks=checks,
            resolution_status=payload["resolution_status"],
        )
        if replayed.receipt_hash != self.receipt_hash:
            raise ValueError("audit receipt replay integrity mismatch")
        return replayed

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name) and name.startswith("_"):
            raise AttributeError("DecisionAuditReceipt is immutable")
        super().__setattr__(name, value)
