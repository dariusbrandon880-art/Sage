"""Canonical serialization for MissionProgressionReceipt evidence."""
from __future__ import annotations

import hashlib
from typing import Any

from sage.experimental.progression import MissionProgressionReceipt, canonical_serialize


class MissionProgressionReceiptSerializer:
    """Produce stable bytes/hash without treating telemetry as canonical identity."""

    def to_canonical_dict(self, receipt: MissionProgressionReceipt) -> dict[str, Any]:
        data = receipt.model_dump(mode="json")
        data.pop("timestamp", None)
        data.pop("receipt_id", None)
        return data

    def serialize(self, receipt: MissionProgressionReceipt) -> bytes:
        return canonical_serialize(self.to_canonical_dict(receipt))

    def digest(self, receipt: MissionProgressionReceipt) -> str:
        return hashlib.sha256(self.serialize(receipt)).hexdigest()
