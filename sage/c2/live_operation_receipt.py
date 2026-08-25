"""Receipt-backed live capability execution and replay verification for the SAGE C2 boundary.

Receipts are created by the operation boundary itself with hardware/AttestationProvider-bound
source signatures. Persisted receipts can be rehydrated in a fresh process and independently
verified without trusting caller booleans or un-attested JSON payloads.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Protocol

from sage.acr.attestation import AttestationProvider


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
    source_id: str = "sage-c2-operation-boundary"
    source_signature: str = ""

    def _payload(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "capability": self.capability,
            "target_resource": self.target_resource,
            "timestamp": self.timestamp,
            "success": self.success,
            "result_digest": self.result_digest,
            "source_id": self.source_id,
        }

    def verify(self, attestation: AttestationProvider | None = None) -> bool:
        """Verify receipt integrity, schema rules, and source attestation signature."""
        if not self.operation or not self.capability or not self.target_resource or not self.source_id:
            return False
        if len(self.result_digest) != 64 or len(self.receipt_hash) != 64:
            return False

        expected_hash = sha256(
            json.dumps(self._payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if self.receipt_hash != expected_hash:
            return False

        if not self.source_signature:
            return False

        provider = attestation or AttestationProvider()
        return provider.verify_signature(self._payload(), self.source_signature)

    def to_dict(self) -> dict[str, Any]:
        """Canonical JSON-safe representation for durable evidence storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> LiveOperationReceipt:
        """Strictly reconstruct a receipt; unknown, missing, or mistyped fields fail closed."""
        required = {
            "operation", "capability", "target_resource", "timestamp",
            "success", "result_digest", "receipt_hash", "source_id", "source_signature",
        }
        if set(payload) != required:
            raise ValueError("Persisted live operation receipt has invalid schema key set")
        if not isinstance(payload["success"], bool):
            raise ValueError("Persisted live operation receipt success must be boolean")
        for key in ("operation", "capability", "target_resource", "timestamp", "result_digest", "receipt_hash", "source_id", "source_signature"):
            val = payload[key]
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"Persisted live operation receipt '{key}' must be a non-empty string")

        if len(payload["result_digest"]) != 64 or len(payload["receipt_hash"]) != 64:
            raise ValueError("Persisted live operation receipt contains malformed SHA-256 hex digest")

        return cls(**{name: payload[name] for name in required})


def persist_live_operation_receipt(
    receipt: LiveOperationReceipt,
    path: str | Path,
    attestation: AttestationProvider | None = None,
) -> None:
    """Persist one canonical receipt only after integrity and signature verification."""
    if not receipt.verify(attestation=attestation) or not receipt.success:
        raise ValueError("Cannot persist invalid, forged, or failed live operation receipt")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def rehydrate_live_operation_receipt(
    path: str | Path,
    attestation: AttestationProvider | None = None,
) -> LiveOperationReceipt:
    """Fresh-process-safe load that rejects malformed, forged, or un-attested evidence."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Persisted live operation receipt is unavailable or malformed") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Persisted live operation receipt must be an object")
    receipt = LiveOperationReceipt.from_dict(payload)
    if not receipt.verify(attestation=attestation) or not receipt.success:
        raise ValueError("Persisted live operation receipt failed replay verification or source signature check")
    return receipt


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
    attestation: AttestationProvider | None = None,
) -> LiveOperationReceipt:
    """Invoke a connected capability and create its signed receipt at the operation boundary."""
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
    source_id = "sage-c2-operation-boundary"

    unsigned_payload = {
        "operation": operation,
        "capability": str(capability.capability_id),
        "target_resource": target_resource,
        "timestamp": timestamp,
        "success": success,
        "result_digest": result_digest,
        "source_id": source_id,
    }

    provider = attestation or AttestationProvider()
    signature = provider.sign_payload(unsigned_payload)

    receipt_hash = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    receipt = LiveOperationReceipt(
        operation=operation,
        capability=str(capability.capability_id),
        target_resource=target_resource,
        timestamp=timestamp,
        success=success,
        result_digest=result_digest,
        receipt_hash=receipt_hash,
        source_id=source_id,
        source_signature=signature,
    )

    if not receipt.verify(attestation=provider):
        raise ValueError("Generated live operation receipt failed self-verification or signature check")
    if not receipt.success:
        raise ValueError("Live capability operation failed; C2 verification is held")
    return receipt
