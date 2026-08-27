"""Fail-closed reconvergence over independently validated front receipts."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Mapping

from .receipt_schema import ProvenanceTuple, StrictEvidenceReceipt


class FrontState(str, Enum):
    EXPECTED = "EXPECTED"
    SCHEDULED = "SCHEDULED"
    STARTED = "STARTED"
    EXECUTED = "EXECUTED"
    RECEIPT_PRESENT = "RECEIPT_PRESENT"
    RECEIPT_VALID = "RECEIPT_VALID"
    RECONVERGED = "RECONVERGED"
    UNVERIFIED = "UNVERIFIED"


class AggregatorError(RuntimeError):
    """Raised when a wave cannot be proven complete."""


class ReconvergenceAggregator:
    """Validate all required fronts without best-effort or fallback semantics."""

    REQUIRED_FRONTS = ("F1", "F2", "F3", "F4", "F5")

    def aggregate_wave(
        self,
        wave_id: str,
        expected_provenance: Mapping[str, ProvenanceTuple],
        receipts: Mapping[str, StrictEvidenceReceipt],
        observed_artifact_digests: Mapping[str, str],
    ) -> Dict[str, object]:
        if set(expected_provenance) != set(self.REQUIRED_FRONTS):
            raise AggregatorError("EXPECTED_FRONT_SET_MISMATCH")

        states = {front: FrontState.EXPECTED for front in self.REQUIRED_FRONTS}
        validated: Dict[str, StrictEvidenceReceipt] = {}

        for front in self.REQUIRED_FRONTS:
            receipt = receipts.get(front)
            if receipt is None:
                raise AggregatorError(f"MISSING_FRONT:{front}")
            states[front] = FrontState.RECEIPT_PRESENT

            expected = expected_provenance[front]
            observed = observed_artifact_digests.get(front)
            if observed is None:
                raise AggregatorError(f"MISSING_ARTIFACT_DIGEST:{front}")
            if not receipt.verify_against_context(expected, observed):
                raise AggregatorError(f"INVALID_RECEIPT:{front}")

            states[front] = FrontState.RECEIPT_VALID
            validated[front] = receipt

        for front in self.REQUIRED_FRONTS:
            states[front] = FrontState.RECONVERGED

        return {
            "wave_id": wave_id,
            "reconverged": True,
            "front_states": {front: state.value for front, state in states.items()},
            "validated_receipts": validated,
        }
