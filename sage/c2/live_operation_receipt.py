"""Receipt-backed live capability execution and replay verification for the SAGE C2 boundary.

Receipts are created by the operation boundary itself. Persisted receipts can be
rehydrated in a fresh process and independently verified without trusting caller
booleans or in-memory execution state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class LiveOperationReceipt:
    """Cryptographically bound proof that a live capability was invoked."""

    operation: str
    capability: str
    target_resource: str
    timestamp: str
    success: bool
    result_digest: str
    receipt_hash: str

    def _payload(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "capability": self.capability,
            "target_resource": self.target_resource,
            "timestamp": self.timestamp,
            "success": self.success,
            "result_digest": self.result_digest,
        }

    def verify(self) -> bool:
        """Verify receipt integrity and required fields without trusting caller state."""
        if not self.operation or not self.capability or not self.target_resource:
            return False
        expected = sha256(
            json.dumps(self._payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return self.receipt_hash == expected

    def to_dict(self) -> dict[str, Any]:
        """Canonical JSON-safe representation for durable evidence storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LiveOperationReceipt":
        """Strictly reconstruct a receipt; unknown or missing fields fail closed."""
        required = {
            "operation", "capability", "target_resource", "timestamp",
            "success", "result_digest", "receipt_hash",
        }
        if set(payload) != required:
            raise ValueError("Persisted live operation receipt has invalid schema")
        if not isinstance(payload["success"], bool):
            raise ValueError("Persisted live operation receipt success must be boolean")
        return cls(**{name: payload[name] for name in required})


def persist_live_operation_receipt(receipt: LiveOperationReceipt, path: str | Path) -> None:
    """Persist one canonical receipt only after integrity verification."""
    if not receipt.verify() or not receipt.success:
        raise ValueError("Cannot persist invalid or failed live operation receipt")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def rehydrate_live_operation_receipt(path: str | Path) -> LiveOperationReceipt:
    """Fresh-process-safe load that rejects malformed or tampered evidence."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Persisted live operation receipt is unavailable or malformed") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Persisted live operation receipt must be an object")
    receipt = LiveOperationReceipt.from_dict(payload)
    if not receipt.verify() or not receipt.success:
        raise ValueError("Persisted live operation receipt failed replay verification")
    return receipt


class LiveCapability(Protocol):
    """Connected capability whose invoke method is the live operation boundary."""

    capability_id: str

    def invoke(self, *, operation: str, task: str) -> Mapping[str, Any]:
        ...


def execute_live_capability(
    capability: LiveCapability,
    *,
    operation: str,
    task: str,
) -> LiveOperationReceipt:
    """Invoke a connected capability and create its receipt at the boundary."""
    observed = capability.invoke(operation=operation, task=task)
    if not isinstance(observed, Mapping):
        raise TypeError("Live capability must return a mapping observation")
    target_resource = str(observed.get("target_resource", "")).strip()
    if not target_resource:
        raise ValueError("Live capability result is missing target_resource")
    success = bool(observed.get("success", True))
    result = observed.get("result", observed)
    result_payload = json.dumps(result, sort_keys=True, default=str, separators=(",", ":"))
    result_digest = sha256(result_payload.encode("utf-8")).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat()
    unsigned = {
        "operation": operation,
        "capability": str(capability.capability_id),
        "target_resource": target_resource,
        "timestamp": timestamp,
        "success": success,
        "result_digest": result_digest,
    }
    receipt_hash = sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt = LiveOperationReceipt(
        operation=operation,
        capability=str(capability.capability_id),
        target_resource=target_resource,
        timestamp=timestamp,
        success=success,
        result_digest=result_digest,
        receipt_hash=receipt_hash,
    )
    if not receipt.verify():
        raise ValueError("Generated live operation receipt failed self-verification")
    if not receipt.success:
        raise ValueError("Live capability operation failed; C2 verification is held")
    return receipt
