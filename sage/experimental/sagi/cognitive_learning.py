"""SAGI Closed-Loop Cognitive Learning & Progression Learning Signal Bridge.

Bridges verified MissionProgressionReceipt objects at stage OUTCOME_CLASSIFIED
directly into SAGI candidate generation memory and failure logs without granting
unauthorized execution permissions or modifying Prefrontal Cortex (PFC) governance.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.progression import MissionProgressionReceipt
from sage.experimental.sagi.sagi import SAGICandidateGenerator


class SAGICognitiveLearningSignal(BaseModel):
    """Identity-anchored learning signal generated from a classified mission receipt."""
    signal_id: str
    mission_id: str
    receipt_id: str
    outcome_classification: str
    lesson_learned: str
    learning_timestamp: str = Field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    receipt_signature: str
    signal_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.signal_hash:
            self.signal_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Computes deterministic SHA-256 hash over learning signal payload."""
        payload = {
            "signal_id": self.signal_id,
            "mission_id": self.mission_id,
            "receipt_id": self.receipt_id,
            "outcome_classification": self.outcome_classification,
            "lesson_learned": self.lesson_learned,
            "receipt_signature": self.receipt_signature,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGICognitiveLearningEngine:
    """Ingests verified mission progression receipts and updates candidate generator memory."""

    def __init__(
        self,
        generator: Optional[SAGICandidateGenerator] = None,
        persistence_path: Optional[Path] = None,
    ):
        self.generator = generator or SAGICandidateGenerator()
        self.persistence_path = persistence_path or Path("evidence_capture/sagi_cognitive_learning_signals.json")
        self.learning_signals: List[SAGICognitiveLearningSignal] = []

    def ingest_progression_receipt(
        self, receipt: MissionProgressionReceipt
    ) -> SAGICognitiveLearningSignal:
        """Ingests a MissionProgressionReceipt and emits a learning signal if verified.

        Fails closed if the receipt is unverified, missing, or not at OUTCOME_CLASSIFIED stage.
        Does NOT grant execution authority or alter PFC decision rules.
        """
        if not receipt or not isinstance(receipt, MissionProgressionReceipt):
            raise ValueError("FAIL_CLOSED_INVALID_RECEIPT: Receipt must be a valid MissionProgressionReceipt instance.")

        if receipt.next_state != "OUTCOME_CLASSIFIED":
            raise ValueError(
                f"FAIL_CLOSED_NOT_CLASSIFIED: Cannot ingest receipt at state '{receipt.next_state}'. "
                "Must be 'OUTCOME_CLASSIFIED'."
            )

        val_res = receipt.validation_result or {}
        if val_res.get("status") != "APPROVED":
            raise ValueError(f"FAIL_CLOSED_UNVERIFIED_RECEIPT: Receipt validation status is '{val_res.get('status')}'.")

        outcome = str(val_res.get("outcome_classification") or "UNKNOWN")
        reason = receipt.reason or "Mission outcome classified."

        signal_id = f"sig_learn_{hashlib.sha256((receipt.receipt_id + outcome).encode('utf-8')).hexdigest()[:12]}"
        lesson = f"Outcome [{outcome}]: {reason}"

        signal = SAGICognitiveLearningSignal(
            signal_id=signal_id,
            mission_id=receipt.mission_id,
            receipt_id=receipt.receipt_id,
            outcome_classification=outcome,
            lesson_learned=lesson,
            receipt_signature=receipt.signature,
        )

        # Update candidate generator memory
        if outcome == "FAILURE":
            fail_record = {
                "signal_id": signal.signal_id,
                "mission_id": receipt.mission_id,
                "reason": reason,
                "classification": outcome,
            }
            if fail_record not in self.generator.failure_memory:
                self.generator.failure_memory.append(fail_record)

        self.learning_signals.append(signal)
        self._persist_signal(signal)
        return signal

    def _persist_signal(self, signal: SAGICognitiveLearningSignal) -> None:
        """Persists learning signals to append-only JSON file."""
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
            except Exception:
                existing = []

        existing.append(signal.model_dump())
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str)

    def load_signals(self) -> List[SAGICognitiveLearningSignal]:
        """Loads persisted learning signals across process restarts."""
        if not self.persistence_path.exists():
            return []
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [SAGICognitiveLearningSignal.model_validate(item) for item in data if isinstance(item, dict)]
            return []
        except Exception:
            return []
