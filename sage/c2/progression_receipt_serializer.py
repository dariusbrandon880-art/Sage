"""Canonical serialization and lineage validation for MissionProgressionReceipt evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any, List, Optional, Protocol, Tuple


class _ReceiptModel(Protocol):
    def model_dump(self, *, mode: str) -> dict[str, Any]: ...


_NONDETERMINISTIC_FIELDS = {"timestamp", "receipt_id", "nonce", "created_at"}


def _filter_nondeterministic_fields(data: Any) -> Any:
    """Remove telemetry/identity fields without importing experimental code."""
    if isinstance(data, dict):
        return {
            key: _filter_nondeterministic_fields(value)
            for key, value in data.items()
            if key not in _NONDETERMINISTIC_FIELDS
        }
    if isinstance(data, list):
        return [_filter_nondeterministic_fields(item) for item in data]
    return data


def _canonical_serialize(data: dict[str, Any]) -> bytes:
    """Stable production-local serialization with no experimental dependency."""
    filtered = _filter_nondeterministic_fields(data)
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")


class MissionProgressionReceiptSerializer:
    """Produce stable bytes/hash and validate evidence lineage chain integrity."""

    def to_canonical_dict(self, receipt: _ReceiptModel) -> dict[str, Any]:
        return _filter_nondeterministic_fields(receipt.model_dump(mode="json"))

    def serialize(self, receipt: _ReceiptModel) -> bytes:
        return _canonical_serialize(self.to_canonical_dict(receipt))

    def digest(self, receipt: _ReceiptModel) -> str:
        return hashlib.sha256(self.serialize(receipt)).hexdigest()

    def validate_receipt_lineage(self, receipts: List[dict[str, Any]]) -> dict[str, Any]:
        """Validates cryptographic parent-child receipt SHA-256 hash chains (`parent_receipt_hash`)."""
        if not receipts:
            return {"is_valid": True, "chain_length": 0, "violations": []}

        violations: List[str] = []
        previous_hash: Optional[str] = None

        for idx, r in enumerate(receipts):
            parent_hash = r.get("parent_receipt_hash")
            current_hash = r.get("receipt_hash")

            if idx > 0 and previous_hash and parent_hash != previous_hash:
                violations.append(
                    f"LINEAGE_CHAIN_BROKEN at index {idx}: parent_receipt_hash '{parent_hash}' "
                    f"does not match previous receipt_hash '{previous_hash}'."
                )

            if not current_hash or len(current_hash) != 64:
                violations.append(f"INVALID_RECEIPT_HASH at index {idx}: hash is missing or invalid length.")

            previous_hash = current_hash

        is_valid = len(violations) == 0
        return {
            "is_valid": is_valid,
            "chain_length": len(receipts),
            "violations": violations,
            "lineage_verdict": "LINEAGE_VERIFIED" if is_valid else "LINEAGE_CHAIN_INVALID",
        }
