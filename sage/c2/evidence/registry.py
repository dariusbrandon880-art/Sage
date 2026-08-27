"""Append-only, identity-addressed evidence registry."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Dict, Any

from .receipt_schema import HEX_SHA40, StrictEvidenceReceipt


class ImmutableEvidenceRegistry:
    """Persist receipts under wave/head/front namespaces and refuse overwrites."""

    def __init__(self, base_dir: str = "evidence_capture") -> None:
        self.base_dir = Path(base_dir)

    def resolve_receipt_path(self, wave_id: str, head_sha: str, flight_id: str) -> Path:
        if not HEX_SHA40.fullmatch(head_sha):
            raise ValueError("head_sha must be a 40-character commit SHA")
        if not wave_id or not flight_id:
            raise ValueError("wave_id and flight_id must be non-empty")
        return self.base_dir / "waves" / wave_id / head_sha / f"{flight_id}_receipt.json"

    def register_receipt(self, receipt: StrictEvidenceReceipt) -> Path:
        receipt.validate()
        path = self.resolve_receipt_path(
            receipt.provenance.wave_id,
            receipt.provenance.executed_head,
            receipt.provenance.flight_id,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = asdict(receipt)
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except FileExistsError as exc:
            raise FileExistsError(f"IMMUTABLE_RECEIPT_EXISTS:{path}") from exc
        return path

    def load_wave_receipts(self, wave_id: str, target_sha: str) -> Dict[str, Dict[str, Any]]:
        directory = self.base_dir / "waves" / wave_id / target_sha
        if not directory.is_dir():
            return {}
        receipts: Dict[str, Dict[str, Any]] = {}
        for path in sorted(directory.glob("*_receipt.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            flight_id = data.get("provenance", {}).get("flight_id")
            if flight_id:
                receipts[flight_id] = data
        return receipts
