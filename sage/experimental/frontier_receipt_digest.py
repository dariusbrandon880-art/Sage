"""Deterministic, read-only digesting for frontier execution evidence."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if hasattr(value, "model_dump"):
        return _canonical(value.model_dump(mode="json"))
    return value


def frontier_receipt_digest(receipt: Any) -> str:
    """Return a stable SHA-256 digest of the public receipt representation."""
    payload = _canonical(receipt)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_frontier_receipt_digest(receipt: Any, expected_digest: str) -> bool:
    """Verify a receipt digest without mutating or qualifying the receipt."""
    if not expected_digest or len(expected_digest) != 64:
        return False
    return frontier_receipt_digest(receipt) == expected_digest
