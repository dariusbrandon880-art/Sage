"""Canonical serialization for MissionProgressionReceipt evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any


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
    """Produce stable bytes/hash without treating telemetry as canonical identity."""

    def to_canonical_dict(self, receipt: Any) -> dict[str, Any]:
        return _filter_nondeterministic_fields(receipt.model_dump(mode="json"))

    def serialize(self, receipt: Any) -> bytes:
        return _canonical_serialize(self.to_canonical_dict(receipt))

    def digest(self, receipt: Any) -> str:
        return hashlib.sha256(self.serialize(receipt)).hexdigest()
