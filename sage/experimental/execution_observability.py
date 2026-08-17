"""SAGE Execution Observation Receipt Layer.

Provides a read-only audit and projection layer capturing execution observation receipts across
subsystems (ACT Continuity, Airspace/C2, Sports/RCE, CCL-OPS) with canonical SHA-256 integrity verification,
duplicate execution ID rejection, and fresh-process restart state reconstruction.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionObservationReceipt(BaseModel):
    """Immutable audit observation receipt capturing what actually occurred during a governed operational cycle."""

    execution_id: str
    mission_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    initiating_subsystem: str = "CCL-OPS"  # CCL-OPS, ACT, Airspace, Sports/RCE
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    authorization_result: Dict[str, Any] = Field(default_factory=dict)
    observed_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    subsystem_receipts: Dict[str, Any] = Field(default_factory=dict)
    completion_state: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED, HALTED
    failure_state: Optional[str] = None
    hash_integrity_marker: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.hash_integrity_marker:
            self.hash_integrity_marker = self.compute_integrity_hash()

    def compute_integrity_hash(self) -> str:
        """Computes deterministic SHA-256 integrity hash over canonical JSON representation."""
        payload = {
            "execution_id": self.execution_id,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp,
            "initiating_subsystem": self.initiating_subsystem,
            "validation_result": self.validation_result,
            "authorization_result": self.authorization_result,
            "observed_transitions": self.observed_transitions,
            "evidence_references": sorted(self.evidence_references),
            "subsystem_receipts": self.subsystem_receipts,
            "completion_state": self.completion_state,
            "failure_state": self.failure_state or "",
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verifies stored hash_integrity_marker against independent recomputation."""
        if not self.hash_integrity_marker:
            return False
        return self.hash_integrity_marker == self.compute_integrity_hash()


class ExecutionObservationTracker:
    """Read-only audit and projection layer for observing governed SAGE operational cycles."""

    def __init__(self, ledger_path: Optional[str | Path] = None):
        self.ledger_path = Path(ledger_path or "evidence_capture/execution_observation_ledger.json")

    def _load_records(self) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def record_observation_receipt(self, receipt: ExecutionObservationReceipt) -> ExecutionObservationReceipt:
        """Records an execution observation receipt into the read-only audit ledger."""
        # 1. Verify hash integrity
        if not receipt.verify_integrity():
            raise ValueError(f"Receipt integrity validation failed for execution_id '{receipt.execution_id}'")

        # 2. Check missing evidence requirement on completion
        if receipt.completion_state == "COMPLETED" and not receipt.evidence_references:
            raise ValueError(f"Missing evidence blocks completion for execution_id '{receipt.execution_id}'")

        records = self._load_records()

        # 3. Duplicate execution_id check
        for existing in records:
            if existing.get("execution_id") == receipt.execution_id:
                raise ValueError(f"Duplicate execution_id '{receipt.execution_id}' detected.")

        records.append(receipt.model_dump())
        self._save_records(records)
        return receipt

    def retrieve_observation_receipt(self, execution_id: str) -> Optional[ExecutionObservationReceipt]:
        """Retrieves observation receipt by execution_id and verifies its integrity."""
        records = self._load_records()
        for rec in records:
            if rec.get("execution_id") == execution_id:
                receipt = ExecutionObservationReceipt(**rec)
                if not receipt.verify_integrity():
                    raise ValueError(f"Corrupted receipt integrity detected for execution_id '{execution_id}'")
                return receipt
        return None

    def reconstruct_observation_state(self) -> Dict[str, Any]:
        """Reconstructs execution observation state across fresh processes from durable disk evidence."""
        records = self._load_records()
        valid_receipts = []

        for rec in records:
            exec_id = rec.get("execution_id", "unknown")
            try:
                receipt = ExecutionObservationReceipt(**rec)
                if not receipt.verify_integrity():
                    raise ValueError(f"Hash mismatch in stored receipt '{exec_id}'")
                valid_receipts.append(receipt)
            except Exception as e:
                raise ValueError(f"Corrupted execution observation ledger entry '{exec_id}': {e}")

        completed = [r for r in valid_receipts if r.completion_state == "COMPLETED"]
        failed = [r for r in valid_receipts if r.completion_state == "FAILED"]
        in_progress = [r for r in valid_receipts if r.completion_state == "IN_PROGRESS"]

        last_receipt = valid_receipts[-1] if valid_receipts else None

        return {
            "status": "RECONSTRUCTED",
            "total_observations": len(valid_receipts),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "in_progress_count": len(in_progress),
            "last_known_execution_id": last_receipt.execution_id if last_receipt else None,
            "last_known_mission_id": last_receipt.mission_id if last_receipt else None,
            "last_known_state": last_receipt.completion_state if last_receipt else "IDLE",
            "receipts": [r.model_dump() for r in valid_receipts]
        }
