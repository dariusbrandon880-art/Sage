"""Receipt-backed live capability execution for the SAGE C2 boundary.

The receipt is created by the operation boundary itself, immediately after the
connected capability returns. Callers cannot mark an operation as performed by
passing a boolean; they must supply an actual capability implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
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

    def verify(self) -> bool:
        """Verify the receipt hash and required fields without trusting a caller flag."""
        if not self.operation or not self.capability or not self.target_resource:
            return False
        payload = {
            "operation": self.operation,
            "capability": self.capability,
            "target_resource": self.target_resource,
            "timestamp": self.timestamp,
            "success": self.success,
            "result_digest": self.result_digest,
        }
        expected = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return self.receipt_hash == expected


class LiveCapability(Protocol):
    """Connected capability whose invoke method is the live operation boundary."""

    capability_id: str

    def invoke(self, *, operation: str, task: str) -> Mapping[str, Any]:
        """Perform the actual connected operation and return its observed result."""
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
